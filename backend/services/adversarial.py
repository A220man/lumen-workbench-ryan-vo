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
        all_cases: List[AdversarialTestCase] = []

        # 1. libSceAgcDriver boundary cases
        agc_cases = [
            AdversarialTestCase(
                symbol="sceAgcDriverGetTFRing",
                nid=nid_of("sceAgcDriverGetTFRing"),
                target_library="libSceAgcDriver",
                category="agc_driver_boundary",
                mutation_type="valid_boundary",
                expected_status="resolved",
            ),
            AdversarialTestCase(
                symbol="sceAgcDriverSubmit",
                nid=nid_of("sceAgcDriverSubmit"),
                target_library="libSceAgcDriver",
                category="agc_driver_boundary",
                mutation_type="valid_boundary",
                expected_status="resolved",
            ),
            AdversarialTestCase(
                symbol="sceAgcDriverTrackStorageImage",
                nid=nid_of("sceAgcDriverTrackStorageImage"),
                target_library="libSceAgcDriver",
                category="agc_driver_boundary",
                mutation_type="valid_boundary",
                expected_status="resolved",
            ),
            AdversarialTestCase(
                symbol="sceAgcDriverGetTFRing_v2",
                nid=nid_of("sceAgcDriverGetTFRing_v2"),
                target_library=None,
                category="agc_driver_boundary",
                mutation_type="near_miss",
                expected_status="unresolved",
            ),
            AdversarialTestCase(
                symbol="sceAgcDriverRegisterShaderType99",
                nid=nid_of("sceAgcDriverRegisterShaderType99"),
                target_library=None,
                category="agc_driver_boundary",
                mutation_type="invalid_shader_type",
                expected_status="unresolved",
            ),
            AdversarialTestCase(
                symbol="sceAgcDriverStorageTextureEagerWriteback",
                nid=nid_of("sceAgcDriverStorageTextureEagerWriteback"),
                target_library=None,
                category="agc_driver_boundary",
                mutation_type="synthetic_boundary",
                expected_status="unresolved",
            ),
        ]
        all_cases.extend(agc_cases)

        # 2. libSceVideoOut boundary cases
        video_cases = [
            AdversarialTestCase(
                symbol="sceVideoOutGetResolutionStatus",
                nid=nid_of("sceVideoOutGetResolutionStatus"),
                target_library="libSceVideoOut",
                category="video_out_boundary",
                mutation_type="valid_boundary",
                expected_status="resolved",
            ),
            AdversarialTestCase(
                symbol="sceVideoOutOpen",
                nid=nid_of("sceVideoOutOpen"),
                target_library="libSceVideoOut",
                category="video_out_boundary",
                mutation_type="valid_boundary",
                expected_status="resolved",
            ),
            AdversarialTestCase(
                symbol="sceVideoOutSubmitFlip",
                nid=nid_of("sceVideoOutSubmitFlip"),
                target_library="libSceVideoOut",
                category="video_out_boundary",
                mutation_type="valid_boundary",
                expected_status="resolved",
            ),
            AdversarialTestCase(
                symbol="sceVideoOutGetResolutionStatus_unsupported",
                nid=nid_of("sceVideoOutGetResolutionStatus_unsupported"),
                target_library=None,
                category="video_out_boundary",
                mutation_type="near_miss",
                expected_status="unresolved",
            ),
            AdversarialTestCase(
                symbol="sceVideoOutPixelFormatC001000622000000",
                nid=nid_of("sceVideoOutPixelFormatC001000622000000"),
                target_library=None,
                category="video_out_boundary",
                mutation_type="unsupported_format",
                expected_status="unresolved",
            ),
            AdversarialTestCase(
                symbol="sceVideoOutSubmitFlipAsync_nonexistent",
                nid=nid_of("sceVideoOutSubmitFlipAsync_nonexistent"),
                target_library=None,
                category="video_out_boundary",
                mutation_type="synthetic_boundary",
                expected_status="unresolved",
            ),
        ]
        all_cases.extend(video_cases)

        # 3. Missing module probe cases (e.g. libSceXml, libSceOpusDec)
        missing_cases = [
            AdversarialTestCase(
                symbol="sceXmlInit",
                nid=nid_of("sceXmlInit"),
                target_library="libSceXml",
                category="missing_module_probe",
                mutation_type="missing_probe",
                expected_status="missing-module",
            ),
            AdversarialTestCase(
                symbol="sceXmlParse",
                nid=nid_of("sceXmlParse"),
                target_library="libSceXml",
                category="missing_module_probe",
                mutation_type="missing_probe",
                expected_status="missing-module",
            ),
            AdversarialTestCase(
                symbol="CreateEx",
                nid=nid_of("CreateEx"),
                target_library="libSceOpusDec",
                category="missing_module_probe",
                mutation_type="missing_probe",
                expected_status="missing-module",
            ),
            AdversarialTestCase(
                symbol="sceUnknownMissingModule_func",
                nid=nid_of("sceUnknownMissingModule_func"),
                target_library=None,
                category="missing_module_probe",
                mutation_type="unknown_probe",
                expected_status="unresolved",
            ),
        ]
        all_cases.extend(missing_cases)

        # 4. Malformed symbol and edge cases
        edge_cases = [
            AdversarialTestCase(
                symbol="",
                nid=0,
                target_library=None,
                category="malformed_symbol",
                mutation_type="empty_symbol",
                expected_status="unresolved",
            ),
            AdversarialTestCase(
                symbol="!@#$%^&*()_+",
                nid=nid_of("!@#$%^&*()_+"),
                target_library=None,
                category="malformed_symbol",
                mutation_type="special_characters",
                expected_status="unresolved",
            ),
            AdversarialTestCase(
                symbol="sysctl_boundary_overflow_" + ("x" * 64),
                nid=nid_of("sysctl_boundary_overflow_" + ("x" * 64)),
                target_library=None,
                category="malformed_symbol",
                mutation_type="oversized_identifier",
                expected_status="unresolved",
            ),
        ]
        all_cases.extend(edge_cases)

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
