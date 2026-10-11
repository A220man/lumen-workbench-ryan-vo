"""Adversarial ELF import generator and stress-testing engine.

Generates synthetic boundary imports, graphics driver mutations,
missing-module probes, and malformed inputs to stress-test the resolver.
Computes stress-test stability scores and tracks boundary failure rates.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..core.elf_parser import ELFImport
from ..core.nid import nid_of
from .export_db import build_export_db
from .import_resolver import ImportResolver, ResolvedImport


@dataclass(frozen=True)
class AdversarialTestCase:
    symbol: str
    nid: int
    target_library: Optional[str]
    category: str
    mutation_type: str
    expected_status: str  # "resolved" | "unresolved" | "missing-module"


@dataclass
class StressTestReport:
    total_cases: int
    passed_cases: int
    failed_cases: int
    stability_score: float  # 0.0 to 100.0
    false_positive_rate: float  # 0.0 to 1.0
    category_scores: Dict[str, Dict[str, Any]]
    vulnerabilities: List[str]


class AdversarialGenerator:
    """Generates synthetic adversarial test cases to probe import resolver limits."""

    def __init__(self) -> None:
        self.export_db = build_export_db()

    def generate_cases(
        self, category: Optional[str] = None, count: int = 20
    ) -> List[AdversarialTestCase]:
        """Generate adversarial test cases filtered by category or across all categories."""
        specs = [
            ("sceAgcDriverGetTFRing", "libSceAgcDriver", "agc_driver_boundary", "valid_boundary", "resolved"),
            ("sceAgcDriverSubmit", "libSceAgcDriver", "agc_driver_boundary", "valid_boundary", "resolved"),
            ("sceAgcDriverTrackStorageImage", "libSceAgcDriver", "agc_driver_boundary", "valid_boundary", "resolved"),
            ("sceAgcDriverGetTFRing_v2", None, "agc_driver_boundary", "near_miss", "unresolved"),
            ("sceAgcDriverRegisterShaderType99", None, "agc_driver_boundary", "invalid_shader_type", "unresolved"),
            ("sceAgcDriverStorageTextureEagerWriteback", None, "agc_driver_boundary", "synthetic_boundary", "unresolved"),
            ("sceVideoOutGetResolutionStatus", "libSceVideoOut", "video_out_boundary", "valid_boundary", "resolved"),
            ("sceVideoOutOpen", "libSceVideoOut", "video_out_boundary", "valid_boundary", "resolved"),
            ("sceVideoOutSubmitFlip", "libSceVideoOut", "video_out_boundary", "valid_boundary", "resolved"),
            ("sceVideoOutGetResolutionStatus_unsupported", None, "video_out_boundary", "near_miss", "unresolved"),
            ("sceVideoOutPixelFormatC001000622000000", None, "video_out_boundary", "unsupported_format", "unresolved"),
            ("sceVideoOutSubmitFlipAsync_nonexistent", None, "video_out_boundary", "synthetic_boundary", "unresolved"),
            ("sceXmlInit", "libSceXml", "missing_module_probe", "missing_probe", "missing-module"),
            ("sceXmlParse", "libSceXml", "missing_module_probe", "missing_probe", "missing-module"),
            ("CreateEx", "libSceOpusDec", "missing_module_probe", "missing_probe", "missing-module"),
            ("sceUnknownMissingModule_func", None, "missing_module_probe", "unknown_probe", "unresolved"),
            ("", None, "malformed_symbol", "empty_symbol", "unresolved"),
            ("!@#$%^&*()_+", None, "malformed_symbol", "special_characters", "unresolved"),
            ("sysctl_boundary_overflow_" + ("x" * 64), None, "malformed_symbol", "oversized_identifier", "unresolved"),
        ]
        all_cases = [
            AdversarialTestCase(
                symbol=sym,
                nid=nid_of(sym) if sym else 0,
                target_library=lib,
                category=cat,
                mutation_type=mut,
                expected_status=exp,
            )
            for sym, lib, cat, mut, exp in specs
        ]

        # Filter by category if requested
        if category and category != "all":
            filtered = [c for c in all_cases if c.category == category or category in c.category]
            if filtered:
                return filtered[:count]

        return all_cases[:count]


def run_stress_test(
    resolver: ImportResolver,
    custom_cases: Optional[List[AdversarialTestCase]] = None,
) -> StressTestReport:
    """Stress-test the resolver against adversarial boundary test cases.

    Returns the stability score, false positive rate, category breakdown,
    and any detected boundary vulnerabilities.
    """
    generator = AdversarialGenerator()
    cases = custom_cases if custom_cases is not None else generator.generate_cases(count=50)

    total = len(cases)
    passed = 0
    failed = 0
    false_positives = 0
    total_negatives = 0
    vulnerabilities: List[str] = []
    category_map: Dict[str, Dict[str, Any]] = {}

    for case in cases:
        cat = category_map.setdefault(
            case.category, {"total": 0, "passed": 0, "failed": 0, "score": 100.0}
        )
        cat["total"] += 1

        raw_imports = [ELFImport(name=case.symbol, nid=case.nid, library="", address=0)]
        resolved_list = resolver.resolve_imports(raw_imports)
        actual_status = resolved_list[0].status if resolved_list else "unresolved"

        is_negative = case.expected_status in ("unresolved", "missing-module")
        if is_negative:
            total_negatives += 1

        if actual_status == case.expected_status:
            passed += 1
            cat["passed"] += 1
        else:
            failed += 1
            cat["failed"] += 1
            vulnerabilities.append(
                f"Symbol '{case.symbol}' expected '{case.expected_status}', got '{actual_status}'"
            )
            if case.expected_status == "unresolved" and actual_status == "resolved":
                false_positives += 1

    stability_score = (passed / total * 100.0) if total > 0 else 100.0
    fp_rate = (false_positives / total_negatives) if total_negatives > 0 else 0.0

    for cat_data in category_map.values():
        if cat_data["total"] > 0:
            cat_data["score"] = round((cat_data["passed"] / cat_data["total"]) * 100.0, 1)

    return StressTestReport(
        total_cases=total,
        passed_cases=passed,
        failed_cases=failed,
        stability_score=round(stability_score, 2),
        false_positive_rate=round(fp_rate, 4),
        category_scores=category_map,
        vulnerabilities=vulnerabilities,
    )
