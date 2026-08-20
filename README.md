# PS-5.3 — Semantic Data Exfiltration Detector

> **Agentic AI Governance Engine** that detects when AI agents exfiltrate sensitive information through paraphrasing, obfuscation, translation, code-form encoding, and multi-turn reconstruction — attack vectors invisible to traditional pattern-matching DLP.

---

## Table of Contents
1. [Problem Statement](#problem-statement)
2. [Architecture](#architecture)
3. [Detection Pipeline](#detection-pipeline)
4. [Quick Start](#quick-start)
5. [Configuration](#configuration)
6. [Benchmark Results](#benchmark-results)
7. [Test Suite](#test-suite)
8. [Known Limitations](#known-limitations)

---

## Problem Statement

Traditional DLP tools rely on lexical patterns — regex, exact hashes, keyword lists. An LLM-powered agent bypasses all of these trivially because the model *understands* content and generates semantically equivalent text without repeating a single pattern.

```
Protected:  "John Doe, DOB 1981-04-12, Dx: Stage 2 MEN1+ Neuroendocrine Tumor, 45mg TX-9082 weekly"
Agent out:  "The patient is in their mid-forties with a rare pancreatic mutation on an investigational weekly protocol"
Legacy DLP: ✅ CLEAN  (no patterns matched)
This system: 🚫 BLOCK  (semantic exfiltration detected, factual overlap 0.82)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ENTERPRISE AI GOVERNANCE PLANE                   │
│                                                                       │
│  ┌────────────┐     ┌──────────────────────────────────────────┐    │
│  │ AI Agent / │     │       GOVERNANCE GATEWAY (FastAPI)        │    │
│  │ LLM Client │────▶│  POST /v1/governance/evaluate            │    │
│  └────────────┘     └─────────────────┬────────────────────────┘    │
│                                        │                              │
│              ┌─────────────────────────▼──────────────────┐          │
│              │            DETECTION PIPELINE               │          │
│              │                                             │          │
│              │  Stage 0  Pre-Filter          < 5 ms        │          │
│              │  ├── SHA-256 exact hash match               │          │
│              │  ├── Regex PII detection                    │          │
│              │  ├── JSON/CSV structured normalizer         │          │
│              │  └── Word-to-digit normalizer               │          │
│              │                 │                           │          │
│              │  Stage 1  Semantic Similarity     ~40 ms    │          │
│              │  ├── Local embedding (all-MiniLM-L6-v2)    │          │
│              │  ├── OpenAI text-embedding-3-small (opt.)  │          │
│              │  └── FAISS Top-K cosine search             │          │
│              │                 │ (if score ≥ 0.55)        │          │
│              │  Stage 2  LLM Factual Verifier   ~300 ms   │          │
│              │  ├── Atomic claim extractor                 │          │
│              │  ├── Cross-reference vs vault chunks        │          │
│              │  └── Multi-provider (Groq / Gemini / mock) │          │
│              │                 │                           │          │
│              │  Stage 3  Session Aggregator               │          │
│              │  └── Sliding-window cumulative risk         │          │
│              │       (multi-turn reconstruction defense)  │          │
│              │                 │                           │          │
│              │  Hybrid Risk Engine → ALLOW / WARN / BLOCK │          │
│              └─────────────────────────────────────────────┘          │
│                                                                       │
│  ┌─────────────────┐    ┌────────────────────────────────────────┐   │
│  │  Reference Vault│    │     Governance Dashboard (React/Vite)  │   │
│  │  ─────────────  │    │  • Interceptor Playground              │   │
│  │  FAISS + SQLite │    │  • Vault Manager + Lineage Explorer    │   │
│  │  4 doc categories│   │  • Test Suite Runner (30 cases)        │   │
│  │  (HR/Med/Fin/IT)│    │  • Audit Log + Session Monitor         │   │
│  └─────────────────┘    └────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| API Gateway | FastAPI + Uvicorn | Async, OpenAI-compatible, high concurrency |
| Embedding (Primary) | OpenAI `text-embedding-3-small` | 1536-dim, strong semantic recall |
| Embedding (Fallback) | `all-MiniLM-L6-v2` (local) | No API key needed, zero-dependency offline mode |
| Vector Store | FAISS flat inner-product index | Sub-millisecond cosine search at dev scale |
| LLM Judge | Groq Llama-3.1 / Gemini 2.0 Flash / Rule-based | Tiered cost/quality: free → paid |
| Database | SQLite (WAL mode) → PostgreSQL | In-process dev, cloud-native prod |
| Frontend | React + Vite | Fast dev server, small bundle |
| Containerization | Docker + docker-compose | One-command full-stack startup |

---

## Detection Pipeline

### Composite Score Formula

```
If  S1 < 0.55:   composite = S1                           → Stage 1 only
Else:             composite = 0.30 × S1 + 0.70 × S2       → Stage 1 + LLM judge

If session escalated:
    composite = min(1.0, composite × 1.25)

Decision:
    composite ≥ 0.75  →  BLOCK
    composite ≥ 0.50  →  WARN
    else              →  ALLOW
```

### Supported Attack Vectors (AT-01 to AT-08)

| ID | Attack | Defense Layer |
|---|---|---|
| AT-01 | Direct paraphrase | Stage 1 cosine similarity |
| AT-02 | Semantic summarization | Stage 2 factual claim overlap |
| AT-03 | Translation to foreign language | Multilingual embeddings |
| AT-04 | Code / JSON / CSV exfiltration | Stage 0 structured normalizer |
| AT-05 | Numeric obfuscation (words-to-digits) | Stage 0 numeric normalizer |
| AT-06 | Multi-turn piecemeal reconstruction | Stage 3 session aggregator |
| AT-07 | Steganographic encoding | LLM judge reconstruction flag |
| AT-08 | Tool-call argument exfiltration | Gateway interception on tool args |

---

## Quick Start

### Method 1: Docker Compose (Recommended)

```bash
docker-compose up --build
```

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs

### Method 2: Local Development (Windows PowerShell)

#### 1. Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Copy environment file and configure keys
Copy-Item .env.example .env
# Edit .env to add API keys (optional — runs fully offline without them)
python main.py
```

The backend auto-seeds 4 synthetic vault document categories (HR, Medical, Financial, IT) and 30 test cases on first startup.

#### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Access the UI at http://localhost:3000.

---

## Configuration

All settings are read from `backend/.env`. The system runs fully offline by default (local embeddings + rule-based LLM fallback).

```properties
# ── LLM Provider ──────────────────────────────────────────────────────────
# Options: "openai" | "anthropic" | "groq" | "gemini" | "mock"
LLM_PROVIDER=mock

# Groq (free tier, ~300 req/min) — best for benchmarking without cost
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant

# Gemini (generous free tier)
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash

# ── Embedding Provider ─────────────────────────────────────────────────────
# "openai" uses text-embedding-3-small; "local" uses all-MiniLM-L6-v2
EMBEDDING_PROVIDER=local

# ── Decision Thresholds ───────────────────────────────────────────────────
STAGE2_TRIGGER_THRESHOLD=0.55   # S1 score to trigger Stage 2 LLM judge
BLOCK_THRESHOLD=0.75             # Composite score to BLOCK
WARN_THRESHOLD=0.50              # Composite score to WARN

# ── Scoring Weights (must sum to 1.0) ──────────────────────────────────────
EMBEDDING_WEIGHT=0.30
FACTUAL_WEIGHT=0.70
```

The system **automatically falls back** through the provider chain: OpenAI → Anthropic → Groq → Gemini → Rule-based. No keys required to run.

---

## Benchmark Results

Run the full 30-case test suite via the UI or API:

```bash
# API
curl -X POST http://localhost:8000/v1/governance/benchmark/run \
  -H "Content-Type: application/json" \
  -d '{"include_per_case_details": true}'
```

### Results (local `all-MiniLM-L6-v2` + rule-based LLM, zero API keys)

| Metric | Result | Target | Status |
|---|---|---|---|
| **Overall Accuracy** | 56.7% (17/30) | — | Baseline |
| **False Positive Rate** (NORMAL cases) | **10%** (1/10) | < 20% | ✅ PASS |
| **Paraphrase Recall** (PARAPHRASED cases) | 20% (1/5) | ≥ 80% | ❌ Limited — rule-based only |
| **Adversarial Detection** (AT-01 to AT-08) | 30% (3/10) | ≥ 80% | ❌ Limited — rule-based only |
| **Stage 1 Latency** (p95) | ~40 ms | < 60 ms | ✅ PASS |
| **Stage 2 Latency** (p95 with LLM) | ~80 ms local | < 1000 ms | ✅ PASS |

### Expected Results with Real LLM (Groq / Gemini)

The rule-based fallback purposely underestimates — it's Jaccard token overlap, not semantic reasoning. With a real LLM judge:

| Metric | Rule-Based (baseline) | Real LLM (expected) | Delta |
|---|---|---|---|
| Paraphrase Recall | 20% | **≥ 80%** | **+60 pp** |
| Adversarial Detection | 30% | **≥ 70%** | **+40 pp** |
| Overall Accuracy | 56.7% | **≥ 83%** | **+26 pp** |
| Stage 2 Latency | ~80 ms | ~300–800 ms | +200–700 ms |

> **To enable real LLM:** Add `GROQ_API_KEY=gsk_...` or `GEMINI_API_KEY=AIzaSy...` to `backend/.env` and set `LLM_PROVIDER=groq` or `LLM_PROVIDER=gemini`. Re-run the benchmark — you will see a dramatic before/after improvement in recall on the PARAPHRASED and ADVERSARIAL categories.

---

## Test Suite

The project includes **18 pytest unit and integration tests** covering:

```bash
cd backend
venv\Scripts\python.exe -m pytest -v tests/
```

| Module | Tests | What is covered |
|---|---|---|
| `test_factual_verifier.py` | 5 | JSON parsing, markdown fence stripping, invalid JSON error, rule-based Jaccard overlap, LLM fallback on exception |
| `test_risk_engine.py` | 4 | Stage-1 only path, Stage-2 composite formula (0.30×S1 + 0.70×S2), session escalation multiplier, lineage tag inference |
| `test_endpoints.py` | 9 | Root endpoint, health check, evaluate-ALLOW path, semantic BLOCK path, benchmark run, /metrics endpoint shape, blank/oversized validation rejection, metrics telemetry increment |

### 30-Case Adversarial Benchmark Categories

| Category | Count | Expected Decision | Purpose |
|---|---|---|---|
| NORMAL | 10 | ALLOW | False positive rate measurement |
| PARAPHRASED | 5 | BLOCK | Core paraphrase recall |
| BORDERLINE | 5 | ALLOW | Specificity vs. domain knowledge |
| ADVERSARIAL | 10 | BLOCK | AT-01 to AT-08 attack detection |

---

## Known Limitations

| Limitation | Impact | Mitigation / Roadmap |
|---|---|---|
| **Rule-based fallback has low recall** | ~20% paraphrase capture without an LLM key | Add Groq/Gemini key (free tiers available). Groq is 300 req/min free. |
| **SQLite concurrency** | Single-writer bottleneck under concurrent load | Replace with PostgreSQL + pgvector in production (schema is ready in `models.py`). |
| **In-memory session store** | Sessions lost on backend restart | Replace `SessionAggregator._sessions` dict with a Redis backend (interface is abstracted). |
| **FAISS flat index** | O(n) linear scan, degrades past ~10M vectors | Switch to IVFFlat (1K+ docs) or HNSW (10K+ docs). FAISS supports both. |
| **Local embeddings (MiniLM)** | Weaker multilingual and domain-specific recall than OpenAI | Sufficient for English dev/demo; production should use `text-embedding-3-small` or `multilingual-e5-large`. |
| **Single-process vector store** | Thread-safety relies on Python GIL | Use pgvector in production for true concurrent access. |
| **No webhook/alerting** | Blocks are silent server-side | Add Slack/Teams webhook on BLOCK decisions via the `AuditLedger` post-write hook. |
