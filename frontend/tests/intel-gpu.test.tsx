import { describe, it, expect, vi, beforeEach } from "vitest"
import React from "react"
import { render, screen, waitFor, fireEvent } from "@testing-library/react"
import { IntelGpuPanel } from "../src/components/intel-gpu-panel"
import * as api from "../src/api"
import * as hooks from "../src/hooks"

vi.mock("../src/hooks", () => ({
  useAuth: vi.fn(),
}))

const mockProfiles: api.GpuDeviceProfile[] = [
  {
    gpu_id: "intel_uhd_770",
    name: "Intel UHD Graphics 770",
    device_id: "0xa780",
    driver_version: "101.6129",
    vulkan_version: "1.3.295",
  },
  {
    gpu_id: "rtx_4080",
    name: "NVIDIA GeForce RTX 4080",
    device_id: "0x2704",
    driver_version: "551.76",
    vulkan_version: "1.3.277",
  },
]

const mockReportFail: api.IntelGpuDiagnosticReport = {
  gpu_id: "intel_uhd_770",
  device_id: "0xa780",
  driver_version: "101.6129",
  vulkan_version: "1.3.295",
  total_diagnosed: 4,
  baseline_passed: 0,
  baseline_failed: 4,
  has_int64_atomics: false,
  diagnostics: [
    {
      test_id: "vop1_float_unary",
      test_name: "agc_driver_vop1_float_unary",
      target_location: "lane 13 fract_f32 v5",
      observed_output: "0x3f7fbd2b",
      expected_output: "0x3f7fbd2c",
      status: "failed",
      ulp_drift: 1,
      root_cause: "Intel Gen12 EU 1-ULP fract drift",
      resolution: "PR #1250 exact fraction V_FRACT_F32 from |x|",
    },
    {
      test_id: "sdwa_float_selectors",
      test_name: "agc_driver_sdwa_float_selectors",
      target_location: "lane 6 min_f16 BYTE_0/WORD_1 -> WORD_0",
      observed_output: "0xfda00047",
      expected_output: "0xfda00000",
      status: "failed",
      ulp_drift: null,
      root_cause: "SDWA sub-dword unmasked byte 0x47 leak in WORD_0",
      resolution: "SDWA destination 16-bit zero mask (dest & 0xFFFF0000)",
    },
    {
      test_id: "vopc_compare",
      test_name: "agc_driver_vopc_compare",
      target_location: "thread 0 compare 36 (f16 !(a >= b) with NaN)",
      observed_output: "0",
      expected_output: "1",
      status: "failed",
      ulp_drift: null,
      root_cause: "OpFOrdLessThan folds !(NaN >= NaN) to 0",
      resolution: "Emit SPIR-V OpFUnordLessThan for AMD RDNA semantics",
    },
    {
      test_id: "buffer_unaligned_base",
      test_name: "agc_driver_buffer_unaligned_base",
      target_location: "emission pass (64-bit buffer atomics)",
      observed_output: "ShaderRecompiler::Recompile: SPIR-V module emission failed: 64-bit buffer atomics need shaderBufferInt64Atomics",
      expected_output: "Clean SPIR-V emission or capability-aware test skip",
      status: "failed",
      ulp_drift: null,
      root_cause: "Device lacks optional shaderBufferInt64Atomics",
      resolution: "Query shaderBufferInt64Atomics and skip on unsupported devices",
    },
  ],
  recommendations: [
    "Merge PR #1250 (V_FRACT_F32 exact formulation) to resolve 1-ULP precision drift on Intel Gen12 EUs.",
  ],
}

describe("IntelGpuPanel Component", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(hooks.useAuth as any).mockReturnValue({
      user: { email: "ryan@example.com", role: "operator" },
      checkRole: vi.fn().mockReturnValue(true),
    })
  })

  it("renders Intel UHD 770 diagnostics with 4 failures detected", async () => {
    vi.spyOn(api, "getIntelGpuProfiles").mockResolvedValue(mockProfiles)
    vi.spyOn(api, "getIntelGpuDiagnostics").mockResolvedValue(mockReportFail)

    render(<IntelGpuPanel />)

    await waitFor(() => {
      expect(
        screen.getByText("Intel UHD 770 Execution Diagnostics (Issue #2114)")
      ).toBeInTheDocument()
    })

    expect(screen.getByText("4 Failures Detected")).toBeInTheDocument()
    expect(screen.getByText("agc_driver_vop1_float_unary")).toBeInTheDocument()
    expect(screen.getByText("agc_driver_sdwa_float_selectors")).toBeInTheDocument()
    expect(screen.getByText("agc_driver_vopc_compare")).toBeInTheDocument()
    expect(screen.getByText("agc_driver_buffer_unaligned_base")).toBeInTheDocument()
  })

  it("toggles fixes checkbox and reloads diagnostics", async () => {
    vi.spyOn(api, "getIntelGpuProfiles").mockResolvedValue(mockProfiles)
    const diagSpy = vi.spyOn(api, "getIntelGpuDiagnostics").mockResolvedValue(mockReportFail)

    render(<IntelGpuPanel />)

    await waitFor(() => {
      expect(screen.getByText("Intel UHD 770 Execution Diagnostics (Issue #2114)")).toBeInTheDocument()
    })

    const checkbox = screen.getByRole("checkbox")
    fireEvent.click(checkbox)

    expect(diagSpy).toHaveBeenCalledWith("intel_uhd_770", true)
  })
})
