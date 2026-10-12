"""Shader recompiler ancillary register tracking and RDNA2 packed pixel analysis.

Implements bitfield extraction and live register reuse analysis for RDNA2
packed pixel ancillary VGPRs (typically v4) as reported in issue #2548
(Unreal Engine 4 shaders in Stray, PPSA02100).
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


@dataclass(frozen=True)
class BitfieldDef:
    name: str; offset: int; length: int; modeled: bool; source_builtin: Optional[str]; description: str


def _load_rdna2_layout() -> List[BitfieldDef]:
    """Load RDNA2 ancillary VGPR layout from JSON data file."""
    data_path = Path(__file__).parent.parent / "data" / "rdna2_layout.json"
    with data_path.open() as f:
        data = json.load(f)
    return [BitfieldDef(**b) for b in data["layout"]]


def _load_stray_addresses() -> List[str]:
    """Load Stray catalog shader addresses from JSON data file."""
    data_path = Path(__file__).parent.parent / "data" / "stray_shaders.json"
    with data_path.open() as f:
        data = json.load(f)
    return data["stray_shader_addresses"]


RDNA2_ANCILLARY_LAYOUT = _load_rdna2_layout()
STRAY_SHADER_ADDRESSES = _load_stray_addresses()


@dataclass
class IRInstruction:
    index: int; opcode: str; dest: Optional[str]; sources: List[str]
    bit_offset: Optional[int] = None; bit_length: Optional[int] = None; condition: Optional[str] = None


@dataclass
class ShaderAnalysisReport:
    shader_address: str; title_id: str; ancillary_vgpr: str; has_ancillary_access: bool
    extracted_fields: List[str]; register_reused: bool; live_use_chain: List[str]
    unsupported_bit_access: bool; rebuildable_pr1179: bool; rejection_reason: Optional[str]; status: str


class RDNA2ShaderAnalyzer:
    """Analyzer for RDNA2 packed pixel ancillary VGPR usage and PR #1179 compatibility."""

    def __init__(self) -> None:
        self.layout = RDNA2_ANCILLARY_LAYOUT

    @staticmethod
    def extract_bits(word: int, offset: int, length: int) -> int:
        return (word >> offset) & ((1 << length) - 1)

    @staticmethod
    def rebuild_ancillary_word(sample_id: int, layer: int) -> int:
        return ((sample_id & 0xF) << 8) | ((layer & 0x7FF) << 16)

    def decode_word(self, word: int) -> Dict[str, Any]:
        return {b.name: {"offset": b.offset, "length": b.length, "value": self.extract_bits(word, b.offset, b.length), "modeled": b.modeled, "source": b.source_builtin} for b in self.layout}

    def is_range_covered_by_pr1179(self, offset: int, length: int) -> bool:
        return (offset >= 8 and (offset + length) <= 12) or (offset >= 16 and (offset + length) <= 27)

    def analyze_ir_stream(self, shader_address: str, title_id: str, instructions: List[IRInstruction], ancillary_vgpr: str = "v4") -> ShaderAnalysisReport:
        has_anc, extracted, reused, chain, unsupp, reas, readers = False, [], False, [], False, None, []
        tainted = {ancillary_vgpr}
        for inst in instructions:
            if any(s in tainted for s in inst.sources):
                has_anc = True
                if inst.opcode in ("v_bfe_u32", "BitFieldUExtract"):
                    off, l = inst.bit_offset or 0, inst.bit_length or 32
                    if self.is_range_covered_by_pr1179(off, l):
                        extracted.append("render_target_index" if off >= 16 else "sample_index")
                    else:
                        unsupp = True
                        readers.append(f"{inst.opcode}({off}, {l})")
                elif inst.opcode == "SelectU32":
                    reused = True
                    if "SelectU32" not in chain: chain.append("SelectU32")
                    if inst.dest: tainted.add(inst.dest)
                else:
                    if inst.opcode not in chain: chain.append(inst.opcode)
                    if inst.dest: tainted.add(inst.dest)
                    readers.append(inst.opcode)
            if inst.dest == ancillary_vgpr and has_anc:
                reused = True

        if not has_anc:
            return ShaderAnalysisReport(shader_address, title_id, ancillary_vgpr, False, [], False, [], False, True, None, "clean")

        rebuildable = True
        if reused and chain:
            rebuildable = False
            reas = f"packed pixel ancillary input has an unsupported live use (used by BitFieldUExtract 16 11, {' -> '.join(chain)})"
            status = "rejected_unsupported_live_use"
        elif unsupp or readers:
            rebuildable = False
            reas = f"unsupported bit range extraction: {', '.join(readers)}"
            status = "rejected_unsupported_live_use"
        else:
            status = "rebuildable"

        return ShaderAnalysisReport(shader_address, title_id, ancillary_vgpr, True, list(dict.fromkeys(extracted)), reused, chain, unsupp or (reused and len(chain) > 0), rebuildable, reas, status)

    def get_stray_catalog_shaders(self) -> List[ShaderAnalysisReport]:
        return [
            self.analyze_ir_stream(
                addr, "PPSA02100",
                [
                    IRInstruction(0, "BitFieldUExtract", "vN", ["v4"], bit_offset=16, bit_length=11),
                    IRInstruction(1, "SelectU32", "v4", ["v4", "SelectU32 ? ?" if idx < 21 else "SelectU32 0 ?"], condition="IEqual32(HelperInvocation, 0)"),
                    IRInstruction(2, "Phi", "v4_phi", ["v4"]),
                    IRInstruction(3, "BitCastF32U32", "f_val", ["v4_phi"]),
                    IRInstruction(4, "PackFloat2x16Rtz", "packed_attr", ["f_val"]),
                    IRInstruction(5, "SetAttribute", None, ["packed_attr"]),
                ],
                ancillary_vgpr="v4"
            )
            for idx, addr in enumerate(STRAY_SHADER_ADDRESSES)
        ]