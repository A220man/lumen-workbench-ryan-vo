"""Intel UHD 770 GPU execution precision, SDWA, and capability diagnostics (issue #2114)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass(frozen=True)
class GpuDeviceProfile:
    gpu_id: str; name: str; device_id: str; driver_version: str; vulkan_version: str
    has_shader_buffer_int64_atomics: bool; fp_precision_mode: str; sdwa_masking_mode: str
    nan_comparison_mode: str; baseline_passed: int; baseline_total: int

GPU_PROFILES = {
    "intel_uhd_770": GpuDeviceProfile("intel_uhd_770", "Intel UHD Graphics 770", "0xa780", "101.6129", "1.3.295", False, "relaxed_ulp_drift", "unmasked_leak", "ordered_folding", 489, 494),
    "rtx_4080": GpuDeviceProfile("rtx_4080", "NVIDIA GeForce RTX 4080", "0x2704", "551.76", "1.3.277", True, "strict_ieee754", "hardware_subdword", "strict_unordered", 494, 494),
}

TEST_SPECS = {
    "vop1_float_unary": ("agc_driver_vop1_float_unary", "lane 13 fract_f32 v5", "0x3f7fbd2c", "0x3f7fbd2b", 1, "Intel Gen12 EU 1-ULP fract drift", "PR #1250 exact fraction V_FRACT_F32 from |x|"),
    "sdwa_float_selectors": ("agc_driver_sdwa_float_selectors", "lane 6 min_f16 BYTE_0/WORD_1 -> WORD_0", "0xfda00000", "0xfda00047", None, "SDWA sub-dword unmasked byte 0x47 leak in WORD_0", "SDWA destination 16-bit zero mask (dest & 0xFFFF0000)"),
    "vopc_compare": ("agc_driver_vopc_compare", "thread 0 compare 36 (f16 !(a >= b) with NaN)", "1", "0", None, "OpFOrdLessThan folds !(NaN >= NaN) to 0", "Emit SPIR-V OpFUnordLessThan for AMD RDNA semantics"),
    "buffer_unaligned_base": ("agc_driver_buffer_unaligned_base", "emission pass (64-bit buffer atomics)", "Clean SPIR-V emission or capability-aware test skip", "ShaderRecompiler::Recompile: SPIR-V module emission failed: 64-bit buffer atomics need shaderBufferInt64Atomics", None, "Device lacks optional shaderBufferInt64Atomics", "Query shaderBufferInt64Atomics and skip on unsupported devices"),
}

@dataclass
class ExecutionTestDiagnostic:
    test_id: str; test_name: str; target_location: str; observed_output: str; expected_output: str
    status: str; ulp_drift: Optional[int]; root_cause: str; resolution: str; applied_fix: bool
    fixed_output: str; fixed_status: str

@dataclass
class IntelGpuDiagnosticReport:
    gpu_id: str; gpu_name: str; device_id: str; driver_version: str; vulkan_version: str
    total_diagnosed: int; baseline_passed: int; baseline_failed: int; fixed_passed: int
    overall_status: str; has_int64_atomics: bool; diagnostics: List[ExecutionTestDiagnostic]
    recommendations: List[str]

class IntelGpuCompatAnalyzer:
    def __init__(self) -> None:
        self.profiles = GPU_PROFILES

    def get_profiles(self) -> List[GpuDeviceProfile]:
        return list(self.profiles.values())

    def get_profile(self, gpu_id: str) -> GpuDeviceProfile:
        return self.profiles.get(gpu_id, self.profiles["intel_uhd_770"])

    def diagnose_test(self, test_id: str, gpu_id: str = "intel_uhd_770", apply_fix: bool = False) -> ExecutionTestDiagnostic:
        name, target, exp, fail_out, drift, cause, res = TEST_SPECS[test_id]
        p = self.get_profile(gpu_id)
        is_intel = p.gpu_id == "intel_uhd_770"
        if test_id == "buffer_unaligned_base":
            if p.has_shader_buffer_int64_atomics: out, st = "Clean 64-bit SPIR-V emission (hardware supported)", "passed"
            elif apply_fix: out, st = "Skipped unsupported 64-bit atomic test with clean capability diagnostic", "passed"
            else: out, st = fail_out, "failed"
            fixed_out = "Skipped unsupported 64-bit atomic test with clean capability diagnostic" if not p.has_shader_buffer_int64_atomics else out
        else:
            out, st = (exp, "passed") if (not is_intel or apply_fix) else (fail_out, "failed")
            fixed_out = exp
        return ExecutionTestDiagnostic(
            test_id, name, target, out, exp, st, drift if st == "failed" else None, cause, res,
            apply_fix or (not is_intel and test_id != "buffer_unaligned_base") or (test_id == "buffer_unaligned_base" and p.has_shader_buffer_int64_atomics),
            fixed_out, "passed",
        )

    def diagnose_vop1_fract(self, gpu_id: str = "intel_uhd_770", apply_fix: bool = False) -> ExecutionTestDiagnostic: return self.diagnose_test("vop1_float_unary", gpu_id, apply_fix)
    def diagnose_sdwa_min_f16(self, gpu_id: str = "intel_uhd_770", apply_fix: bool = False) -> ExecutionTestDiagnostic: return self.diagnose_test("sdwa_float_selectors", gpu_id, apply_fix)
    def diagnose_vopc_compare(self, gpu_id: str = "intel_uhd_770", apply_fix: bool = False) -> ExecutionTestDiagnostic: return self.diagnose_test("vopc_compare", gpu_id, apply_fix)
    def diagnose_buffer_atomics(self, gpu_id: str = "intel_uhd_770", apply_fix: bool = False) -> ExecutionTestDiagnostic: return self.diagnose_test("buffer_unaligned_base", gpu_id, apply_fix)

    def run_diagnostics(self, gpu_id: str = "intel_uhd_770", apply_fixes: bool = False) -> IntelGpuDiagnosticReport:
        p = self.get_profile(gpu_id)
        diag = [self.diagnose_test(tid, gpu_id, apply_fixes) for tid in TEST_SPECS]
        passed = sum(1 for d in diag if d.status == "passed")
        recs = [
            "Merge PR #1250 (V_FRACT_F32 exact formulation) to resolve 1-ULP precision drift on Intel Gen12 EUs.",
            "Enforce destination masking (0xFFFF0000) for half-precision SDWA float selector inserts.",
            "Use SPIR-V OpFUnordLessThan for AMD RDNA !(a >= b) f16 comparisons to preserve IEEE NaN semantics.",
            "Check VkPhysicalDeviceVulkan12Features.shaderBufferInt64Atomics before emitting 64-bit atomics; skip tests on unsupported devices.",
        ]
        return IntelGpuDiagnosticReport(
            p.gpu_id, p.name, p.device_id, p.driver_version, p.vulkan_version, len(diag),
            passed, len(diag) - passed, len(diag), "clean" if passed == len(diag) else "hardware_incompatibilities_detected",
            p.has_shader_buffer_int64_atomics, diag, recs,
        )
