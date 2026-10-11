"""Known host-side export surface for the PS5 porting workbench.

Symbol names are taken from the public homebrew import audit (issue #1578):
they are real unresolved imports reported by contributors, used here as
the ground-truth surface the resolver matches against. Module absence is
recorded explicitly (e.g. libSceOpusDec) so the resolver can report a
missing-module blocker instead of a missing-symbol one.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List


@dataclass(frozen=True)
class ModuleExport:
    module: str
    symbols: FrozenSet[str]
    present: bool = True


def build_export_db() -> List[ModuleExport]:
    """Return a deterministic, in-memory export database."""
    return [
        ModuleExport(
            module="libkernel",
            symbols=frozenset({
                "sysctl",
                "sysctlbyname",
                "pthread_set_name_np",
                "pthread_setcanceltype",
                "pthread_sigmask",
                "sigaction",
                "sigaddset",
                "sigemptyset",
                "sigdelset",
                "sigfillset",
                "_umtx_op",
                "getegid",
                "geteuid",
                "getgid",
                "getrlimit",
                "getuid",
                "pthread_getcpuclockid",
                "system",
                "readlink",
                "sceKernelGetFsSandboxRandomWord",
                "setcontext",
                "tcgetattr",
                "tcsetattr",
                "lstat",
                "madvise",
                "mlock",
                "socketpair",
                "fdatasync",
                "issetugid",
                "getdents",
                "getdirentries",
            }),
            present=True,
        ),
        ModuleExport(
            module="libScePosixForWebKit",
            symbols=frozenset({
                "isatty",
                "mkstemp",
                "arc4random_buf",
                "gethostbyname",
            }),
            present=True,
        ),
        ModuleExport(
            module="libSceLibcInternal",
            symbols=frozenset({
                "atoll",
                "gethostname",
                "makecontext",
                "getprogname",
                "malloc_usable_size",
                "syslog",
                "__isinf",
                "realpath",
                "memrchr",
                "freeifaddrs",
                "getifaddrs",
                "acosh",
                "asinh",
                "atanh",
                "cosh",
                "sinh",
                "sqrt",
                "trunc",
                "utime",
            }),
            present=True,
        ),
        ModuleExport(
            module="libSceVideoOut",
            symbols=frozenset({
                "sceVideoOutGetResolutionStatus",
                "sceVideoOutOpen",
                "sceVideoOutClose",
                "sceVideoOutRegisterBuffers",
                "sceVideoOutSubmitFlip",
                "sceVideoOutSetFlipRate",
                "sceVideoOutGetBufferAttribute",
            }),
            present=True,
        ),
        ModuleExport(
            module="libSceSystemService",
            symbols=frozenset({
                "sceSystemServiceLaunchWebBrowser",
            }),
            present=True,
        ),
        ModuleExport(
            module="libSceAgcDriver",
            symbols=frozenset({
                "sceAgcDriverGetTFRing",
                "sceAgcDriverSubmit",
                "sceAgcDriverRegisterResource",
                "sceAgcDriverNotify",
                "sceAgcDriverTrackStorageImage",
                "sceAgcDriverRegisterShaderType",
            }),
            present=True,
        ),
        ModuleExport(
            module="libSceSsl",
            symbols=frozenset({
                "sceSslGetCaList",
                "sceSslFreeCaList",
            }),
            present=True,
        ),
        ModuleExport(
            module="libSceNet",
            symbols=frozenset({
                "sceNetShowNetstat",
            }),
            present=True,
        ),
        ModuleExport(
            module="libSceOpusDec",
            symbols=frozenset({
                "CreateEx",
                "Decode",
                "Destroy",
                "GetSize",
                "Initialize",
                "Terminate",
            }),
            present=False,  # known missing module from the audit
        ),
        ModuleExport(
            module="libSceOpusCeltDec",
            symbols=frozenset({
                "CreateEx",
                "Decode",
                "Destroy",
                "GetSize",
                "Initialize",
                "Terminate",
            }),
            present=False,
        ),
        ModuleExport(
            module="libSceXml",
            symbols=frozenset({
                "sceXmlInit",
                "sceXmlParse",
                "sceXmlTerm",
                "sceXmlCreateParser",
                "sceXmlDestroyParser",
            }),
            present=False,  # missing system library reported in issue #2591
        ),
    ]