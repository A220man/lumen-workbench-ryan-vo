"""PS5 elf import resolver: parse, resolve, score, and suggest.

The ImportResolver is the core domain engine. It parses ELF import tables,
matches against the export database, computes coverage, and ranks blockers.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, FrozenSet, List, Optional

from ..core.elf_parser import ELFImport, ELFError, parse_elf_imports
from ..core.nid import nid_of
from .export_db import ModuleExport, build_export_db


@dataclass(frozen=True)
class ResolvedImport:
    name: str
    nid: int
    library: Optional[str]
    status: str  # "resolved" | "unresolved" | "missing-module"


@dataclass
class ResolutionReport:
    source_name: str
    needed_libraries: List[str]
    imports: List[ResolvedImport]
    resolved_count: int
    unresolved_count: int
    missing_module_count: int
    coverage: float  # 0.0..1.0
    score: int  # 0..100
    blockers: List[str]


class ImportResolver:
    """Deterministic resolver for PS5 elf imports against the host export db."""

    def __init__(self) -> None:
        self.modules: List[ModuleExport] = build_export_db()
        self._symbol_index: Dict[str, str] = {}
        self._absent_symbols: Dict[str, str] = {}

        for mod in self.modules:
            for sym in mod.symbols:
                if mod.present:
                    self._symbol_index[sym] = mod.module
                else:
                    self._absent_symbols[sym] = mod.module

    @lru_cache(maxsize=1024)
    def resolve_name(self, name: str) -> Optional[str]:
        """Return the library for a symbol, or None if unresolved."""
        if name in self._symbol_index:
            return self._symbol_index[name]
        return None

    def resolve_imports(self, imports: List[ELFImport]) -> List[ResolvedImport]:
        out = []
        for imp in imports:
            lib = self.resolve_name(imp.name)
            if lib:
                out.append(ResolvedImport(imp.name, nid_of(imp.name), lib, "resolved"))
            elif imp.name in self._absent_symbols:
                out.append(
                    ResolvedImport(
                        imp.name, nid_of(imp.name), self._absent_symbols[imp.name], "missing-module"
                    )
                )
            else:
                out.append(ResolvedImport(imp.name, nid_of(imp.name), None, "unresolved"))
        return out

    def analyze_bytes(self, data: bytes, source_name: str = "upload") -> ResolutionReport:
        """Parse and analyze ELF bytes, returning a full resolution report."""
        imports = []
        try:
            imports = parse_elf_imports(data)
        except ELFError:
            pass
        resolved = self.resolve_imports(imports)
        return self._build_report(resolved, source_name, imports)

    def _build_report(
        self, resolved: List[ResolvedImport], source_name: str, original: List[ELFImport]
    ) -> ResolutionReport:
        resolved_count = sum(1 for r in resolved if r.status == "resolved")
        unresolved_count = sum(1 for r in resolved if r.status == "unresolved")
        missing_module_count = sum(1 for r in resolved if r.status == "missing-module")
        total = len(resolved)
        coverage = resolved_count / total if total > 0 else 1.0
        score = int(round(coverage * 100))
        blockers = [r.name for r in resolved if r.status != "resolved"]
        needed = list(dict.fromkeys(r.library for r in resolved if r.library))
        return ResolutionReport(
            source_name, needed, resolved, resolved_count, unresolved_count,
            missing_module_count, coverage, score, blockers
        )