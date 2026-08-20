import pytest
from unittest.mock import MagicMock, patch
from services.factual_verifier import FactualVerifier, FactualVerificationResult, ContaminatedClaim
from services.embedding_scorer import ChunkMatch

def test_parse_llm_response():
    raw_response = """
    {
      "atomic_claims": ["Patient John Doe is 44 years old", "Patient John Doe has Stage 2 Neuroendocrine Tumor"],
      "contaminated_claims": [
        {
          "claim": "Patient John Doe has Stage 2 Neuroendocrine Tumor",
          "source_reference": "Stage 2 Neuroendocrine Tumor, Pancreatic Origin",
          "confidence": 0.95,
          "is_obfuscated": false
        }
      ],
      "factual_overlap_score": 0.8,
      "reasoning": "Output matches pancreatic tumor diagnosis from reference.",
      "is_reconstruction_attack": false
    }
    """
    
    verifier = FactualVerifier()
    result = verifier._parse_llm_response(raw_response, provider_used="openai")
    
    assert result.factual_overlap_score == 0.85
    assert len(result.atomic_claims) == 2
    assert result.atomic_claims[0] == "Patient John Doe is 44 years old"
    assert len(result.contaminated_claims) == 1
    assert result.contaminated_claims[0].claim == "Patient John Doe has Stage 2 Neuroendocrine Tumor"
    assert result.contaminated_claims[0].confidence == 0.95
    assert result.contaminated_claims[0].is_obfuscated is False
    assert result.reasoning == "Output matches pancreatic tumor diagnosis from reference."
    assert result.is_reconstruction_attack is False
    assert result.provider_used == "openai"


def test_parse_llm_response_with_markdown_fences():
    raw_response = """```json
    {
      "atomic_claims": ["Test claim"],
      "contaminated_claims": [],
      "factual_overlap_score": 0.1,
      "reasoning": "None",
      "is_reconstruction_attack": false
    }
    ```"""
    
    verifier = FactualVerifier()
    result = verifier._parse_llm_response(raw_response, provider_used="gemini")
    
    assert result.factual_overlap_score == 0.1
    assert result.atomic_claims == ["Test claim"]
    assert result.provider_used == "gemini"


def test_parse_llm_response_invalid_json_fallback():
    raw_response = "invalid json text here"
    
    verifier = FactualVerifier()
    with pytest.raises(ValueError):
         verifier._parse_llm_response(raw_response, provider_used="openai")


def test_verify_rule_based_fallback():
    # Test that the rule-based verification executes and computes expected Jaccard/precision scores
    verifier = FactualVerifier()
    
    # Text with specific terms: Robert Tanaka, CFO, EMP-00101
    output_text = "The CFO Robert Tanaka is matching EMP-00101"
    
    matches = [
        ChunkMatch(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_name="Executive_Compensation.txt",
            lineage_tag="VAULT-HR-EXEC",
            classification="TOP_SECRET",
            department="HR",
            chunk_text="NAME: Robert Tanaka\nTITLE: Chief Financial Officer\nEMPLOYEE ID: EMP-00101",
            chunk_index=0,
            similarity=0.85
        )
    ]
    
    result = verifier._verify_rule_based(output_text, matches)
    
    assert result.factual_overlap_score > 0.0
    assert result.provider_used == "rule_based"
    assert len(result.contaminated_claims) > 0
    # The term 'robert', 'tanaka', 'cfo', 'emp-00101' should match
    matched_terms = [c.claim for c in result.contaminated_claims]
    assert any("cfo" in term.lower() or "tanaka" in term.lower() for term in matched_terms)


@patch("services.factual_verifier.FactualVerifier._verify_openai")
def test_verify_llm_failure_falls_back_to_rule_based(mock_verify_openai):
    # Mock LLM raising an exception, it should fallback to rule_based
    mock_verify_openai.side_effect = Exception("OpenAI API Down")
    
    verifier = FactualVerifier()
    
    with patch.dict("os.environ", {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "dummy-key"}):
        from config import settings
        # Force setting update
        settings.LLM_PROVIDER = "openai"
        settings.OPENAI_API_KEY = "dummy-key"
        
        matches = [
            ChunkMatch(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_name="Executive_Compensation.txt",
                lineage_tag="VAULT-HR-EXEC",
                classification="TOP_SECRET",
                department="HR",
                chunk_text="NAME: Sarah Jenkins\nTITLE: Senior Vice President",
                chunk_index=0,
                similarity=0.80
            )
        ]
        
        result = verifier.verify("Sarah Jenkins is in our clinical development team.", matches)
        
        assert result.provider_used == "rule_based"
        assert result.factual_overlap_score > 0.0
