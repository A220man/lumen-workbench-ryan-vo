"""007 First Light (PPSA11386) startup sequence diagnostic.

Models the 13-stop startup sequence from AnyPS5 issue #2523, including
PR references, verification status, and regression detection for each stop.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import json


@dataclass(frozen=True)
class StopPR:
    number: int
    url: str
    commit: str
    merged: bool
    description: str


@dataclass(frozen=True)
class StartupStop:
    index: int
    description: str
    error_text: str
    shader_cache_misses: Optional[int]
    prs: List[StopPR]
    verified: bool
    notes: str = ""


@dataclass
class FirstLightReport:
    title_id: str
    title_name: str
    version: str
    stops: List[StartupStop]
    current_stop: int
    passed_stops: int
    failed_stops: int
    status: str  # "running" | "blocked" | "passed"
    regression_detected: bool
    regression_details: List[str]


def _load_stops() -> List[StartupStop]:
    """Load stop definitions from JSON data file."""
    data_path = Path(__file__).parent.parent / "data" / "first_light_stops.json"
    with data_path.open() as f:
        data = json.load(f)

    stops = []
    for s in data["stops"]:
        prs = [StopPR(**pr) for pr in s["prs"]]
        stops.append(StartupStop(
            index=s["index"],
            description=s["description"],
            error_text=s["error_text"],
            shader_cache_misses=s["shader_cache_misses"],
            prs=prs,
            verified=s["verified"],
            notes=s.get("notes", ""),
        ))
    return stops


def _load_presets() -> List[Dict[str, any]]:
    """Load preset configurations from JSON data file."""
    data_path = Path(__file__).parent.parent / "data" / "first_light_stops.json"
    with data_path.open() as f:
        data = json.load(f)
    return data["presets"]


STOP_DEFINITIONS = _load_stops()
PRESETS = _load_presets()


class FirstLightDiagnostic:
    """Diagnostic for 007 First Light (PPSA11386) startup sequence."""

    def __init__(self) -> None:
        self.stops = STOP_DEFINITIONS

    def get_all_stops(self) -> List[StartupStop]:
        """Return all defined startup stops."""
        return self.stops

    def get_stop(self, index: int) -> Optional[StartupStop]:
        """Get a specific stop by 1-based index."""
        if 1 <= index <= len(self.stops):
            return self.stops[index - 1]
        return None

    def analyze_sequence(self, applied_prs: Optional[List[int]] = None) -> FirstLightReport:
        """Analyze the startup sequence given a set of applied PR numbers."""
        applied = set(applied_prs or [])
        passed = 0
        failed = 0
        current = 1
        first_failure = None
        regression_details = []

        for stop in self.stops:
            stop_prs = {pr.number for pr in stop.prs if pr.number > 0}
            # If verified and NO PRs at all (stop_prs empty AND stop.prs empty), consider covered
            stop_covered = stop_prs.issubset(applied) if stop_prs else (stop.verified and not stop.prs)

            if stop.verified and stop_covered:
                passed += 1
                if first_failure is None:
                    current = stop.index + 1
            elif stop.verified and not stop_covered:
                failed += 1
                if first_failure is None:
                    first_failure = stop.index
                    current = stop.index
                regression_details.append(f"Stop {stop.index}: expected PRs {sorted(stop_prs)} not all applied")
            elif not stop.verified:
                # Unverified stop (stop 13+)
                if first_failure is None and current == stop.index:
                    break

        status = "passed" if failed == 0 and passed == len([s for s in self.stops if s.verified]) else (
            "blocked" if failed > 0 else "running"
        )

        return FirstLightReport(
            title_id="PPSA11386",
            title_name="007 First Light",
            version="v01.018.000",
            stops=self.stops,
            current_stop=current,
            passed_stops=passed,
            failed_stops=failed,
            status=status,
            regression_detected=len(regression_details) > 0,
            regression_details=regression_details,
        )

    def get_presets(self) -> List[Dict[str, any]]:
        """Return preset configurations for testing."""
        return PRESETS


def get_first_light_diagnostic() -> FirstLightDiagnostic:
    """Singleton accessor."""
    return FirstLightDiagnostic()