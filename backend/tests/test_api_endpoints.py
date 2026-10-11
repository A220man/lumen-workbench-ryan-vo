import io
import pytest
from backend.app.api.auth import create_token


@pytest.fixture
def operator_headers():
    token = create_token("op-1", "operator@test.local", "Operator User", "operator")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers():
    token = create_token("ad-1", "admin@test.local", "Admin User", "admin")
    return {"Authorization": f"Bearer {token}"}


def test_titles_crud_lifecycle(client, operator_headers, admin_headers):
    """Test full Title lifecycle: create, list, retrieve, update, delete."""
    # 1. Create Title
    payload = {"name": "Demonstration Game", "description": "PS5 test binary", "status": "active"}
    create_res = client.post("/api/v1/titles", json=payload, headers=operator_headers)
    assert create_res.status_code == 201
    created = create_res.json()
    title_id = created["id"]
    assert created["name"] == "Demonstration Game"

    # 2. List Titles
    list_res = client.get("/api/v1/titles", headers=operator_headers)
    assert list_res.status_code == 200
    titles = list_res.json()
    assert len(titles) >= 1
    assert any(t["id"] == title_id for t in titles)

    # 3. Retrieve Title
    get_res = client.get(f"/api/v1/titles/{title_id}", headers=operator_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == title_id

    # 4. Update Title
    update_res = client.put(
        f"/api/v1/titles/{title_id}",
        json={"name": "Demonstration Game Updated", "status": "draft"},
        headers=operator_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Demonstration Game Updated"

    # 5. Delete Title (Admin only)
    del_res = client.delete(f"/api/v1/titles/{title_id}", headers=admin_headers)
    assert del_res.status_code == 204

    # Verify deleted
    get_after_del = client.get(f"/api/v1/titles/{title_id}", headers=operator_headers)
    assert get_after_del.status_code == 404


def test_import_analysis_endpoint(client, operator_headers):
    """Test ELF import analysis via file upload."""
    dummy_elf = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 128
    files = {"file": ("test_binary.elf", io.BytesIO(dummy_elf), "application/octet-stream")}
    res = client.post("/api/v1/imports/analyze", files=files, headers=operator_headers)
    assert res.status_code == 200
    report = res.json()
    assert report["source_name"] == "test_binary.elf"
    assert "score" in report
    assert "coverage" in report
    assert "resolved_count" in report


def test_evaluations_run_endpoint(client, operator_headers):
    """Test benchmark evaluation runner endpoint."""
    res = client.post("/api/v1/evaluations/run", json={}, headers=operator_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "precision" in data
    assert "recall" in data
    assert "f1" in data


def test_adversarial_generation_endpoint(client, operator_headers):
    """Test synthetic adversarial symbol generator endpoint."""
    res = client.post(
        "/api/v1/adversarial/generate?prefix=sceTest&count=3",
        headers=operator_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["generated_count"] == 3
    assert len(data["symbols"]) == 3


def test_system_stats_endpoint(client, operator_headers):
    """Test retrieval of system telemetry and runtime statistics."""
    # Create an active title to verify count
    client.post(
        "/api/v1/titles",
        json={"name": "Telemetry Active Title", "status": "active"},
        headers=operator_headers,
    )
    res = client.get("/api/v1/stats", headers=operator_headers)
    assert res.status_code == 200
    stats = res.json()
    assert "active_titles" in stats
    assert stats["active_titles"] >= 1
    assert "total_imports" in stats
    assert "resolution_rate" in stats
    assert "evaluation_count" in stats
    assert "%" in stats["resolution_rate"]


def test_system_analytics_endpoint(client, operator_headers):
    """Test retrieval of domain analytics and per-library breakdowns."""
    res = client.get("/api/v1/analytics", headers=operator_headers)
    assert res.status_code == 200
    analytics = res.json()
    assert "resolution_by_library" in analytics
    assert "performance_trend" in analytics
    assert "import_volume" in analytics
    assert "per_library" in analytics
    assert "metrics" in analytics
    assert "f1" in analytics["metrics"]
    assert "precision" in analytics["metrics"]
    assert "recall" in analytics["metrics"]
    assert "libkernel" in analytics["per_library"]


def test_integration_workflow_http_boundary(client, operator_headers):
    """Integration test verifying end-to-end data propagation across HTTP endpoints."""
    # 1. Check initial stats
    initial_stats = client.get("/api/v1/stats", headers=operator_headers).json()

    # 2. Create title
    create_res = client.post(
        "/api/v1/titles",
        json={"name": "Integration Target", "description": "Workflow verification", "status": "active"},
        headers=operator_headers,
    )
    assert create_res.status_code == 201
    title_id = create_res.json()["id"]

    # 3. Stats reflect new active title
    stats_after_title = client.get("/api/v1/stats", headers=operator_headers).json()
    assert stats_after_title["active_titles"] == initial_stats["active_titles"] + 1

    # 4. Run evaluation linking to this title
    eval_res = client.post(
        "/api/v1/evaluations/run",
        json={"title_id": title_id},
        headers=operator_headers,
    )
    assert eval_res.status_code == 200

    # 5. Stats reflect incremented evaluation count
    final_stats = client.get("/api/v1/stats", headers=operator_headers).json()
    assert final_stats["evaluation_count"] == initial_stats["evaluation_count"] + 1

    # 6. Analytics endpoint returns grounded metrics
    analytics_res = client.get("/api/v1/analytics", headers=operator_headers).json()
    assert analytics_res["metrics"]["f1"] > 0.0

