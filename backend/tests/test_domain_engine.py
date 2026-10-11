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


