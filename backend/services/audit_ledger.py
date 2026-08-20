"""
services/audit_ledger.py — Immutable audit log writer and reader.
"""
import hashlib
import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import AuditLog
from services.embedding_scorer import SimilarityResult
from services.factual_verifier import FactualVerificationResult
from services.hybrid_risk_engine import RiskDecision
from services.pre_filter import PreFilterResult
from services.session_aggregator import SessionState

logger = logging.getLogger(__name__)


class AuditLedger:
    """Immutable audit log writer and reader."""

    def record(
        self,
        db: Session,
        *,
        agent_id: str,
        session_id: Optional[str],
        output_text: str,
        prompt_text: Optional[str],
        pre_result: PreFilterResult,
        s1_result: SimilarityResult,
        s2_result: Optional[FactualVerificationResult],
        session_state: SessionState,
        risk_decision: RiskDecision,
        total_latency_ms: float,
    ) -> AuditLog:
        """Persist a complete evaluation audit record to the database."""

        output_hash = hashlib.sha256(output_text.encode()).hexdigest()
        request_id = str(uuid.uuid4())

        # Build lineage tag JSON
        lineage_tags_json = [
            {
                "tag": t.tag,
                "document_name": t.document_name,
                "classification": t.classification,
                "department": t.department,
                "data_type": t.data_type,
                "match_score": round(t.match_score, 4),
            }
            for t in risk_decision.lineage_tags
        ]

        # S2 fields
        s2_atomic = None
        s2_contaminated = None
        s2_is_recon = None
        s2_reasoning = None
        s2_latency = None
        s2_factual_score = None

        if s2_result is not None:
            s2_factual_score = s2_result.factual_overlap_score
            s2_atomic = s2_result.atomic_claims
            s2_contaminated = [
                {
                    "claim": c.claim,
                    "source_reference": c.source_reference,
                    "confidence": round(c.confidence, 3),
                    "is_obfuscated": c.is_obfuscated,
                }
                for c in s2_result.contaminated_claims
            ]
            s2_is_recon = s2_result.is_reconstruction_attack
            s2_reasoning = s2_result.reasoning
            s2_latency = s2_result.latency_ms

        # S1 top match info
        top_chunk_id = None
        top_doc_name = None
        if s1_result.top_match:
            top_chunk_id = s1_result.top_match.chunk_id
            top_doc_name = s1_result.top_match.document_name

        log = AuditLog(
            agent_id=agent_id,
            session_id=session_id,
            request_id=request_id,
            prompt_preview=(prompt_text or "")[:500] if prompt_text else None,
            output_text=output_text,
            output_text_hash=output_hash,
            normalized_output=pre_result.normalized_text[:5000],

            stage0_pii_detected=bool(pre_result.pii_flags),
            stage0_exact_match=pre_result.exact_hash_match,
            stage0_latency_ms=pre_result.latency_ms,

            stage1_max_similarity=round(s1_result.max_similarity, 4),
            stage1_mean_top3=round(s1_result.mean_top3, 4),
            stage1_top_chunk_id=top_chunk_id,
            stage1_top_document=top_doc_name,
            stage1_triggered_stage2=s1_result.triggered_stage2,
            stage1_latency_ms=s1_result.latency_ms,

            stage2_factual_score=(
                round(s2_factual_score, 4)
                if s2_factual_score is not None
                else None
            ),
            stage2_atomic_claims=s2_atomic,
            stage2_contaminated_claims=s2_contaminated,
            stage2_is_reconstruction=s2_is_recon,
            stage2_llm_reasoning=s2_reasoning,
            stage2_latency_ms=s2_latency,

            session_cumulative_score=round(session_state.cumulative_score, 4),
            session_turn_number=session_state.turn_number,
            session_escalated=session_state.escalated,

            composite_risk_score=round(risk_decision.composite_risk_score, 4),
            decision=risk_decision.decision,
            decision_rationale=risk_decision.decision_rationale,
            flagged_lineage_tags=lineage_tags_json,
            total_latency_ms=round(total_latency_ms, 2),
        )

        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def get_logs(
        self,
        db: Session,
        agent_id: Optional[str] = None,
        decision: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditLog]:
        """Retrieve audit log entries with optional filters.

        Args:
            db: SQLAlchemy database session.
            agent_id: If provided, filters logs to this agent only.
            decision: If provided, filters logs by decision outcome (e.g. 'approved', 'rejected').
            limit: Maximum number of records to return. Defaults to 50.
            offset: Number of records to skip for pagination. Defaults to 0.

        Returns:
            A list of AuditLog ORM objects matching the given filters.
        """
        query = db.query(AuditLog)
        if agent_id:
            query = query.filter(AuditLog.agent_id == agent_id)
        if decision:
            query = query.filter(AuditLog.decision == decision)
        return (
            query.order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_stats(self, db: Session) -> Dict[str, Any]:
        """Retrieve aggregated statistics from the audit log."""
        total = db.query(func.count(AuditLog.id)).scalar() or 0
        blocked = (
            db.query(func.count(AuditLog.id))
            .filter(AuditLog.decision == "BLOCK")
            .scalar() or 0
        )
        warned = (
            db.query(func.count(AuditLog.id))
            .filter(AuditLog.decision == "WARN")
            .scalar() or 0
        )
        allowed = (
            db.query(func.count(AuditLog.id))
            .filter(AuditLog.decision == "ALLOW")
            .scalar() or 0
        )
        avg_score = (
            db.query(func.avg(AuditLog.composite_risk_score)).scalar() or 0.0
        )
        return {
            "total_evaluations": total,
            "blocked": blocked,
            "warned": warned,
            "allowed": allowed,
            "avg_composite_risk_score": round(float(avg_score), 4),
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
AUDIT_LEDGER = AuditLedger()


def get_audit_ledger() -> AuditLedger:
    """Get the module-level singleton instance of AuditLedger."""
    return AUDIT_LEDGER
