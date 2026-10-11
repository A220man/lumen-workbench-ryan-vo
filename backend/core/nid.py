"""Deterministic 32-bit symbol hasher used by the workbench resolver.

This is the workbench's own FNV-1a hash, not a console SDK NID algorithm.
The labeled evaluation dataset is generated with the same function, so
metrics measure resolver logic, not fidelity to any console SDK.
"""
from __future__ import annotations

MASK32 = 0xFFFFFFFF


def nid_of(name: str) -> int:
    """Return the deterministic 32-bit nid hash for a symbol name."""
    h = 0x811c9dc5
    for b in name.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & MASK32
    return h
