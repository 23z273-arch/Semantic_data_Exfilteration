"""
services/pre_filter.py — Stage-0 fast pre-filter.

Runs in < 5 ms and produces a PreFilterResult with:
  • exact_hash_match  — SHA-256 of output matches a known vault document hash
  • normalized_text   — text with structured data flattened and numbers normalised
  • pii_flags         — list of simple PII type flags detected via regex
"""
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Set

logger = logging.getLogger(__name__)

# ── Robust word-to-digit parser helpers ───────────────────────────────────────

def _parse_int_words(words: list[str]) -> int:
    num_map = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
        "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
        "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
        "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90
    }
    scale_map = {
        "hundred": 100, "thousand": 1000, "million": 1000000, "billion": 1000000000, "trillion": 1000000000000
    }
    
    current_val = 0
    total_val = 0
    
    for w in words:
        if w == "and":
            continue
        if w in num_map:
            current_val += num_map[w]
        elif w in scale_map:
            scale = scale_map[w]
            if scale == 100:
                current_val = (current_val or 1) * 100
            else:
                total_val += (current_val or 1) * scale
                current_val = 0
        elif w.isdigit():
            current_val += int(w)
            
    return total_val + current_val


def _words_to_number(words: list[str]) -> float | int:
    if not words:
        return 0
        
    large_scales = {
        "thousand": 1000,
        "million": 1000000,
        "billion": 1000000000,
        "trillion": 1000000000000,
        "thousands": 1000,
        "millions": 1000000,
        "billions": 1000000000,
        "trillions": 1000000000000
    }
    
    if "point" in words:
        scale_multiplier = 1
        if len(words) > 1 and words[-1] in large_scales:
            scale_multiplier = large_scales[words[-1]]
            words = words[:-1]
            
        idx = words.index("point")
        int_part = words[:idx]
        dec_part = words[idx+1:]
        
        int_val = _parse_int_words(int_part)
        dec_str = ""
        dec_map = {
            "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
            "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"
        }
        for w in dec_part:
            if w in dec_map:
                dec_str += dec_map[w]
            elif w.isdigit():
                dec_str += w
        
        val_str = f"{int_val}.{dec_str if dec_str else '0'}"
        val = float(val_str)
        return val * scale_multiplier
    else:
        return _parse_int_words(words)


# Simple PII regex patterns (no external lib needed)
_PII_PATTERNS = {
    "EMAIL":      r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b",
    "PHONE_US":   r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "SSN":        r"\b\d{3}-\d{2}-\d{4}\b",
    "CREDIT_CARD":r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "IP_ADDRESS": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
}


@dataclass
class PreFilterResult:
    normalized_text: str
    original_text: str
    exact_hash_match: bool = False
    matched_hash: Optional[str] = None
    pii_flags: List[str] = field(default_factory=list)
    latency_ms: float = 0.0


class PreFilter:
    """
    Stage-0 filter that:
      1. Computes SHA-256 of raw output and checks against vault content hashes.
      2. Extracts structured data (JSON/CSV → plain text).
      3. Normalises numeric expressions (word → digit) for embedding accuracy.
      4. Detects surface-level PII via regex.
    """

    def __init__(self):
        self._vault_hashes: Set[str] = set()

    def register_hash(self, content_hash: str) -> None:
        """Register a vault document content hash for exact-match detection."""
        self._vault_hashes.add(content_hash)

    def unregister_hash(self, content_hash: str) -> None:
        self._vault_hashes.discard(content_hash)

    def run(self, text: str) -> PreFilterResult:
        import time
        t0 = time.perf_counter()

        result = PreFilterResult(normalized_text=text, original_text=text)

        # 1. Exact hash match
        raw_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if raw_hash in self._vault_hashes:
            result.exact_hash_match = True
            result.matched_hash = raw_hash
            result.latency_ms = (time.perf_counter() - t0) * 1000
            return result

        # 2. Structural normalisation
        normalised = self._normalise_structured(text)

        # 3. Numeric normalisation
        normalised = self._normalise_numerics(normalised)

        # 4. PII detection (on original text)
        result.pii_flags = self._detect_pii(text)

        result.normalized_text = normalised
        result.latency_ms = (time.perf_counter() - t0) * 1000
        return result

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _normalise_structured(text: str) -> str:
        """Convert JSON / pseudo-CSV embedded in text into plain key:value form."""
        # Detect JSON objects or arrays
        stripped = text.strip()
        if stripped.startswith(("{", "[")):
            try:
                obj = json.loads(stripped)
                return _flatten_json(obj)
            except json.JSONDecodeError:
                pass

        # Inline JSON fragments
        json_fragments = re.findall(r"\{[^{}]{10,}\}", text)
        for frag in json_fragments:
            try:
                obj = json.loads(frag)
                flat = _flatten_json(obj)
                text = text.replace(frag, " " + flat + " ")
            except json.JSONDecodeError:
                pass

        return text

    @staticmethod
    def _normalise_numerics(text: str) -> str:
        """Replace written-out numbers with digits, expanding k/m/b suffixes."""
        num_tokens = {
            "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
            "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
            "seventeen", "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty",
            "sixty", "seventy", "eighty", "ninety", "hundred", "thousand", "million",
            "billion", "trillion", "thousands", "millions", "billions", "trillions",
            "point"
        }
        
        # Pre-collapse comma-formatted numbers: 400,000 → 400000 (before tokenization)
        text = re.sub(
            r"\b(\d{1,3}(?:,\d{3})+)\b",
            lambda m: m.group(1).replace(",", ""),
            text
        )

        # Pre-replace common fractional word expressions
        text = re.sub(r"\ba\s+quarter\s+million\b", "250000", text, flags=re.IGNORECASE)
        text = re.sub(r"\bquarter\s+million\b", "250000", text, flags=re.IGNORECASE)
        text = re.sub(r"\bhalf\s+a\s+million\b", "500000", text, flags=re.IGNORECASE)
        text = re.sub(r"\bhalf\s+million\b", "500000", text, flags=re.IGNORECASE)

        # Pre-expand short digit abbreviations: 400k → 400000, 2.5m → 2500000
        # Use negative lookahead to avoid matching the start of words like 'million','billion'
        text = re.sub(
            r"\b(\d+(?:\.\d+)?)\s*[kK](?!ilo|nowledge|ey|eep|ind|ing)",
            lambda m: str(int(float(m.group(1)) * 1_000)),
            text
        )
        text = re.sub(
            r"\b(\d+(?:\.\d+)?)\s*(?:million|M)\b",
            lambda m: str(int(float(m.group(1)) * 1_000_000)),
            text
        )
        text = re.sub(
            r"\b(\d+(?:\.\d+)?)\s*(?:billion|B)\b",
            lambda m: str(int(float(m.group(1)) * 1_000_000_000)),
            text
        )
        text = re.sub(
            r"\b(\d+(?:\.\d+)?)\s*(?:trillion|T)\b",
            lambda m: str(int(float(m.group(1)) * 1_000_000_000_000)),
            text
        )
        
        tokens = re.split(r"(\b)", text)
        is_num = [False] * len(tokens)
        
        for idx, t in enumerate(tokens):
            t_clean = t.lower().strip()
            if not t_clean:
                continue
            if t_clean in num_tokens or t_clean.isdigit():
                is_num[idx] = True
            elif re.match(r"^\d+\.\d+$", t_clean):
                is_num[idx] = True
                
        # Connect separators flanked by number tokens.
        # NOTE: 'and' is intentionally NOT a connector here — it would merge
        # standalone numbers like "5 and 6" into "11". 'and' is only handled
        # inside _parse_int_words when building compound words (e.g. "forty and two").
        _CONNECTORS = {"", "-", ","}
        for idx in range(len(tokens)):
            if is_num[idx]:
                continue
            t_clean = tokens[idx].lower().strip()
            if t_clean in _CONNECTORS or not tokens[idx].strip():
                left_num_idx = -1
                for j in range(idx - 1, -1, -1):
                    j_clean = tokens[j].lower().strip()
                    if is_num[j]:
                        left_num_idx = j
                        break
                    if j_clean not in _CONNECTORS and tokens[j].strip():
                        break

                right_num_idx = -1
                for j in range(idx + 1, len(tokens)):
                    j_clean = tokens[j].lower().strip()
                    if is_num[j]:
                        right_num_idx = j
                        break
                    if j_clean not in _CONNECTORS and tokens[j].strip():
                        break

                if left_num_idx != -1 and right_num_idx != -1:
                    for j in range(left_num_idx + 1, right_num_idx):
                        is_num[j] = True

        new_tokens = []
        i = 0
        n = len(tokens)
        while i < n:
            if is_num[i]:
                seq_tokens = []
                while i < n and is_num[i]:
                    seq_tokens.append(tokens[i])
                    i += 1
                words = []
                for t in seq_tokens:
                    t_clean = t.lower().strip()
                    if t_clean and t_clean not in {",", "-"}:
                        words.append(t_clean)
                
                if words:
                    try:
                        num_val = _words_to_number(words)
                        if isinstance(num_val, float) and num_val.is_integer():
                            num_str = str(int(num_val))
                        else:
                            num_str = str(num_val)
                        new_tokens.append(num_str)
                    except Exception:
                        new_tokens.extend(seq_tokens)
                else:
                    new_tokens.extend(seq_tokens)
            else:
                new_tokens.append(tokens[i])
                i += 1
                
        return "".join(new_tokens)

    @staticmethod
    def _detect_pii(text: str) -> List[str]:
        detected = []
        for label, pattern in _PII_PATTERNS.items():
            if re.search(pattern, text):
                detected.append(label)
        return detected


def _flatten_json(obj, prefix: str = "") -> str:
    """Recursively flatten a JSON object to 'key: value' pairs."""
    parts = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            parts.append(_flatten_json(v, prefix=f"{prefix}{k}: " if prefix else f"{k}: "))
    elif isinstance(obj, list):
        for item in obj:
            parts.append(_flatten_json(item, prefix=prefix))
    else:
        parts.append(f"{prefix}{obj}")
    return " | ".join(parts)


# ── Singleton ─────────────────────────────────────────────────────────────────
_pre_filter: PreFilter | None = None


def get_pre_filter() -> PreFilter:
    global _pre_filter
    if _pre_filter is None:
        _pre_filter = PreFilter()
    return _pre_filter
