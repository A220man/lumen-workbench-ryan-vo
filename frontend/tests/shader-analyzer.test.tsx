import React from "react"
import { render, screen, waitFor, fireEvent } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { ShaderAnalyzerPanel } from "../src/components/shader-analyzer"
import * as hooks from "../src/hooks"
import * as api from "../src/api"

describe("ShaderAnalyzerPanel Component", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("renders RDNA2 bit layout and Stray catalog shaders", async () => {
    vi.spyOn(hooks, "useAuth").mockReturnValue({
      user: { id: "1", email: "viewer@test.local", name: "Viewer", role: "viewer" },
      token: "dummy-token",
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      checkRole: vi.fn().mockReturnValue(true),
    })

    vi.spyOn(api, "getRDNA2Layout").mockResolvedValue([
      {
        name: "render_target_index",
        offset: 16,
        length: 11,
        modeled: true,
        source_builtin: "Layer",
        description: "Render target index (bits 16-26)",
      },
      {
        name: "sample_index",
        offset: 8,
        length: 4,
        modeled: true,
        source_builtin: "SampleId",
        description: "MSAA sample index (bits 8-11)",
      },
    ])

    vi.spyOn(api, "getStrayShadersBatch").mockResolvedValue([
      {
        shader_address: "0x200e370000",
        title_id: "PPSA02100",
        ancillary_vgpr: "v4",
        has_ancillary_access: true,
        extracted_fields: ["render_target_index"],
        register_reused: true,
        live_use_chain: ["SelectU32", "Phi", "BitCastF32U32"],
        unsupported_bit_access: true,
        rebuildable_pr1179: false,
        rejection_reason: "packed pixel ancillary input has an unsupported live use",
        status: "rejected_unsupported_live_use",
      },
    ])

    render(<ShaderAnalyzerPanel />)

    await waitFor(() => {
      expect(
        screen.getByText("RDNA2 Shader Recompiler Diagnostics (Issue #2548)")
      ).toBeInTheDocument()
    })

    expect(screen.getByText("render_target_index")).toBeInTheDocument()
    expect(screen.getByText("sample_index")).toBeInTheDocument()
    expect(screen.getByText("0x200e370000")).toBeInTheDocument()
    expect(screen.getByText("rejected_unsupported_live_use")).toBeInTheDocument()
  })

  it("handles interactive bitfield reconstruction and decoding", async () => {
    vi.spyOn(hooks, "useAuth").mockReturnValue({
      user: { id: "1", email: "viewer@test.local", name: "Viewer", role: "viewer" },
      token: "dummy-token",
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      checkRole: vi.fn().mockReturnValue(true),
    })

    vi.spyOn(api, "getRDNA2Layout").mockResolvedValue([])
    vi.spyOn(api, "getStrayShadersBatch").mockResolvedValue([])

    vi.spyOn(api, "analyzeShader").mockResolvedValue({
      shader_address: "0x1000_interactive",
      title_id: "INTERACTIVE",
      ancillary_vgpr: "v4",
      has_ancillary_access: true,
      extracted_fields: ["render_target_index", "sample_index"],
      register_reused: false,
      live_use_chain: [],
      unsupported_bit_access: false,
      rebuildable_pr1179: true,
      rejection_reason: null,
      status: "rebuildable",
      decoded_word: {
        sample_index: { offset: 8, length: 4, value: 2, modeled: true, source: "SampleId" },
        render_target_index: { offset: 16, length: 11, value: 4, modeled: true, source: "Layer" },
      },
    })

    render(<ShaderAnalyzerPanel />)

    await waitFor(() => {
      expect(screen.getByText("Reconstruct & Decode")).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText("Reconstruct & Decode"))

    await waitFor(() => {
      expect(screen.getByText(/Sample Index \(bits 8-11\): 2/)).toBeInTheDocument()
      expect(screen.getByText(/Render Target Layer \(bits 16-26\): 4/)).toBeInTheDocument()
    })
  })
})
