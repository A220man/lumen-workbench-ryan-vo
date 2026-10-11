"""Import-resolution evaluation: labeled dataset + computed metrics.

This is the workbench's agent-evaluation workflow. It compares the
resolver's predictions against a grounded truth set (derived from the
public import audit) and reports precision, recall, F1 and coverage.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .export_db import build_export_db
from .import_resolver import ImportResolver, ResolvedImport


@dataclass(frozen=True)
class DatasetExample:
    symbol: str
    expected_library: str


def labeled_dataset() -> List[Tuple[str, str]]:
    """Ground-truth import audit from community reports (issue #1578)."""
    groups = {
        "libkernel": [
            "sysctl", "sysctlbyname", "pthread_set_name_np", "pthread_setcanceltype",
            "pthread_sigmask", "sigaction", "sigaddset", "sigemptyset", "sigdelset",
            "sigfillset", "_umtx_op", "getegid", "geteuid", "getgid", "getrlimit",
            "getuid", "pthread_getcpuclockid", "system", "readlink",
            "sceKernelGetFsSandboxRandomWord", "setcontext", "tcgetattr", "tcsetattr",
            "lstat", "madvise", "mlock", "socketpair", "fdatasync", "issetugid",
            "getdents", "getdirentries",
        ],
        "libScePosixForWebKit": ["isatty", "mkstemp", "arc4random_buf", "gethostbyname"],
        "libSceLibcInternal": [
            "atoll", "gethostname", "makecontext", "getprogname", "malloc_usable_size",
            "syslog", "__isinf", "realpath", "memrchr", "freeifaddrs", "getifaddrs",
            "acosh", "asinh", "atanh", "cosh", "sinh", "sqrt", "trunc", "utime",
        ],
        "libSceVideoOut": [
            "sceVideoOutGetResolutionStatus", "sceVideoOutOpen", "sceVideoOutRegisterBuffers", "sceVideoOutSubmitFlip",
        ],
        "libSceSystemService": ["sceSystemServiceLaunchWebBrowser"],
        "libSceAgcDriver": [
            "sceAgcDriverGetTFRing", "sceAgcDriverSubmit", "sceAgcDriverRegisterResource", "sceAgcDriverTrackStorageImage",
        ],
    }
    return [(sym, lib) for lib, syms in groups.items() for sym in syms]


@dataclass
class EvalMetrics:
    precision: float  # 0..1
    recall: float
    f1: float
    coverage: float  # fraction of dataset symbols resolved
    true_positive: int
    false_positive: int
    false_negative: int
    per_library: Dict[str, Dict[str, int]]  # lib -> {tp,fp,fn}


def run_evaluation(resolver: ImportResolver) -> EvalMetrics:
    """Run the import resolver against the labeled dataset.

    Returns precision, recall, F1, and coverage. The labeled dataset is
    grounded in the public import audit (issue #1578), so this measures
    how well the resolver predicts the expected library for each symbol.
    """
    dataset = labeled_dataset()
    tp = fp = fn = 0
    per_lib: Dict[str, Dict[str, int]] = {}
    for ex in dataset:
        sym = ex.symbol if hasattr(ex, "symbol") else ex[0]
        exp_lib = ex.expected_library if hasattr(ex, "expected_library") else ex[1]
        pred_lib = resolver.resolve_name(sym)
        if pred_lib == exp_lib:
            tp += 1
            d = per_lib.setdefault(exp_lib, {"tp": 0, "fp": 0, "fn": 0})
            d["tp"] += 1
        else:
            fn += 1
            d = per_lib.setdefault(exp_lib, {"tp": 0, "fp": 0, "fn": 0})
            d["fn"] += 1
            if pred_lib:
                d2 = per_lib.setdefault(pred_lib, {"tp": 0, "fp": 0, "fn": 0})
                d2["fp"] += 1
    total = len(dataset)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    coverage = tp / total if total > 0 else 0.0
    return EvalMetrics(
        precision=precision,
        recall=recall,
        f1=f1,
        coverage=coverage,
        true_positive=tp,
        false_positive=fp,
        false_negative=fn,
        per_library=per_lib,
    )