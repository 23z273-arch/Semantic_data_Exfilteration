import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import app from main
from main import app

@pytest.fixture(scope="module")
def client():
    # 'with' statement triggers the lifespan event (startup & shutdown)
    with TestClient(app) as c:
        yield c


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["service"] == "Semantic Data Exfiltration Detector"
    assert "version" in json_data


def test_health_endpoint(client):
    response = client.get("/v1/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "healthy"
    assert "components" in json_data
    assert json_data["components"]["database"] == "healthy"
    assert json_data["components"]["vector_store"] == "healthy"


def test_evaluate_endpoint_allow(client):
    # Evaluate a generic, non-matching input string
    payload = {
        "agent_id": "test-agent",
        "output_text": "This is completely normal output text about writing asynchronous code in Python.",
        "include_debug": True
    }
    response = client.post("/v1/governance/evaluate", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert "evaluation_id" in json_data
    assert json_data["decision"] == "ALLOW"
    assert json_data["composite_risk_score"] < 0.5
    assert json_data["stage_executed"] == 1


def test_evaluate_endpoint_semantic_block(client):
    # Paraphrase of the clinical trial patient record — should score high semantic similarity
    # and be BLOCKED or WARNED (no exact hash match needed)
    payload = {
        "agent_id": "test-agent",
        "output_text": (
            "Patient ID PT-0042, John Doe, born April 1981. "
            "Diagnosed with Stage 2 Neuroendocrine Tumor of pancreatic origin. "
            "MEN1 positive mutation confirmed. Currently on TX-9082, 45mg weekly oral tablet. "
            "Enrolled in Arm B of the Meridian Biosciences clinical trial."
        ),
        "include_debug": False
    }
    response = client.post("/v1/governance/evaluate", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    # Should flag as BLOCK or WARN due to high semantic similarity to the clinical trial vault doc
    assert json_data["decision"] in ("BLOCK", "WARN")
    assert json_data["composite_risk_score"] >= 0.50
    assert json_data["stage0"]["exact_match"] is False


def test_benchmark_run_endpoint(client):
    # Test executing a subset category of benchmarks to ensure the route functions properly
    payload = {
        "categories": ["PARAPHRASED"],
        "include_per_case_details": True
    }
    response = client.post("/v1/governance/benchmark/run", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert "run_id" in json_data
    assert "metrics" in json_data
    assert "overall" in json_data["metrics"]
    assert "by_category" in json_data["metrics"]
    assert "PARAPHRASED" in json_data["metrics"]["by_category"]


# ── Tier-2 tests ──────────────────────────────────────────────────────────────

def test_metrics_endpoint_shape(client):
    """GET /v1/governance/metrics must return all expected keys."""
    response = client.get("/v1/governance/metrics")
    assert response.status_code == 200
    data = response.json()

    assert "verifier" in data
    assert "embedding" in data
    assert "rate_limiter" in data

    # Verifier keys
    v = data["verifier"]
    for key in ("total_calls", "cache_hits", "cache_misses", "cache_size",
                "max_cache_size", "cache_hit_rate", "avg_latency_ms", "provider_distribution"):
        assert key in v, f"Missing verifier key: {key}"
    assert v["max_cache_size"] == 512
    assert 0.0 <= v["cache_hit_rate"] <= 1.0

    # Embedding keys
    e = data["embedding"]
    for key in ("provider", "dim", "cache_size", "max_cache_size"):
        assert key in e, f"Missing embedding key: {key}"
    assert e["max_cache_size"] == 2048

    # Rate-limiter keys
    rl = data["rate_limiter"]
    assert "global_hits" in rl
    assert "per_agent_hits_total" in rl
    assert isinstance(rl["top_limited_agents"], list)
    # Each throttled-agent entry must be a proper dict, not a tuple
    for entry in rl["top_limited_agents"]:
        assert "agent_id" in entry and "hits" in entry


def test_evaluate_rejects_blank_output_text(client):
    """Pure-whitespace output_text must return 422 Unprocessable Entity."""
    payload = {"agent_id": "test-agent", "output_text": "   \t\n  "}
    response = client.post("/v1/governance/evaluate", json=payload)
    assert response.status_code == 422


def test_evaluate_rejects_oversized_output_text(client):
    """output_text exceeding 50 000 characters must return 422 Unprocessable Entity."""
    payload = {"agent_id": "test-agent", "output_text": "x" * 50_001}
    response = client.post("/v1/governance/evaluate", json=payload)
    assert response.status_code == 422


def test_metrics_total_calls_increases(client):
    """total_calls in /metrics must increment after each /evaluate call."""
    before = client.get("/v1/governance/metrics").json()["verifier"]["total_calls"]

    client.post("/v1/governance/evaluate", json={
        "agent_id": "metrics-probe",
        "output_text": "Normal benign output with absolutely no sensitive data.",
        "similarity_threshold_override": 0.0,
    })

    after = client.get("/v1/governance/metrics").json()["verifier"]["total_calls"]
    assert after > before
