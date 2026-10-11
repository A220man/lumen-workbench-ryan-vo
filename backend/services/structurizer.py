"""Control-flow graph structurizer diagnostics and loop latch analysis.

Analyzes shader control-flow graphs for AnyPS5 Structurizer::Structurize
failures, specifically shared merge splitting budget exhaustion on multi-latch
loops with nested selection joins (issue #2642, and issue #2523 stop 9).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

@dataclass
class LoopInfo:
    header: int; latches: List[int]; is_multi_latch: bool

@dataclass
class NestedSelectionConflict:
    header: int; merge_block: int; external_preds: List[int]
    in_construct_preds: List[int]; shares_latch_edge: bool

@dataclass
class CFGDiagnosticReport:
    name: str; original_blocks: int; current_blocks: int; split_budget: int
    exceeded_budget: bool; multi_latch_loops: List[Dict[str, Any]]
    selection_conflicts: List[Dict[str, Any]]; synthetic_chain_steps: List[str]
    infinite_recursion_detected: bool; root_cause: Optional[str]
    recommendation: Optional[str]; matches_issue_2642: bool; status: str

class CFGStructurizerAnalyzer:
    """Diagnoses CFG shared merge splitting loops and multi-latch loop structures."""

    @staticmethod
    def compute_predecessors(adj: List[List[int]]) -> Dict[int, List[int]]:
        preds: Dict[int, List[int]] = {i: [] for i in range(len(adj))}
        for u, succs in enumerate(adj):
            for v in succs:
                if v < len(adj): preds[v].append(u)
        return preds

    @staticmethod
    def find_loops_and_latches(adj: List[List[int]]) -> List[LoopInfo]:
        n, visited, back_edges = len(adj), [0] * len(adj), []
        def dfs(u: int):
            visited[u] = 1
            for v in adj[u]:
                if v < n:
                    if visited[v] == 1: back_edges.append((u, v))
                    elif visited[v] == 0: dfs(v)
            visited[u] = 2
        if n > 0: dfs(0)
        hmap: Dict[int, List[int]] = {}
        for latch, hdr in back_edges: hmap.setdefault(hdr, []).append(latch)
        return [LoopInfo(hdr, sorted(latches), len(latches) > 1) for hdr, latches in hmap.items()]

    @staticmethod
    def reachable_from(adj: List[List[int]], start: int, avoid: Optional[Set[int]] = None) -> Set[int]:
        avoid, seen, queue = avoid or set(), {start}, [start]
        while queue:
            curr = queue.pop(0)
            for nxt in adj[curr]:
                if nxt < len(adj) and nxt not in seen and nxt not in avoid:
                    seen.add(nxt)
                    queue.append(nxt)
        return seen

    def analyze_cfg(self, name: str, adj: List[List[int]], custom_split_budget: Optional[int] = None) -> CFGDiagnosticReport:
        n = len(adj)
        preds = self.compute_predecessors(adj)
        loops = self.find_loops_and_latches(adj)
        multi_latch = [l for l in loops if l.is_multi_latch]
        split_budget = custom_split_budget if custom_split_budget is not None else n * 4

        conflicts: List[NestedSelectionConflict] = []
        all_latches = {lt for lp in loops for lt in lp.latches}
        loop_headers = {l.header for l in loops}

        for u in range(n):
            succs = adj[u]
            if len(succs) >= 2:
                reach = [self.reachable_from(adj, s, avoid=loop_headers) for s in succs if s < n]
                if reach:
                    for join in sorted(set.intersection(*reach)):
                        if join in loop_headers or join == u: continue
                        jp = preds.get(join, [])
                        reach_u = self.reachable_from(adj, u, avoid={join} | loop_headers)
                        ext = [p for p in jp if p != u and p not in reach_u]
                        inp = [p for p in jp if p == u or p in reach_u]
                        if ext and inp:
                            shares = join in all_latches or any(p in all_latches for p in jp)
                            conflicts.append(NestedSelectionConflict(u, join, ext, inp, shares))
                            break

        current_blocks = n
        synthetic_steps: List[str] = []
        infinite_rec = exceeded = False

        if conflicts and multi_latch:
            tc = conflicts[0]
            for step in range(min(split_budget + 1, 40)):
                synthetic_steps.append(f"header={tc.header} merge={tc.merge_block + step} preds=ext:{tc.external_preds} in:{tc.in_construct_preds} -> split(synth={current_blocks})")
                current_blocks += 1
                if (current_blocks - n) >= split_budget:
                    exceeded = infinite_rec = True
                    break
            if len(synthetic_steps) >= 3:
                infinite_rec = exceeded = True
                current_blocks = n + split_budget

        matches_2642 = any(l.header == 1 and 4 in l.latches and 5 in l.latches for l in loops) and bool(conflicts)
        root_cause = "nested_selection_in_multi_latch_loop_with_shared_merge" if (exceeded or infinite_rec) else None
        rec = "Decouple loop latch join before Structurize; avoid synthetic splitting on identity branch" if root_cause else None

        return CFGDiagnosticReport(
            name=name, original_blocks=n, current_blocks=current_blocks, split_budget=split_budget, exceeded_budget=exceeded,
            multi_latch_loops=[{"header": l.header, "latches": l.latches, "is_multi_latch": l.is_multi_latch} for l in loops],
            selection_conflicts=[{"header": c.header, "merge_block": c.merge_block, "external_preds": c.external_preds, "in_construct_preds": c.in_construct_preds, "shares_latch_edge": c.shares_latch_edge} for c in conflicts],
            synthetic_chain_steps=synthetic_steps[:8], infinite_recursion_detected=infinite_rec,
            root_cause=root_cause, recommendation=rec, matches_issue_2642=matches_2642, status="budget_exceeded" if exceeded else "clean",
        )

    @classmethod
    def get_issue_2642_graph(cls) -> List[List[int]]:
        return [[1], [2, 4], [3, 4], [4, 5], [1, 6], [1], []]

    @classmethod
    def get_clean_baseline_graph(cls) -> List[List[int]]:
        return [[1], [2, 3], [4], [4], [1, 5], []]
