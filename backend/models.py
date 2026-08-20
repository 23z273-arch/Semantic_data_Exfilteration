"""
models.py — SQLAlchemy ORM models for all database tables.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey,
    Integer, String, Text, JSON
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


# ─────────────────────────────────────────────────────────────────────────────
# VAULT
# ─────────────────────────────────────────────────────────────────────────────

class VaultDocument(Base):
    __tablename__ = "vault_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)          # HR_RECORD | FINANCIAL | MEDICAL | INFRASTRUCTURE
    classification: Mapped[str] = mapped_column(String(50), nullable=False)     # RESTRICTED | CONFIDENTIAL | TOP_SECRET
    lineage_tag: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    department: Mapped[Optional[str]] = mapped_column(String(200))
    data_owner: Mapped[Optional[str]] = mapped_column(String(200))
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)       # SHA-256
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False, default="text-embedding-3-small")
    ingest_status: Mapped[str] = mapped_column(String(20), default="PENDING")   # PENDING | PROCESSING | READY | FAILED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    meta_data: Mapped[dict] = mapped_column(JSON, default=dict)

    chunks: Mapped[List["VaultChunk"]] = relationship("VaultChunk", back_populates="document", cascade="all, delete-orphan")


class VaultChunk(Base):
    __tablename__ = "vault_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("vault_documents.id", ondelete="CASCADE"), nullable=False)
    lineage_tag: Mapped[str] = mapped_column(String(200), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    position_ratio: Mapped[float] = mapped_column(Float, nullable=False)          # 0.0 = start, 1.0 = end
    faiss_index_id: Mapped[Optional[int]] = mapped_column(Integer)                        # ID in the FAISS flat index
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    document: Mapped["VaultDocument"] = relationship("VaultDocument", back_populates="chunks")


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT
# ─────────────────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)

    # Request context
    agent_id: Mapped[str] = mapped_column(String(200), nullable=False)
    session_id: Mapped[Optional[str]] = mapped_column(String(200))
    request_id: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)

    # Content
    prompt_preview: Mapped[Optional[str]] = mapped_column(String(1000))
    output_text: Mapped[str] = mapped_column(Text, nullable=False)
    output_text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_output: Mapped[Optional[str]] = mapped_column(Text)

    # Stage 0
    stage0_pii_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    stage0_exact_match: Mapped[bool] = mapped_column(Boolean, default=False)
    stage0_latency_ms: Mapped[Optional[float]] = mapped_column(Float)

    # Stage 1
    stage1_max_similarity: Mapped[Optional[float]] = mapped_column(Float)
    stage1_mean_top3: Mapped[Optional[float]] = mapped_column(Float)
    stage1_top_chunk_id: Mapped[Optional[str]] = mapped_column(String(36))
    stage1_top_document: Mapped[Optional[str]] = mapped_column(String(500))
    stage1_triggered_stage2: Mapped[bool] = mapped_column(Boolean, default=False)
    stage1_latency_ms: Mapped[Optional[float]] = mapped_column(Float)

    # Stage 2 (nullable — only when stage 2 runs)
    stage2_factual_score: Mapped[Optional[float]] = mapped_column(Float)
    stage2_atomic_claims: Mapped[Optional[dict]] = mapped_column(JSON)
    stage2_contaminated_claims: Mapped[Optional[dict]] = mapped_column(JSON)
    stage2_is_reconstruction: Mapped[Optional[bool]] = mapped_column(Boolean)
    stage2_llm_reasoning: Mapped[Optional[str]] = mapped_column(Text)
    stage2_latency_ms: Mapped[Optional[float]] = mapped_column(Float)

    # Stage 3 — session
    session_cumulative_score: Mapped[Optional[float]] = mapped_column(Float)
    session_turn_number: Mapped[Optional[int]] = mapped_column(Integer)
    session_escalated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Final decision
    composite_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)           # ALLOW | WARN | BLOCK
    decision_rationale: Mapped[Optional[str]] = mapped_column(Text)
    flagged_lineage_tags: Mapped[list] = mapped_column(JSON, default=list)
    total_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)

    # Human feedback
    human_review_status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING | CONFIRMED_TP | CONFIRMED_FP | CONFIRMED_FN | IGNORED
    human_reviewer: Mapped[Optional[str]] = mapped_column(String(200))
    human_review_notes: Mapped[Optional[str]] = mapped_column(Text)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ─────────────────────────────────────────────────────────────────────────────
# TEST SUITE
# ─────────────────────────────────────────────────────────────────────────────

class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    case_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)   # e.g. "NORMAL-01"
    category: Mapped[str] = mapped_column(String(50), nullable=False)               # NORMAL | PARAPHRASED | BORDERLINE | ADVERSARIAL
    attack_type: Mapped[Optional[str]] = mapped_column(String(50))                            # AT-01 … AT-08 (NULL for normal)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    vault_source_tag: Mapped[Optional[str]] = mapped_column(String(200))                      # lineage_tag of source (if applicable)
    expected_decision: Mapped[str] = mapped_column(String(20), nullable=False)      # ALLOW | WARN | BLOCK
    expected_min_score: Mapped[Optional[float]] = mapped_column(Float)
    expected_max_score: Mapped[Optional[float]] = mapped_column(Float)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class TestSuiteRun(Base):
    __tablename__ = "test_suite_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    run_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    config_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    results_per_case: Mapped[dict] = mapped_column(JSON, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    total_latency_ms: Mapped[Optional[float]] = mapped_column(Float)
