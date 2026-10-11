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
