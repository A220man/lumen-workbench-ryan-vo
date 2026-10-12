import pytest
from backend.core.elf_parser import ELFImport, ELFError, parse_elf_imports
from backend.core.nid import nid_of
from backend.services.import_resolver import ImportResolver
from backend.services.export_db import build_export_db
from backend.services.evaluator import run_evaluation, labeled_dataset
from backend.services.adversarial import AdversarialGenerator, run_stress_test
from backend.services.shader_analyzer import RDNA2ShaderAnalyzer, IRInstruction, RDNA2_ANCILLARY_LAYOUT
from backend.services.structurizer import CFGStructurizerAnalyzer
from backend.services.storage_writeback import StorageWritebackAnalyzer, StorageWritebackConfig


def test_nid_hashing_deterministic():
    """Verify NID hashing is deterministic across executions."""
    assert nid_of("sysctl") == nid_of("sysctl")
    assert nid_of("pthread_set_name_np") == nid_of("pthread_set_name_np")
    assert 0 <= nid_of("test_symbol") <= 0xFFFFFFFF


def test_export_db_structure():
    """Verify host export surface contains required modules and symbols."""
    modules = build_export_db()
    kernel = next(m for m in modules if m.module == "libkernel")
    assert "sysctl" in kernel.symbols
    assert "pthread_set_name_np" in kernel.symbols
    assert kernel.present is True

    xml_mod = next(m for m in modules if m.module == "libSceXml")
    assert xml_mod.present is False
    assert "sceXmlInit" in xml_mod.symbols


def test_import_resolver_known_symbol():
    """Verify ImportResolver resolves symbols found in export database."""
    resolver = ImportResolver()
    assert resolver.resolve_name("pthread_set_name_np") == "libkernel"
    assert resolver.resolve_name("sceVideoOutGetResolutionStatus") == "libSceVideoOut"


def test_import_resolver_unknown_symbol():
    """Verify unknown symbol returns None."""
    resolver = ImportResolver()
    assert resolver.resolve_name("unknown_nonexistent_symbol_xyz") is None


def test_resolver_batch_imports():
    """Verify resolution of a batch of ELF imports."""
    resolver = ImportResolver()
    imports = [
        ELFImport(name="sysctl", nid=nid_of("sysctl"), library="libkernel", address=0x1000),
        ELFImport(name="missing_symbol_xyz", nid=0xDEADBEEF, library="libkernel", address=0x2000),
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
    assert metrics.precision >= 0.0
    assert metrics.recall >= 0.0
    assert metrics.f1 >= 0.0
    assert "libkernel" in metrics.per_library
    assert metrics.per_library["libkernel"]["tp"] > 0


def test_elf_parser_invalid_header():
    """Verify ELF parser properly rejects invalid headers."""
    with pytest.raises(ELFError):
        parse_elf_imports(b"not an elf")
    with pytest.raises(ELFError):
        parse_elf_imports(b"\x7fELF\x01\x01")  # Not ELF64 (class 1 is 32-bit)


def test_missing_module_libscxml_resolution():
    """Verify resolver identifies missing system libraries (issue #2591 Road of Death)."""
    resolver = ImportResolver()
    imports = [ELFImport(name="sceXmlInit", nid=nid_of("sceXmlInit"), library="", address=0x1000)]
    resolved = resolver.resolve_imports(imports)
    assert len(resolved) == 1
    r = resolved[0]
    assert r.status == "missing-module"
    assert r.library == "libSceXml"


def test_graphics_driver_module_exports():
    """Verify graphics driver modules export expected functions."""
    modules = build_export_db()
    agc = next(m for m in modules if m.module == "libSceAgcDriver")
    assert agc.present is True
    assert "sceAgcDriverGetTFRing" in agc.symbols
    assert "sceAgcDriverSubmit" in agc.symbols
    assert "sceAgcDriverTrackStorageImage" in agc.symbols


def test_adversarial_generator_graphics_boundary_cases():
    """Verify adversarial generator synthesizes graphics boundary imports."""
    gen = AdversarialGenerator()
    cases = gen.generate_cases(category="agc_driver_boundary", count=10)
    assert len(cases) >= 3
    symbols = {c.symbol for c in cases}
    assert "sceAgcDriverGetTFRing" in symbols
    assert "sceAgcDriverSubmit" in symbols


def test_adversarial_stress_test_stability():
    """Verify stress test reports stability scores against host boundaries."""
    resolver = ImportResolver()
    report = run_stress_test(resolver)
    assert report.total_cases >= 20
    assert 0.0 <= report.stability_score <= 100.0
    assert 0.0 <= report.false_positive_rate <= 1.0
    assert "agc_driver_boundary" in report.category_scores
    assert "video_out_boundary" in report.category_scores
    assert report.category_scores["agc_driver_boundary"]["score"] == 100.0
    assert report.category_scores["video_out_boundary"]["score"] == 100.0


def test_rdna2_ancillary_layout_structure():
    """Verify RDNA2 ancillary bitfield specification matches PR #1179 / issue #2548."""
    assert len(RDNA2_ANCILLARY_LAYOUT) >= 5
    rt = next(b for b in RDNA2_ANCILLARY_LAYOUT if b.name == "render_target_index")
    assert rt.offset == 16
    assert rt.length == 11
    assert rt.modeled is True
    assert rt.source_builtin == "Layer"
    si = next(b for b in RDNA2_ANCILLARY_LAYOUT if b.name == "sample_index")
    assert si.offset == 8
    assert si.length == 4
    assert si.modeled is True
    assert si.source_builtin == "SampleId"
    prim = next(b for b in RDNA2_ANCILLARY_LAYOUT if b.name == "prim_type")
    assert prim.modeled is False


def test_rdna2_bitfield_extraction_and_rebuild():
    """Verify bitfield decoding and PR #1179 word reconstruction."""
    analyzer = RDNA2ShaderAnalyzer()
    word = 0x00050200  # sample_id=2 (bits 8-11), layer=5 (bits 16-26)
    decoded = analyzer.decode_word(word)
    assert decoded["sample_index"]["value"] == 2
    assert decoded["render_target_index"]["value"] == 5
    assert decoded["sample_index"]["modeled"] is True
    assert decoded["render_target_index"]["modeled"] is True
    rebuilt = analyzer.rebuild_ancillary_word(2, 5)
    assert rebuilt == (word & 0x00050200)


def test_shader_recompiler_rebuildable_shader():
    """Verify shader extracting only valid bitfields without register reuse is rebuildable."""
    analyzer = RDNA2ShaderAnalyzer()
    instructions = [
        IRInstruction(0, "BitFieldUExtract", "v0", ["v4"], 16, 11),
        IRInstruction(1, "BitFieldUExtract", "v1", ["v4"], 8, 4),
    ]
    report = analyzer.analyze_ir_stream("0x1000", "PPSA00001", instructions, "v4")
    assert report.status == "rebuildable"
    assert report.rejection_reason is None
    assert "render_target_index" in report.extracted_fields
    assert "sample_index" in report.extracted_fields


def test_shader_recompiler_unsupported_live_use_detection():
    """Verify UE4 register reuse triggers unsupported live use rejection (issue #2548)."""
    analyzer = RDNA2ShaderAnalyzer()
    instructions = [
        IRInstruction(0, "BitFieldUExtract", "vN", ["v4"], 16, 11),
        IRInstruction(1, "SelectU32", "v4", ["v4", "v4"], condition="IEqual32(HelperInvocation, 0)"),
        IRInstruction(2, "Phi", "v4_phi", ["v4"]),
        IRInstruction(3, "BitCastF32U32", "f_val", ["v4_phi"]),
        IRInstruction(4, "PackFloat2x16Rtz", "packed_attr", ["f_val"]),
        IRInstruction(5, "SetAttribute", None, ["packed_attr"]),
    ]
    report = analyzer.analyze_ir_stream("0x200e370000", "PPSA02100", instructions, "v4")
    assert report.status == "rejected_unsupported_live_use"
    assert "unsupported live use" in report.rejection_reason
    assert "SelectU32" in report.live_use_chain


def test_stray_catalog_batch_shaders():
    """Verify Stray (PPSA02100) catalog contains 26 deferred shaders from issue #2548."""
    analyzer = RDNA2ShaderAnalyzer()
    shaders = analyzer.get_stray_catalog_shaders()
    assert len(shaders) == 26
    for s in shaders:
        assert s.status == "rejected_unsupported_live_use"
        assert "render_target_index" in s.extracted_fields


def test_structurizer_issue_2642_budget_exhaustion():
    """Verify AnyPS5 issue #2642 graph causes synthetic merge split budget exhaustion."""
    analyzer = CFGStructurizerAnalyzer()
    graph = analyzer.get_issue_2642_graph()
    report = analyzer.analyze_cfg("issue-2642-repro", graph)
    assert report.exceeded_budget is True
    assert report.matches_issue_2642 is True
    assert report.original_blocks == 7
    assert report.current_blocks > report.split_budget
    assert len(report.multi_latch_loops) == 1
    assert report.multi_latch_loops[0]["is_multi_latch"] is True
    assert report.recommendation is not None


def test_structurizer_clean_baseline():
    """Verify a clean single-latch, unshared merge CFG passes structurizer budget."""
    analyzer = CFGStructurizerAnalyzer()
    graph = analyzer.get_clean_baseline_graph()
    report = analyzer.analyze_cfg("clean-baseline", graph)
    assert report.exceeded_budget is False
    assert report.matches_issue_2642 is False
    assert report.status == "clean"


def test_storage_writeback_silksong_conflict_detection():
    """Verify AnyPS5 issue #865 Silksong SDF atlas writeback drops GPU results under 64K block tracking."""
    analyzer = StorageWritebackAnalyzer()
    config, writes = analyzer.get_silksong_preset()
    report = analyzer.analyze(config, writes)
    assert report.status == "conflict_detected"
    assert report.block_policy_corrupted is True
    assert len(report.block_policy_dropped_units) > 0
    assert report.edge_blocks_count == 2


def test_storage_writeback_4k_page_granularity_preservation():
    """Verify 4 KiB page granularity eliminates false-positive StoredOver drops for Silksong."""
    analyzer = StorageWritebackAnalyzer()
    config, writes = analyzer.get_silksong_preset()
    report = analyzer.analyze(config, writes)
    assert report.page_policy_corrupted is False
    assert report.eager_writeback_corrupted is False


def test_storage_writeback_aligned_baseline():
    """Verify aligned 64 KiB texture without adjacent sharing allocations is clean under all policies."""
    analyzer = StorageWritebackAnalyzer()
    config = StorageWritebackConfig(texture_address=0x25E000000, texture_size=0x40000)
    report = analyzer.analyze(config)
    assert report.status == "clean"
    assert report.block_policy_corrupted is False
    assert report.page_policy_corrupted is False
    assert report.eager_writeback_corrupted is False


def test_adversarial_opus_decoder_boundary_cases():
    """Verify adversarial generator synthesizes Opus decoder boundary imports (issue #1578)."""
    gen = AdversarialGenerator()
    cases = gen.generate_cases(category="opus_decoder_boundary", count=10)
    assert len(cases) >= 3
    symbols = {c.symbol for c in cases}
    assert "sceOpusDecoderCreate" in symbols
    assert "sceOpusDecoderDecodeFrame" in symbols


def test_adversarial_opus_decoder_missing_module_probes():
    """Verify adversarial generator includes missing-module probes for libSceOpusDec and libSceOpusCeltDec."""
    gen = AdversarialGenerator()
    cases = gen.generate_cases(category="missing_module_probe", count=20)
    opus_cases = [c for c in cases if c.target_library in ("libSceOpusDec", "libSceOpusCeltDec")]
    assert len(opus_cases) >= 12


def test_first_light_stop_sequence():
    """Verify FirstLightDiagnostic models the 13-stop startup sequence from issue #2523."""
    from backend.services.first_light_diagnostic import FirstLightDiagnostic, get_first_light_diagnostic

    diag = get_first_light_diagnostic()
    stops = diag.get_all_stops()

    assert len(stops) == 13
    assert stops[0].index == 1
    assert stops[12].index == 13

    # Verify key stops have expected error text
    assert "sceSslGetCaList" in stops[0].error_text
    assert "sceSharePlayInitialize" in stops[1].error_text
    assert "SPIR-V validation" in stops[2].error_text
    assert "pixel format 0xc001000622000000" in stops[3].error_text
    assert "int 0x42 trap" in stops[4].error_text
    assert "all threads asleep" in stops[5].error_text
    assert "heap capacity exceeded" in stops[6].error_text
    assert "VOP3 source modifiers" in stops[7].error_text
    assert "CFG shared merge splitting exceeded budget" in stops[8].error_text
    assert "GetImageResource dword 0" in stops[9].error_text
    assert "unsupported registered shader type" in stops[10].error_text
    assert "GetSamplerResource dword 3" in stops[11].error_text
    assert "static bindless image capacity exceeded" in stops[12].error_text

    # Verify shader cache misses for stops that have them
    assert stops[2].shader_cache_misses == 61
    assert stops[3].shader_cache_misses == 84
    assert stops[4].shader_cache_misses == 84
    assert stops[5].shader_cache_misses == 141
    assert stops[6].shader_cache_misses == 168
    assert stops[7].shader_cache_misses == 230
    assert stops[8].shader_cache_misses == 247
    assert stops[10].shader_cache_misses == 654
    assert stops[11].shader_cache_misses == 725
    assert stops[12].shader_cache_misses == 733

    # Verify PR references
    assert any(p.number == 2830 for p in stops[0].prs)
    assert any(p.number == 2946 for p in stops[1].prs)
    assert any(p.number == 1964 for p in stops[2].prs)
    assert any(p.number == 3134 for p in stops[3].prs)
    assert any(p.number == 2455 for p in stops[5].prs)
    assert any(p.number == 2282 for p in stops[6].prs)
    assert any(p.number == 2463 for p in stops[7].prs)
    assert any(p.number == 2471 for p in stops[8].prs)
    assert any(p.number == 1184 for p in stops[9].prs)
    assert any(p.number == 1893 for p in stops[10].prs)
    assert any(p.number == 1184 for p in stops[11].prs)
    assert len(stops[12].prs) == 0  # No PR for stop 13 yet

    # Verify verification status
    assert stops[0].verified is True
    assert stops[12].verified is False  # Stop 13 not verified yet


def test_first_light_pr_mapping():
    """Verify analyze_sequence correctly maps applied PRs to stop progression."""
    from backend.services.first_light_diagnostic import get_first_light_diagnostic

    diag = get_first_light_diagnostic()

    # No PRs applied - should be at stop 1
    report = diag.analyze_sequence([])
    assert report.current_stop == 1
    assert report.passed_stops == 0
    assert report.failed_stops == 12  # All verified stops failed
    assert report.status == "blocked"
    assert report.regression_detected is True

    # Apply stops 1-3 PRs
    report = diag.analyze_sequence([2830, 2831, 2946, 1964])
    assert report.current_stop == 4
    assert report.passed_stops == 3
    assert report.failed_stops == 9
    assert report.status == "blocked"

    # Apply all main repo merged PRs through stop 12 (stop 5 only has SleglJan fork PR)
    all_prs = [2830, 2831, 2946, 1964, 3134, 2455, 2282, 2463, 2471, 1184, 2347, 1893]
    report = diag.analyze_sequence(all_prs)
    # Stop 5 requires SleglJan fork PR (not in main repo), so 11 passed, 1 failed
    assert report.passed_stops == 11
    assert report.failed_stops == 1
    assert report.current_stop == 5
    assert report.status == "blocked"
    assert report.regression_detected is True


def test_first_light_presets():
    """Verify preset configurations cover key progression points."""
    from backend.services.first_light_diagnostic import get_first_light_diagnostic

    diag = get_first_light_diagnostic()
    presets = diag.get_presets()

    assert len(presets) >= 6
    preset_names = {p["name"] for p in presets}
    assert "main (no fixes)" in preset_names
    assert "stops 1-3 fixed" in preset_names
    assert "stops 1-6 fixed" in preset_names
    assert "stops 1-9 fixed" in preset_names
    assert "stops 1-12 fixed" in preset_names

    # Verify main preset has no PRs
    main_preset = next(p for p in presets if p["name"] == "main (no fixes)")
    assert main_preset["applied_prs"] == []

    # Verify all-merged preset has all PRs
    all_merged = next(p for p in presets if p["name"] == "all merged PRs")
    assert 2830 in all_merged["applied_prs"]
    assert 1893 in all_merged["applied_prs"]