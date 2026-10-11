"""Shader recompiler ancillary register tracking and RDNA2 packed pixel analysis.

Implements bitfield extraction and live register reuse analysis for RDNA2
packed pixel ancillary VGPRs (typically v4) as reported in issue #2548
(Unreal Engine 4 shaders in Stray, PPSA02100).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class BitfieldDef:
    name: str
    offset: int
    length: int
    modeled: bool
    source_builtin: Optional[str]
    description: str


RDNA2_ANCILLARY_LAYOUT: List[BitfieldDef] = [
    BitfieldDef(*s) for s in [
        ("prim_type", 0, 2, False, "PrimitiveType", "Primitive type (RDNA 3.5 ISA; unmeasured on RDNA 2)"),
        ("vrs_rates", 2, 4, False, "FragmentSizeEXT", "VRS shading rate bits (unmeasured on RDNA 2)"),
        ("reserved_low", 6, 1, False, None, "Undocumented ancillary bit 6"),
        ("eye_id", 7, 1, False, "ViewIndex", "Eye ID / multiview view index"),
        ("sample_index", 8, 4, True, "SampleId", "MSAA sample index (bits 8-11)"),
        ("reserved_mid", 12, 4, False, None, "Undocumented ancillary bits 12-15"),
        ("render_target_index", 16, 11, True, "Layer", "Render target index (bits 16-26)"),
        ("reserved_high", 27, 5, False, None, "Undocumented ancillary bits 27-31"),
    ]
]


@dataclass
class IRInstruction:
    index: int
    opcode: str
    dest: Optional[str]
    sources: List[str]
    bit_offset: Optional[int] = None
    bit_length: Optional[int] = None
    condition: Optional[str] = None


@dataclass
class ShaderAnalysisReport:
    shader_address: str
    title_id: str
    ancillary_vgpr: str
    has_ancillary_access: bool
    extracted_fields: List[str]
    register_reused: bool
    live_use_chain: List[str]
    unsupported_bit_access: bool
    rebuildable_pr1179: bool
    rejection_reason: Optional[str]
    status: str  # "rebuildable" | "rejected_unsupported_live_use" | "clean"


class RDNA2ShaderAnalyzer:
    """Analyzer for RDNA2 packed pixel ancillary VGPR usage and PR #1179 compatibility."""

    def __init__(self) -> None:
        self.layout = RDNA2_ANCILLARY_LAYOUT

    @staticmethod
    def extract_bits(word: int, offset: int, length: int) -> int:
        mask = (1 << length) - 1
        return (word >> offset) & mask

    @staticmethod
    def rebuild_ancillary_word(sample_id: int, layer: int) -> int:
        """Deterministic PR #1179 reconstruction from SampleId and Layer."""
        return ((sample_id & 0xF) << 8) | ((layer & 0x7FF) << 16)

    def decode_word(self, word: int) -> Dict[str, Any]:
        """Decode all known and unmodelled bitfields from a 32-bit ancillary word."""
        res: Dict[str, Any] = {}
        for b in self.layout:
            val = self.extract_bits(word, b.offset, b.length)
            res[b.name] = {
                "offset": b.offset,
                "length": b.length,
                "value": val,
                "modeled": b.modeled,
                "source": b.source_builtin,
            }
        return res

    def is_range_covered_by_pr1179(self, offset: int, length: int) -> bool:
        """Check if bitfield extraction falls entirely within SampleId or Layer."""
        sample_ok = (offset >= 8 and (offset + length) <= 12)
        layer_ok = (offset >= 16 and (offset + length) <= 27)
        return sample_ok or layer_ok

    def analyze_ir_stream(
        self,
        shader_address: str,
        title_id: str,
        instructions: List[IRInstruction],
        ancillary_vgpr: str = "v4",
    ) -> ShaderAnalysisReport:
        has_ancillary = False
        extracted_fields: List[str] = []
        register_reused = False
        live_use_chain: List[str] = []
        unsupported_bits = False
        rebuildable = True
        rejection_reason: Optional[str] = None
        raw_word_readers: List[str] = []

        tainted_vars = {ancillary_vgpr}

        for inst in instructions:
            reads_tainted = any(s in tainted_vars for s in inst.sources)

            if reads_tainted:
                has_ancillary = True
                if inst.opcode in ("v_bfe_u32", "BitFieldUExtract"):
                    off = inst.bit_offset if inst.bit_offset is not None else 0
                    length = inst.bit_length if inst.bit_length is not None else 32
                    if self.is_range_covered_by_pr1179(off, length):
                        if off >= 16:
                            extracted_fields.append("render_target_index")
                        else:
                            extracted_fields.append("sample_index")
                    else:
                        unsupported_bits = True
                        rebuildable = False
                        raw_word_readers.append(f"{inst.opcode}({off}, {length})")
                elif inst.opcode == "SelectU32":
                    register_reused = True
                    if "SelectU32" not in live_use_chain:
                        live_use_chain.append("SelectU32")
                    if inst.dest:
                        tainted_vars.add(inst.dest)
                else:
                    if inst.opcode not in live_use_chain:
                        live_use_chain.append(inst.opcode)
                    if inst.dest:
                        tainted_vars.add(inst.dest)
                    raw_word_readers.append(inst.opcode)

            # Detect register overwrite and reuse
            if inst.dest == ancillary_vgpr and has_ancillary:
                register_reused = True

        if not has_ancillary:
            return ShaderAnalysisReport(
                shader_address=shader_address,
                title_id=title_id,
                ancillary_vgpr=ancillary_vgpr,
                has_ancillary_access=False,
                extracted_fields=[],
                register_reused=False,
                live_use_chain=[],
                unsupported_bit_access=False,
                rebuildable_pr1179=True,
                rejection_reason=None,
                status="clean",
            )

        if register_reused and live_use_chain:
            rebuildable = False
            rejection_reason = (
                f"packed pixel ancillary input has an unsupported live use "
                f"(used by BitFieldUExtract 16 11, {' -> '.join(live_use_chain)})"
            )
            status = "rejected_unsupported_live_use"
        elif unsupported_bits or raw_word_readers:
            rebuildable = False
            rejection_reason = f"unsupported bit range extraction: {', '.join(raw_word_readers)}"
            status = "rejected_unsupported_live_use"
        else:
            status = "rebuildable"

        return ShaderAnalysisReport(
            shader_address=shader_address,
            title_id=title_id,
            ancillary_vgpr=ancillary_vgpr,
            has_ancillary_access=True,
            extracted_fields=list(dict.fromkeys(extracted_fields)),
            register_reused=register_reused,
            live_use_chain=live_use_chain,
            unsupported_bit_access=unsupported_bits or (register_reused and len(live_use_chain) > 0),
            rebuildable_pr1179=rebuildable,
            rejection_reason=rejection_reason,
            status=status,
        )

    def get_stray_catalog_shaders(self) -> List[ShaderAnalysisReport]:
        """Known Stray (PPSA02100 v1.05) UE4 pixel shaders failing on issue #2548."""
        stray_addresses = [
            "0x200e370000", "0x200e400000", "0x200e410000", "0x200e460000",
            "0x200e470000", "0x200e4b0000", "0x200e510000", "0x200e580000",
            "0x200e5f0000", "0x200e610000", "0x200e640000", "0x200e650000",
            "0x200e700000", "0x200e760000", "0x200e770000", "0x200e7a0000",
            "0x200e7b0000", "0x200e7c0000", "0x200e800000", "0x200e830000",
            "0x200e840000", "0x200e8c0000", "0x200e8d0000", "0x200e8f0000",
            "0x200e950000", "0x200e970000",
        ]
        reports: List[ShaderAnalysisReport] = []
        for idx, addr in enumerate(stray_addresses):
            select_variant = "SelectU32 ? ?" if idx < 21 else "SelectU32 0 ?"
            instructions = [
                IRInstruction(0, "BitFieldUExtract", "vN", ["v4"], bit_offset=16, bit_length=11),
                IRInstruction(1, "SelectU32", "v4", ["v4", select_variant], condition="IEqual32(HelperInvocation, 0)"),
                IRInstruction(2, "Phi", "v4_phi", ["v4"]),
                IRInstruction(3, "BitCastF32U32", "f_val", ["v4_phi"]),
                IRInstruction(4, "PackFloat2x16Rtz", "packed_attr", ["f_val"]),
                IRInstruction(5, "SetAttribute", None, ["packed_attr"]),
            ]
            report = self.analyze_ir_stream(addr, "PPSA02100", instructions, ancillary_vgpr="v4")
            reports.append(report)
        return reports
