"""
services/hybrid_risk_engine.py — Composite scoring and decision engine.

Combines Stage-1 embedding similarity score and Stage-2 factual overlap score
using calibrated weights, applies session escalation, and produces the final
governance decision (ALLOW / WARN / BLOCK) with lineage tags.
"""
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from config import settings
from services.embedding_scorer import SimilarityResult
from services.factual_verifier import FactualVerificationResult
from services.session_aggregator import SessionState

logger = logging.getLogger(__name__)


@dataclass
class LineageTag:
    tag: str
    document_name: str
    classification: str
    department: Optional[str]
    data_type: str
    match_score: float


@dataclass
class RiskDecision:
    decision: str                   # ALLOW | WARN | BLOCK
    composite_risk_score: float
    embedding_score: float
    factual_score: Optional[float]
    stage_executed: int             # 1 or 2
    session_escalated: bool
    lineage_tags: List[LineageTag] = field(default_factory=list)
    decision_rationale: str = ""


class HybridRiskEngine:
    """
    Deterministic decision engine that combines all stage scores.

    Formula:
      If S1 < STAGE2_TRIGGER:
          composite = S1
      Else:
          composite = 0.30 × S1 + 0.70 × S2
      If session escalated:
          composite = min(1.0, composite × escalation_multiplier)

    Decision:
      composite >= 0.75  → BLOCK
      composite >= 0.50  → WARN
      else               → ALLOW
    """

    def decide(
        self,
        s1: SimilarityResult,
        s2: Optional[FactualVerificationResult],
        session_state: SessionState,
        original_composite: Optional[float] = None,  # Pre-escalation score
    ) -> RiskDecision:

        # ── Compute composite score ────────────────────────────────────────────
        if s2 is None:
            composite = s1.max_similarity
            stage_executed = 1
            factual_score = None
            rationale_parts = [
                f"Stage-1 only (max cosine={s1.max_similarity:.3f} < trigger threshold={settings.STAGE2_TRIGGER_THRESHOLD})"
            ]
        else:
            composite = (
                settings.EMBEDDING_WEIGHT * s1.max_similarity
                + settings.FACTUAL_WEIGHT * s2.factual_overlap_score
            )
            if s2.is_reconstruction_attack:
                composite = max(composite, settings.BLOCK_THRESHOLD)
            stage_executed = 2
            factual_score = s2.factual_overlap_score
            rationale_parts = [
                f"Stage-1 cosine={s1.max_similarity:.3f}",
                f"Stage-2 factual={s2.factual_overlap_score:.3f}",
                f"Reconstruction={s2.is_reconstruction_attack}",
                f"Composite={composite:.3f}",
            ]

        pre_escalation = composite

        # ── Session escalation ─────────────────────────────────────────────────
        if session_state.escalated:
            composite = min(1.0, composite * settings.SESSION_ESCALATION_MULTIPLIER)
            rationale_parts.append(
                f"Session escalation applied (×{settings.SESSION_ESCALATION_MULTIPLIER}): "
                f"{pre_escalation:.3f} → {composite:.3f}"
            )

        # ── Decision ───────────────────────────────────────────────────────────
        if composite >= settings.BLOCK_THRESHOLD:
            decision = "BLOCK"
        elif composite >= settings.WARN_THRESHOLD:
            decision = "WARN"
        else:
            decision = "ALLOW"

        rationale_parts.append(f"Decision: {decision}")

        # ── Lineage tags (only for WARN or BLOCK) ──────────────────────────────
        lineage_tags: List[LineageTag] = []
        if decision in ("WARN", "BLOCK"):
            seen_tags: set = set()
            for match in s1.top_matches[:5]:
                if match.lineage_tag in seen_tags:
                    continue
                seen_tags.add(match.lineage_tag)
                lineage_tags.append(
                    LineageTag(
                        tag=match.lineage_tag,
                        document_name=match.document_name,
                        classification=match.classification,
                        department=match.department,
                        data_type=_infer_data_type(match.lineage_tag),
                        match_score=match.similarity,
                    )
                )

        return RiskDecision(
            decision=decision,
            composite_risk_score=composite,
            embedding_score=s1.max_similarity,
            factual_score=factual_score,
            stage_executed=stage_executed,
            session_escalated=session_state.escalated,
            lineage_tags=lineage_tags,
            decision_rationale=" | ".join(rationale_parts),
        )


def _infer_data_type(lineage_tag: str) -> str:
    """Infer a human-readable data type from the lineage tag string."""
    tag = lineage_tag.upper()
    if "HR" in tag or "EMP" in tag or "EXEC" in tag:
        return "HR_COMPENSATION_RECORD"
    if "MED" in tag or "PAT" in tag or "TRIAL" in tag:
        return "CLINICAL_TRIAL_RECORD"
    if "FIN" in tag or "MA" in tag or "ACQ" in tag:
        return "FINANCIAL_STRATEGIC_MEMO"
    if "IT" in tag or "INFRA" in tag or "NET" in tag:
        return "INFRASTRUCTURE_CREDENTIALS"
    return "PROTECTED_DOCUMENT"


# ── Singleton ─────────────────────────────────────────────────────────────────
_engine: HybridRiskEngine | None = None


def get_risk_engine() -> HybridRiskEngine:
    global _engine
    if _engine is None:
        _engine = HybridRiskEngine()
    return _engine
