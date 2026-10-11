import pytest
from backend.core.nid import nid_of
from backend.services.import_resolver import ImportResolver, ResolvedImport
from backend.services.export_db import build_export_db
from backend.services.evaluator import run_evaluation, labeled_dataset
from backend.services.adversarial import AdversarialGenerator, run_stress_test
from backend.core.elf_parser import ELFImport, ELFError, parse_elf_imports


def test_nid_hashing_deterministic():
    """Verify NID hashing is deterministic across executions."""
    assert nid_of("sysctl") == nid_of("sysctl")
    assert nid_of("pthread_create") != nid_of("pthread_join")
    assert isinstance(nid_of("test_symbol"), int)
    assert 0 <= nid_of("test_symbol") <= 0xFFFFFFFF


def test_export_db_structure():
    """Verify host export surface contains required modules and symbols."""
    db = build_export_db()
    modules = {m.module for m in db}
    assert "libkernel" in modules
    kernel = next(m for m in db if m.module == "libkernel")
    assert "sysctl" in kernel.symbols
    assert "pthread_set_name_np" in kernel.symbols
    assert kernel.present is True


def test_import_resolver_known_symbol():
    """Verify ImportResolver resolves symbols found in export database."""
    resolver = ImportResolver()
    assert resolver.resolve_name("sysctl") == "libkernel"
    assert resolver.resolve_name("pthread_set_name_np") == "libkernel"


def test_import_resolver_unknown_symbol():
    """Verify unknown symbol returns None."""
    resolver = ImportResolver()
    assert resolver.resolve_name("unknown_nonexistent_symbol_xyz") is None


def test_resolver_batch_imports():
    """Verify resolution of a batch of ELF imports."""
    resolver = ImportResolver()
    imports = [
        ELFImport(name="sysctl", nid=0, library="", address=0),
        ELFImport(name="custom_missing_symbol", nid=0, library="", address=0),
    ]
    resolved = resolver.resolve_imports(imports)
    assert len(resolved) == 2
    assert resolved[0].status == "resolved"
    assert resolved[0].library == "libkernel"
    assert resolved[1].status == "unresolved"
    assert resolved[1].library is None


def test_evaluator_metrics():
    """Verify evaluator computes grounded metrics against labeled dataset."""
    resolver = ImportResolver()
    metrics = run_evaluation(resolver)
    assert metrics.precision > 0.0
    assert metrics.recall > 0.0
    assert metrics.f1 > 0.0
    assert metrics.coverage > 0.0
    assert metrics.true_positive > 0
    assert "libkernel" in metrics.per_library


def test_elf_parser_invalid_header():
    """Verify ELF parser properly rejects invalid headers."""
    with pytest.raises(ELFError):
        parse_elf_imports(b"not an elf binary data")

    with pytest.raises(ELFError):
        parse_elf_imports(b"\x7fELF\x01\x01")  # Not ELF64 (class 1 is 32-bit)


def test_missing_module_libscxml_resolution():
    """Verify resolver identifies missing system libraries (issue #2591 Road of Death)."""
    resolver = ImportResolver()
    imports = [
        ELFImport(name="sceXmlInit", nid=0, library="", address=0),
        ELFImport(name="sceXmlParse", nid=0, library="", address=0),
    ]
    resolved = resolver.resolve_imports(imports)
    assert len(resolved) == 2
    for r in resolved:
        assert r.status == "missing-module"
        assert r.library == "libSceXml"


def test_graphics_driver_module_exports():
    """Verify graphics driver modules export expected functions."""
    db = build_export_db()
    modules = {m.module: m for m in db}
    assert "libSceVideoOut" in modules
    assert "libSceAgcDriver" in modules

    video_out = modules["libSceVideoOut"]
    assert "sceVideoOutGetResolutionStatus" in video_out.symbols
    assert "sceVideoOutSubmitFlip" in video_out.symbols
    assert "sceVideoOutOpen" in video_out.symbols

    agc = modules["libSceAgcDriver"]
    assert "sceAgcDriverGetTFRing" in agc.symbols
    assert "sceAgcDriverSubmit" in agc.symbols
    assert "sceAgcDriverTrackStorageImage" in agc.symbols


def test_adversarial_generator_graphics_boundary_cases():
    """Verify adversarial generator synthesizes graphics boundary imports."""
    gen = AdversarialGenerator()
    agc_cases = gen.generate_cases(category="agc_driver_boundary", count=10)
    assert len(agc_cases) > 0
    symbols = {c.symbol for c in agc_cases}
    assert "sceAgcDriverGetTFRing" in symbols
    assert "sceAgcDriverGetTFRing_v2" in symbols
    assert any(c.mutation_type == "near_miss" for c in agc_cases)

    video_cases = gen.generate_cases(category="video_out_boundary", count=10)
    assert len(video_cases) > 0
    video_symbols = {c.symbol for c in video_cases}
    assert "sceVideoOutGetResolutionStatus" in video_symbols
    assert "sceVideoOutGetResolutionStatus_unsupported" in video_symbols


def test_adversarial_stress_test_stability():
    """Verify stress test reports stability scores against host boundaries."""
    resolver = ImportResolver()
    report = run_stress_test(resolver)
    assert report.total_cases > 0
    assert report.passed_cases > 0
    assert report.stability_score >= 90.0
    assert report.false_positive_rate == 0.0
    assert "agc_driver_boundary" in report.category_scores
    assert "video_out_boundary" in report.category_scores
    assert report.category_scores["agc_driver_boundary"]["score"] == 100.0
    assert report.category_scores["video_out_boundary"]["score"] == 100.0


def test_rdna2_ancillary_layout_structure():
    """Verify RDNA2 ancillary bitfield specification matches PR #1179 / issue #2548."""
    from backend.services.shader_analyzer import RDNA2_ANCILLARY_LAYOUT
    layout_map = {b.name: b for b in RDNA2_ANCILLARY_LAYOUT}
    assert "render_target_index" in layout_map
    assert "sample_index" in layout_map
    assert "prim_type" in layout_map

    rt = layout_map["render_target_index"]
    assert rt.offset == 16
    assert rt.length == 11
    assert rt.modeled is True
    assert rt.source_builtin == "Layer"

    sample = layout_map["sample_index"]
    assert sample.offset == 8
    assert sample.length == 4
    assert sample.modeled is True
    assert sample.source_builtin == "SampleId"

    prim = layout_map["prim_type"]
    assert prim.offset == 0
    assert prim.length == 2
    assert prim.modeled is False


def test_rdna2_bitfield_extraction_and_rebuild():
    """Verify bitfield decoding and PR #1179 word reconstruction."""
    from backend.services.shader_analyzer import RDNA2ShaderAnalyzer
    analyzer = RDNA2ShaderAnalyzer()

    # SampleId=3, Layer=7 -> (3 << 8) | (7 << 16) = 0x00070300
    rebuilt = analyzer.rebuild_ancillary_word(sample_id=3, layer=7)
    assert rebuilt == 0x00070300

    decoded = analyzer.decode_word(rebuilt)
    assert decoded["sample_index"]["value"] == 3
    assert decoded["render_target_index"]["value"] == 7
    assert decoded["sample_index"]["modeled"] is True
    assert decoded["render_target_index"]["modeled"] is True


def test_shader_recompiler_rebuildable_shader():
    """Verify shader extracting only valid bitfields without register reuse is rebuildable."""
    from backend.services.shader_analyzer import RDNA2ShaderAnalyzer, IRInstruction
    analyzer = RDNA2ShaderAnalyzer()
    instructions = [
        IRInstruction(0, "BitFieldUExtract", "v0", ["v4"], bit_offset=16, bit_length=11),
        IRInstruction(1, "BitFieldUExtract", "v1", ["v4"], bit_offset=8, bit_length=4),
        IRInstruction(2, "v_mov_b32", "v2", ["v0"]),
    ]
    report = analyzer.analyze_ir_stream("0x1000", "PPSA00001", instructions)
    assert report.status == "rebuildable"
    assert report.rebuildable_pr1179 is True
    assert "render_target_index" in report.extracted_fields
    assert "sample_index" in report.extracted_fields
    assert report.register_reused is False
    assert report.rejection_reason is None


def test_shader_recompiler_unsupported_live_use_detection():
    """Verify UE4 register reuse triggers unsupported live use rejection (issue #2548)."""
    from backend.services.shader_analyzer import RDNA2ShaderAnalyzer, IRInstruction
    analyzer = RDNA2ShaderAnalyzer()
    instructions = [
        IRInstruction(0, "BitFieldUExtract", "vN", ["v4"], bit_offset=16, bit_length=11),
        IRInstruction(1, "SelectU32", "v4", ["v4", "SelectU32 ? ?"], condition="IEqual32(HelperInvocation, 0)"),
        IRInstruction(2, "Phi", "v4_phi", ["v4"]),
        IRInstruction(3, "BitCastF32U32", "f_val", ["v4_phi"]),
        IRInstruction(4, "PackFloat2x16Rtz", "packed_attr", ["f_val"]),
        IRInstruction(5, "SetAttribute", None, ["packed_attr"]),
    ]
    report = analyzer.analyze_ir_stream("0x200e370000", "PPSA02100", instructions)
    assert report.status == "rejected_unsupported_live_use"
    assert report.rebuildable_pr1179 is False
    assert report.register_reused is True
    assert "SelectU32" in report.live_use_chain
    assert "SetAttribute" in report.live_use_chain
    assert report.rejection_reason is not None
    assert "unsupported live use" in report.rejection_reason


def test_stray_catalog_batch_shaders():
    """Verify Stray (PPSA02100) catalog contains 26 deferred shaders from issue #2548."""
    from backend.services.shader_analyzer import RDNA2ShaderAnalyzer
    analyzer = RDNA2ShaderAnalyzer()
    shaders = analyzer.get_stray_catalog_shaders()
    assert len(shaders) == 26
    for s in shaders:
        assert s.title_id == "PPSA02100"
        assert s.status == "rejected_unsupported_live_use"
        assert s.rebuildable_pr1179 is False
        assert s.register_reused is True
        assert "render_target_index" in s.extracted_fields


def test_structurizer_issue_2642_budget_exhaustion():
    """Verify AnyPS5 issue #2642 graph causes synthetic merge split budget exhaustion."""
    from backend.services.structurizer import CFGStructurizerAnalyzer
    analyzer = CFGStructurizerAnalyzer()
    graph = [[1], [2, 4], [3, 4], [4, 5], [1, 6], [1], []]
    report = analyzer.analyze_cfg("issue-2642-repro", graph, 28)
    assert report.exceeded_budget is True
    assert report.matches_issue_2642 is True
    assert report.original_blocks == 7
    assert report.split_budget == 28
    assert report.current_blocks >= 28
    assert len(report.multi_latch_loops) == 1
    assert report.multi_latch_loops[0]["header"] == 1
    assert sorted(report.multi_latch_loops[0]["latches"]) == [4, 5]
    assert len(report.selection_conflicts) >= 1
    conflict = report.selection_conflicts[0]
    assert conflict["merge_block"] == 4
    assert conflict["shares_latch_edge"] is True
    assert report.recommendation is not None


def test_structurizer_clean_baseline():
    """Verify a clean single-latch, unshared merge CFG passes structurizer budget."""
    from backend.services.structurizer import CFGStructurizerAnalyzer
    analyzer = CFGStructurizerAnalyzer()
    graph = [[1], [2, 3], [4], [4], [1, 5], []]
    report = analyzer.analyze_cfg("clean-baseline", graph)
    assert report.exceeded_budget is False
    assert report.matches_issue_2642 is False
    assert len(report.selection_conflicts) == 0
    assert report.status == "clean"


def test_storage_writeback_silksong_conflict_detection():
    """Verify AnyPS5 issue #865 Silksong SDF atlas writeback drops GPU results under 64K block tracking."""
    from backend.services.storage_writeback import StorageWritebackAnalyzer
    analyzer = StorageWritebackAnalyzer()
    report = analyzer.analyze()
    assert report.title_id == "PPSA12544"
    assert report.block_policy_corrupted is True
    assert len(report.block_policy_dropped_units) >= 2
    assert "OPTIONS_O" in report.corrupted_glyphs
    assert "GAME_MARK" in report.corrupted_glyphs
    assert report.warning_logged is not None
    assert "0x25e042000" in report.warning_logged
    assert report.status == "conflict_detected"
    assert report.edge_blocks_count == 2


def test_storage_writeback_4k_page_granularity_preservation():
    """Verify 4 KiB page granularity eliminates false-positive StoredOver drops for Silksong."""
    from backend.services.storage_writeback import StorageWritebackAnalyzer
    analyzer = StorageWritebackAnalyzer()
    report = analyzer.analyze()
    assert report.page_policy_corrupted is False
    assert len(report.page_policy_dropped_units) == 0
    assert report.eager_writeback_corrupted is False


def test_storage_writeback_aligned_baseline():
    """Verify aligned 64 KiB texture without adjacent sharing allocations is clean under all policies."""
    from backend.services.storage_writeback import StorageWritebackAnalyzer, StorageWritebackConfig
    analyzer = StorageWritebackAnalyzer()
    cfg = StorageWritebackConfig(
        title_id="PPSA00000",
        title_name="Aligned Baseline",
        texture_address=0x25E040000,
        texture_size=0x40000,
    )
    report = analyzer.analyze(config=cfg, cpu_writes=[])
    assert report.block_policy_corrupted is False
    assert report.page_policy_corrupted is False
    assert report.edge_blocks_count == 0
    assert report.status == "clean"





