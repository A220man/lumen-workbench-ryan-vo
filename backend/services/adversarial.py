"""Adversarial ELF import generator and stress-testing engine.

Generates synthetic boundary imports, graphics driver mutations,
missing-module probes, and malformed inputs to stress-test the resolver.
Computes stress-test stability scores and tracks boundary failure rates.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
from ..core.elf_parser import ELFImport
from ..core.nid import nid_of
from .export_db import build_export_db
from .import_resolver import ImportResolver


@dataclass(frozen=True)
class AdversarialTestCase:
    symbol: str; nid: int; target_library: Optional[str]; category: str; mutation_type: str; expected_status: str


@dataclass
class StressTestReport:
    total_cases: int; passed_cases: int; failed_cases: int; stability_score: float
    false_positive_rate: float; category_scores: Dict[str, Dict[str, Any]]; vulnerabilities: List[str]


def _load_adversarial_specs() -> List[Dict[str, Any]]:
    """Load adversarial test case specifications from JSON data file."""
    data_path = Path(__file__).parent.parent / "data" / "adversarial_specs.json"
    with data_path.open() as f:
        data = json.load(f)
    return data["specs"]


ADVERSARIAL_SPECS = _load_adversarial_specs()


class AdversarialGenerator:
    """Generates synthetic adversarial test cases to probe import resolver limits."""

    def __init__(self) -> None:
        self.export_db = build_export_db()

    def generate_cases(self, category: Optional[str] = None, count: int = 20) -> List[AdversarialTestCase]:
        cases = [AdversarialTestCase(s["symbol"], nid_of(s["symbol"]) if s["symbol"] else 0, s["target_library"], s["category"], s["mutation_type"], s["expected_status"]) for s in ADVERSARIAL_SPECS]
        if category and category != "all":
            filtered = [c for c in cases if c.category == category or category in c.category]
            if filtered:
                return filtered[:count]
        return cases[:count]


def run_stress_test(resolver: ImportResolver, custom_cases: Optional[List[AdversarialTestCase]] = None) -> StressTestReport:
    cases = custom_cases if custom_cases is not None else AdversarialGenerator().generate_cases(count=50)
    passed, failed, fp, negs, cats, vulns = 0, 0, 0, 0, {}, []
    for c in cases:
        cats.setdefault(c.category, {"total": 0, "passed": 0, "failed": 0})
        cats[c.category]["total"] += 1
        raw = [ELFImport(name=c.symbol, nid=c.nid, library="", address=0)]
        res_list = resolver.resolve_imports(raw)
        act = res_list[0].status if res_list else "unresolved"
        is_neg = c.expected_status in ("unresolved", "missing-module")
        if is_neg:
            negs += 1
        if act == c.expected_status:
            passed += 1
            cats[c.category]["passed"] += 1
        else:
            failed += 1
            cats[c.category]["failed"] += 1
            vulns.append(f"Symbol '{c.symbol}' expected '{c.expected_status}', got '{act}'")
            if c.expected_status == "unresolved" and act == "resolved":
                fp += 1

    tot = len(cases) or 1
    for k, v in cats.items():
        v["score"] = round((v["passed"] / v["total"]) * 100.0, 1) if v["total"] else 100.0
    fp_rate = (fp / negs) if negs > 0 else 0.0
    return StressTestReport(len(cases), passed, failed, round(passed / tot * 100.0, 2), round(fp_rate, 4), cats, vulns)