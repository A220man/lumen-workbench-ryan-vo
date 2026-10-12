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
    # Create
    create_res = client.post(
        "/api/v1/titles",
        json={"name": "Test Title", "description": "A test", "status": "active"},
        headers=operator_headers,
    )
    assert create_res.status_code == 201
    title = create_res.json()
    assert title["name"] == "Test Title"
    assert title["status"] == "active"
    title_id = title["id"]

    # List
    list_res = client.get("/api/v1/titles", headers=operator_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # Retrieve
    get_res = client.get(f"/api/v1/titles/{title_id}", headers=operator_headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Test Title"

    # Retrieve by PPSSA ID
    get_ppsa_res = client.get("/api/v1/titles/ppsa/PPSA12345", headers=operator_headers)
    assert get_ppsa_res.status_code == 404

    # Update
    update_res = client.put(
        f"/api/v1/titles/{title_id}",
        json={"description": "Updated", "status": "archived"},
        headers=operator_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["description"] == "Updated"
    assert update_res.json()["status"] == "archived"

    # Delete
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
    assert "resolved_count" in report
    assert "unresolved_count" in report
    assert "missing_module_count" in report
    assert "coverage" in report
    assert "score" in report
    assert "blockers" in report


def test_evaluations_run_endpoint(client, operator_headers):
    """Test benchmark evaluation runner endpoint."""
    res = client.post("/api/v1/evaluations/run", json={}, headers=operator_headers)
    assert res.status_code == 200
    data = res.json()
    assert "f1" in data
    assert "precision" in data
    assert "recall" in data
    assert "coverage" in data
    assert 0 <= data["f1"] <= 1


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
    assert all(s["name"].startswith("sceTest") for s in data["symbols"])


def test_adversarial_graphics_category_generation(client, operator_headers):
    """Test generation of graphics driver boundary test cases via API."""
    res = client.post(
        "/api/v1/adversarial/generate?category=agc_driver_boundary&count=5",
        headers=operator_headers,
    )
    assert res.status_code == 200
    data = res.json()
    symbols = data["symbols"]
    assert data["generated_count"] == 5
    assert any("sceAgcDriver" in s["name"] for s in symbols)


def test_adversarial_stress_test_endpoint(client, operator_headers):
    """Test adversarial stress test endpoint returns stability scores."""
    res = client.post(
        "/api/v1/adversarial/stress-test",
        headers=operator_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_cases"] >= 20
    assert "stability_score" in data
    assert "false_positive_rate" in data
    assert "category_scores" in data
    assert "video_out_boundary" in data["category_scores"]


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
    assert "total_imports" in stats
    assert "resolution_rate" in stats
    assert "evaluation_count" in stats
    assert "%" in stats["resolution_rate"]


def test_system_analytics_endpoint(client, operator_headers):
    """Test retrieval of domain analytics and per-library breakdowns."""
    res = client.get("/api/v1/analytics", headers=operator_headers)
    assert res.status_code == 200
    analytics = res.json()
    assert "per_library" in analytics
    assert "metrics" in analytics
    assert "stability" in analytics["adversarial_stability"]


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
    assert "shader_diagnostics" in analytics_res


def test_shaders_rdna2_layout_endpoint(client, operator_headers):
    """Test retrieving RDNA2 ancillary VGPR layout specification."""
    res = client.get("/api/v1/shaders/rdna2-layout", headers=operator_headers)
    assert res.status_code == 200
    layout = res.json()
    assert len(layout) >= 5
    rt = next(item for item in layout if item["name"] == "render_target_index")
    assert rt["modeled"] is True
    si = next(item for item in layout if item["name"] == "sample_index")
    assert si["modeled"] is True


def test_shaders_analyze_endpoint_rebuildable(client, operator_headers):
    """Test analyzing a shader with clean bitfield extractions."""
    payload = {
        "shader_address": "0x1000",
        "title_id": "PPSA00001",
        "ancillary_vgpr": "v4",
        "instructions": [
            {"index": 0, "opcode": "BitFieldUExtract", "dest": "v0", "sources": ["v4"], "bit_offset": 16, "bit_length": 11},
            {"index": 1, "opcode": "BitFieldUExtract", "dest": "v1", "sources": ["v4"], "bit_offset": 8, "bit_length": 4},
        ],
        "raw_word": 0x00050200,
    }
    res = client.post("/api/v1/shaders/analyze", json=payload, headers=operator_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "rebuildable"
    assert data["rejection_reason"] is None
    assert data["decoded_word"]["render_target_index"]["value"] == 5


def test_shaders_analyze_endpoint_live_use_rejection(client, operator_headers):
    """Test analyzing a shader with UE4 register reuse (issue #2548)."""
    payload = {
        "shader_address": "0x200e370000",
        "title_id": "PPSA02100",
        "ancillary_vgpr": "v4",
        "instructions": [
            {"index": 0, "opcode": "BitFieldUExtract", "dest": "vN", "sources": ["v4"], "bit_offset": 16, "bit_length": 11},
            {"index": 1, "opcode": "SelectU32", "dest": "v4", "sources": ["v4", "SelectU32 ? ?"], "condition": "IEqual32(HelperInvocation, 0)"},
            {"index": 2, "opcode": "Phi", "dest": "v4_phi", "sources": ["v4"]},
            {"index": 3, "opcode": "BitCastF32U32", "dest": "f_val", "sources": ["v4_phi"]},
            {"index": 4, "opcode": "PackFloat2x16Rtz", "dest": "packed_attr", "sources": ["f_val"]},
            {"index": 5, "opcode": "SetAttribute", "dest": None, "sources": ["packed_attr"]},
        ],
    }
    res = client.post("/api/v1/shaders/analyze", json=payload, headers=operator_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "rejected_unsupported_live_use"
    assert "SelectU32" in data["live_use_chain"]


def test_shaders_stray_batch_endpoint(client, operator_headers):
    """Test retrieving batch analysis for Stray (PPSA02100) catalog shaders."""
    res = client.get("/api/v1/shaders/stray-batch", headers=operator_headers)
    assert res.status_code == 200
    shaders = res.json()
    assert len(shaders) == 26
    assert all(s["status"] == "rejected_unsupported_live_use" for s in shaders)


def test_structurizer_presets_endpoint(client, operator_headers):
    """Test retrieving CFG structurizer presets."""
    res = client.get("/api/v1/structurizer/presets", headers=operator_headers)
    assert res.status_code == 200
    presets = res.json()
    assert len(presets) >= 2
    repro = next(p for p in presets if p["id"] == "issue-2642-repro")
    assert repro["expected_status"] == "budget_exceeded"


def test_structurizer_analyze_endpoint(client, operator_headers):
    """Test analyzing a CFG graph for merge splitting budget and loop latches."""
    payload = {
        "name": "custom-test-repro",
        "adjacency": [[1], [2, 4], [3, 4], [4, 5], [1, 6], [1], []],
        "split_budget": 28,
    }
    res = client.post("/api/v1/structurizer/analyze", json=payload, headers=operator_headers)
    assert res.status_code == 200
    report = res.json()
    assert report["exceeded_budget"] is True
    assert report["matches_issue_2642"] is True
    assert "Decouple loop latch join" in report["recommendation"]


def test_storage_writeback_presets_endpoint(client, operator_headers):
    """Test retrieving storage writeback presets."""
    res = client.get("/api/v1/storage-writeback/presets", headers=operator_headers)
    assert res.status_code == 200
    presets = res.json()
    assert len(presets) >= 2
    repro = next(p for p in presets if p["id"] == "silksong-sdf-atlas")
    assert repro["expected_status"] == "conflict_detected"


def test_storage_writeback_simulate_endpoint(client, operator_headers):
    """Test simulating storage writeback conflict for Silksong issue #865."""
    payload = {
        "title_id": "PPSA12544",
        "title_name": "Hollow Knight: Silksong (Unity TextCore)",
        "texture_address": 0x25E042000,
        "texture_size": 0x40000,
        "gpu_dispatch_generation": 87617,
    }
    res = client.post("/api/v1/storage-writeback/simulate", json=payload, headers=operator_headers)
    assert res.status_code == 200
    report = res.json()
    assert report["status"] == "conflict_detected"
    assert len(report["units"]) > 0


def test_first_light_stops_endpoint(client, operator_headers):
    """Test retrieving 007 First Light startup stops (issue #2523)."""
    resp = client.get("/api/v1/first-light/stops", headers=operator_headers)
    assert resp.status_code == 200
    stops = resp.json()
    assert len(stops) == 13
    assert stops[0]["index"] == 1
    assert stops[12]["index"] == 13
    assert "sceSslGetCaList" in stops[0]["error_text"]
    assert "static bindless image capacity" in stops[12]["error_text"]
    assert len(stops[0]["prs"]) == 2
    assert len(stops[12]["prs"]) == 0
    assert stops[0]["verified"] is True
    assert stops[12]["verified"] is False


def test_first_light_analyze_endpoint(client, operator_headers):
    """Test analyzing First Light sequence with applied PRs."""
    # No PRs - blocked at stop 1
    resp = client.post("/api/v1/first-light/analyze", json={"applied_prs": []}, headers=operator_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_stop"] == 1
    assert data["passed_stops"] == 0
    assert data["failed_stops"] == 12
    assert data["status"] == "blocked"
    assert data["regression_detected"] is True

    # Apply stops 1-3 PRs
    resp = client.post(
        "/api/v1/first-light/analyze",
        json={"applied_prs": [2830, 2831, 2946, 1964]},
        headers=operator_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_stop"] == 4
    assert data["passed_stops"] == 3
    assert data["failed_stops"] == 9

    # Apply all main repo merged PRs through stop 12 (stop 5 only has SleglJan fork PR)
    all_prs = [2830, 2831, 2946, 1964, 3134, 2455, 2282, 2463, 2471, 1184, 2347, 1893]
    resp = client.post(
        "/api/v1/first-light/analyze",
        json={"applied_prs": all_prs},
        headers=operator_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Stop 5 requires SleglJan fork PR (not in main repo), so 11 passed, 1 failed
    assert data["passed_stops"] == 11
    assert data["failed_stops"] == 1
    assert data["current_stop"] == 5
    assert data["status"] == "blocked"
    assert data["regression_detected"] is True


def test_first_light_presets_endpoint(client, operator_headers):
    """Test retrieving First Light diagnostic presets."""
    resp = client.get("/api/v1/first-light/presets", headers=operator_headers)
    assert resp.status_code == 200
    presets = resp.json()
    assert len(presets) >= 6
    names = {p["name"] for p in presets}
    assert "main (no fixes)" in names
    assert "stops 1-3 fixed" in names
    assert "stops 1-12 fixed" in names
    main_preset = next(p for p in presets if p["name"] == "main (no fixes)")
    assert main_preset["applied_prs"] == []