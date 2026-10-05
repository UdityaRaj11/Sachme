import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "TruthFirewall" in data["service"]

def test_get_and_update_credibility_weights():
    # 1. Get current weights
    get_res = client.get("/api/v1/config/credibility-weights")
    assert get_res.status_code == 200
    orig_weights = get_res.json()["weights"]

    # 2. Update weights
    post_res = client.post(
        "/api/v1/config/credibility-weights",
        json={"tier_weight": 0.40, "domain_reputation": 0.30}
    )
    assert post_res.status_code == 200
    updated_weights = post_res.json()["active_weights"]
    assert updated_weights["tier_weight"] == 0.40
    assert updated_weights["domain_reputation"] == 0.30

def test_sync_verification_direct_text_scam_claim():
    """
    Tests the canonical user scenario from Section 11:
    'Government is giving ₹25,000 to every student.'
    """
    req_payload = {
        "url": None,
        "direct_text": "Government is giving ₹25,000 to every student. Register now at http://free-scholarship.xyz"
    }

    response = client.post("/api/v1/verify/sync", json=req_payload)
    assert response.status_code == 200
    data = response.json()

    # Verify JSON structure matches Section 10 strictly
    assert data["status"] == "success"
    assert "content" in data
    assert "claims" in data
    assert len(data["claims"]) >= 1
    assert "overall_verdict" in data
    assert "overall_confidence" in data
    assert isinstance(data["overall_confidence"], int)

    # Claim evaluation
    claim0 = data["claims"][0]
    assert "claim_id" in claim0
    assert "claim" in claim0
    assert "verdict" in claim0
    assert "confidence" in claim0
    assert "evidence" in claim0
    assert "explanation" in claim0

    # Ensure verdict is CONTRADICTED
    assert data["overall_verdict"] == "CONTRADICTED"
    assert claim0["verdict"] == "CONTRADICTED"
    assert claim0["confidence"] >= 80

    # Check evidence provenance
    assert len(claim0["evidence"]) > 0
    first_ev = claim0["evidence"][0]
    assert "pib.gov.in" in first_ev["url"] or "altnews" in first_ev["url"]
    assert first_ev["credibility_score"] >= 85

    # Check UI presentation model matching Section 11
    assert "user_interface" in data
    ui = data["user_interface"]
    assert "badge_label" in ui
    assert "Disproven" in ui["verdict_title"] or "misinformation" in ui["verdict_title"].lower()
    assert len(ui["evidence_points"]) >= 1

def test_async_verification_job_flow():
    req_payload = {
        "url": None,
        "direct_text": "PIB declares fake student scholarship message a scam."
    }
    # 1. Create job
    post_res = client.post("/api/v1/verify", json=req_payload)
    assert post_res.status_code == 202
    job_data = post_res.json()
    assert job_data["status"] == "queued"
    job_id = job_data["job_id"]

    # 2. Poll job status
    poll_res = client.get(f"/api/v1/jobs/{job_id}")
    assert poll_res.status_code == 200
    poll_data = poll_res.json()
    assert poll_data["job_id"] == job_id
    from app.models.api import JobStatus
    assert poll_data["status"] in [s.value for s in JobStatus]

def test_empty_request_validation_error():
    response = client.post("/api/v1/verify/sync", json={})
    assert response.status_code == 400

def test_unsupported_protocol_error():
    response = client.post(
        "/api/v1/verify/sync",
        json={"url": "https://example.com/trojan.exe"}
    )
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert data["error_type"] == "unsupported_content"
