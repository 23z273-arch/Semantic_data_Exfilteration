import pytest
from services.hybrid_risk_engine import HybridRiskEngine, _infer_data_type
from services.embedding_scorer import SimilarityResult, ChunkMatch
from services.factual_verifier import FactualVerificationResult
from services.session_aggregator import SessionState

def test_decide_stage1_only():
    engine = HybridRiskEngine()
    
    # Cosine similarity 0.40, which is below trigger threshold (0.55)
    s1 = SimilarityResult(
        max_similarity=0.40,
        mean_top3=0.30,
        triggered_stage2=False,
        top_matches=[],
        latency_ms=10.0
    )
    
    session_state = SessionState(session_id="test-session", turn_number=1, cumulative_score=0.40, escalated=False)
    
    decision = engine.decide(s1=s1, s2=None, session_state=session_state)
    
    assert decision.decision == "ALLOW"
    assert decision.composite_risk_score == 0.40
    assert decision.stage_executed == 1
    assert len(decision.lineage_tags) == 0


def test_decide_stage2_composite():
    engine = HybridRiskEngine()
    
    # Cosine similarity 0.70, which triggers Stage 2
    s1 = SimilarityResult(
        max_similarity=0.70,
        mean_top3=0.60,
        triggered_stage2=True,
        top_matches=[
            ChunkMatch(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_name="Executive_Compensation_2026_Q2.txt",
                lineage_tag="VAULT-HR-EXEC-2026-Q2",
                classification="TOP_SECRET",
                department="Human Resources",
                chunk_text="NAME: Sarah Jenkins",
                chunk_index=0,
                similarity=0.70
            )
        ],
        latency_ms=15.0
    )
    
    # Stage 2 factual overlap is 0.80
    s2 = FactualVerificationResult(
        factual_overlap_score=0.80,
        atomic_claims=["Claim 1"],
        contaminated_claims=[],
        reasoning="Contamination found",
        provider_used="mock"
    )
    
    session_state = SessionState(session_id="test-session", turn_number=1, cumulative_score=0.75, escalated=False)
    
    # Composite = 0.3 * S1 (0.7) + 0.7 * S2 (0.8) = 0.21 + 0.56 = 0.77
    # Threshold block is >= 0.75, so should BLOCK
    decision = engine.decide(s1=s1, s2=s2, session_state=session_state)
    
    assert decision.decision == "BLOCK"
    assert abs(decision.composite_risk_score - 0.77) < 1e-5
    assert decision.stage_executed == 2
    assert len(decision.lineage_tags) == 1
    assert decision.lineage_tags[0].tag == "VAULT-HR-EXEC-2026-Q2"
    assert decision.lineage_tags[0].data_type == "HR_COMPENSATION_RECORD"


def test_decide_session_escalation():
    engine = HybridRiskEngine()
    
    s1 = SimilarityResult(
        max_similarity=0.50,
        mean_top3=0.40,
        triggered_stage2=False,
        top_matches=[],
        latency_ms=10.0
    )
    
    # Session escalated is True, composite should be multiplied by 1.25
    # Composite = 0.50 * 1.25 = 0.625
    # Threshold warn is >= 0.50, so should WARN
    session_state = SessionState(session_id="test-session", turn_number=3, cumulative_score=0.70, escalated=True)
    
    decision = engine.decide(s1=s1, s2=None, session_state=session_state)
    
    assert decision.decision == "WARN"
    assert decision.composite_risk_score == 0.625
    assert decision.session_escalated is True


def test_infer_data_type():
    assert _infer_data_type("VAULT-HR-EXEC-2026-Q2") == "HR_COMPENSATION_RECORD"
    assert _infer_data_type("VAULT-MED-TRIAL-TX9082") == "CLINICAL_TRIAL_RECORD"
    assert _infer_data_type("VAULT-FIN-ACQ-NEXUS") == "FINANCIAL_STRATEGIC_MEMO"
    assert _infer_data_type("VAULT-IT-INFRA-NET") == "INFRASTRUCTURE_CREDENTIALS"
    assert _infer_data_type("ANY-OTHER-TAG") == "PROTECTED_DOCUMENT"
