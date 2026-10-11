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


def test_adversarial_graphics_category_generation(client, operator_headers):
    """Test generation of graphics driver boundary test cases via API."""
    res = client.post(
        "/api/v1/adversarial/generate?category=agc_driver_boundary&count=5",
        headers=operator_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["generated_count"] > 0
    symbols = [s["name"] for s in data["symbols"]]
    assert any("sceAgcDriver" in s for s in symbols)


def test_adversarial_stress_test_endpoint(client, operator_headers):
    """Test adversarial stress test endpoint returns stability scores."""
    res = client.post(
        "/api/v1/adversarial/stress-test",
        headers=operator_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["total_cases"] > 0
    assert data["stability_score"] >= 90.0
    assert data["false_positive_rate"] == 0.0
    assert "agc_driver_boundary" in data["category_scores"]
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
    assert "adversarial_stability" in analytics
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
    assert analytics_res["metrics"]["f1"] > 0.0
    assert "shader_diagnostics" in analytics_res


def test_shaders_rdna2_layout_endpoint(client, operator_headers):
    """Test retrieving RDNA2 ancillary VGPR layout specification."""
    res = client.get("/api/v1/shaders/rdna2-layout", headers=operator_headers)
    assert res.status_code == 200
    layout = res.json()
    assert len(layout) > 0
    names = [item["name"] for item in layout]
    assert "render_target_index" in names
    assert "sample_index" in names
    assert "prim_type" in names
    rt = next(i for i in layout if i["name"] == "render_target_index")
    assert rt["offset"] == 16
    assert rt["modeled"] is True


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
    assert data["rebuildable_pr1179"] is True
    assert data["decoded_word"] is not None
    assert data["decoded_word"]["sample_index"]["value"] == 2
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
    assert data["rebuildable_pr1179"] is False
    assert data["register_reused"] is True
    assert "SelectU32" in data["live_use_chain"]


def test_shaders_stray_batch_endpoint(client, operator_headers):
    """Test retrieving batch analysis for Stray (PPSA02100) catalog shaders."""
    res = client.get("/api/v1/shaders/stray-batch", headers=operator_headers)
    assert res.status_code == 200
    shaders = res.json()
    assert len(shaders) == 26
    assert all(s["title_id"] == "PPSA02100" for s in shaders)
    assert all(s["status"] == "rejected_unsupported_live_use" for s in shaders)


def test_structurizer_presets_endpoint(client, operator_headers):
    """Test retrieving CFG structurizer presets."""
    res = client.get("/api/v1/structurizer/presets", headers=operator_headers)
    assert res.status_code == 200
    presets = res.json()
    assert len(presets) >= 2
    repro = next(p for p in presets if p["id"] == "issue-2642-repro")
    assert repro["adjacency"] == [[1], [2, 4], [3, 4], [4, 5], [1, 6], [1], []]
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
    assert report["name"] == "custom-test-repro"
    assert report["exceeded_budget"] is True
    assert report["matches_issue_2642"] is True
    assert report["original_blocks"] == 7
    assert report["split_budget"] == 28
    assert report["current_blocks"] >= 28
    assert len(report["multi_latch_loops"]) == 1
    assert len(report["selection_conflicts"]) >= 1
    assert "Decouple loop latch join" in report["recommendation"]


def test_storage_writeback_presets_endpoint(client, operator_headers):
    """Test retrieving storage writeback presets."""
    res = client.get("/api/v1/storage-writeback/presets", headers=operator_headers)
    assert res.status_code == 200
    presets = res.json()
    assert len(presets) >= 2
    repro = next(p for p in presets if p["id"] == "silksong-sdf-atlas")
    assert repro["texture_address"] == 0x25E042000
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
    assert report["title_id"] == "PPSA12544"
    assert report["block_policy_corrupted"] is True
    assert report["page_policy_corrupted"] is False
    assert report["edge_blocks_count"] == 2
    assert "OPTIONS_O" in report["corrupted_glyphs"]
    assert report["status"] == "conflict_detected"
    assert len(report["units"]) > 0





