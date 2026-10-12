import React from "react"
import { render, screen, waitFor, fireEvent } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { StorageWritebackPanel } from "../src/components/storage-writeback"
import * as hooks from "../src/hooks"
import * as api from "../src/api"

describe("StorageWritebackPanel Component", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("renders StorageWritebackPanel and simulates Silksong issue #865 conflict", async () => {
    vi.spyOn(hooks, "useAuth").mockReturnValue({
      user: { id: "1", email: "viewer@test.local", name: "Viewer", role: "viewer" },
      token: "dummy-token",
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      checkRole: vi.fn().mockReturnValue(true),
    })

    vi.spyOn(api, "getStorageWritebackPresets").mockResolvedValue([
      {
        id: "silksong-sdf-atlas",
        name: "Silksong SDF Font Atlas (Issue #865)",
        description: "Unaligned 512x512 R8 texture",
        texture_address: 0x25E042000,
        texture_size: 0x40000,
        expected_status: "conflict_detected",
      },
      {
        id: "aligned-baseline",
        name: "Aligned 64 KiB Texture Baseline",
        description: "Aligned texture baseline",
        texture_address: 0x25E040000,
        texture_size: 0x40000,
        expected_status: "clean",
      },
    ])

    vi.spyOn(api, "simulateStorageWriteback").mockResolvedValue({
      title_id: "PPSA12544",
      title_name: "Hollow Knight: Silksong (Unity TextCore)",
      texture_address: "0x25e042000",
      texture_size: "0x40000",
      alignment_offset: "0x2000",
      total_blocks_spanned: 5,
      total_pages_spanned: 64,
      edge_blocks_count: 2,
      units: [],
      block_policy_corrupted: true,
      block_policy_dropped_units: ["block_0_edge", "block_4_edge"],
      page_policy_corrupted: false,
      page_policy_dropped_units: [],
      eager_writeback_corrupted: false,
      corrupted_glyphs: ["OPTIONS_O", "GAME_MARK"],
      warning_logged: "[gpu] storage image 0x25e042000+0x40000: guest memory changed while GPU results were pending; keeping the CPU's blocks",
      root_cause: "64 KiB block granularity falsely treats adjacent non-overlapping CPU writes as stored-over",
      recommendation: "Adopt 4 KiB page granularity for StoredOver tracking, or enable APS5_EAGER_WRITEBACK=1",
      status: "conflict_detected",
    })

    render(<StorageWritebackPanel />)

    await waitFor(() => {
      expect(screen.getByText("Storage Write-Back Diagnostics (Issue #865)")).toBeInTheDocument()
    })

    expect(screen.getByText("Silksong SDF Font Atlas (Issue #865)")).toBeInTheDocument()
    expect(screen.getByText("Conflict Detected (Boxes in Menu Text)")).toBeInTheDocument()
    expect(screen.getByText(/DROPPED \(Corrupted into Solid Boxes\)/)).toBeInTheDocument()
    expect(screen.getByText(/OPTIONS_O, GAME_MARK/)).toBeInTheDocument()
    expect(screen.getByText(/PRESERVED \(Zero Edge Drops\)/)).toBeInTheDocument()
    expect(screen.getByText(/guest memory changed while GPU results were pending/)).toBeInTheDocument()
  })

  it("handles selecting aligned baseline preset", async () => {
    vi.spyOn(hooks, "useAuth").mockReturnValue({
      user: { id: "1", email: "viewer@test.local", name: "Viewer", role: "viewer" },
      token: "dummy-token",
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      checkRole: vi.fn().mockReturnValue(true),
    })

    vi.spyOn(api, "getStorageWritebackPresets").mockResolvedValue([
      {
        id: "silksong-sdf-atlas",
        name: "Silksong SDF Font Atlas (Issue #865)",
        description: "Unaligned 512x512 R8 texture",
        texture_address: 0x25E042000,
        texture_size: 0x40000,
        expected_status: "conflict_detected",
      },
      {
        id: "aligned-baseline",
        name: "Aligned 64 KiB Texture Baseline",
        description: "Aligned texture baseline",
        texture_address: 0x25E040000,
        texture_size: 0x40000,
        expected_status: "clean",
      },
    ])

    const simulateSpy = vi.spyOn(api, "simulateStorageWriteback").mockResolvedValue({
      title_id: "PPSA00000",
      title_name: "Aligned 64 KiB Texture Baseline",
      texture_address: "0x25e040000",
      texture_size: "0x40000",
      alignment_offset: "0x0",
      total_blocks_spanned: 4,
      total_pages_spanned: 64,
      edge_blocks_count: 0,
      units: [],
      block_policy_corrupted: false,
      block_policy_dropped_units: [],
      page_policy_corrupted: false,
      page_policy_dropped_units: [],
      eager_writeback_corrupted: false,
      corrupted_glyphs: [],
      warning_logged: null,
      root_cause: "clean",
      recommendation: "Adopt 4 KiB page granularity for StoredOver tracking, or enable APS5_EAGER_WRITEBACK=1",
      status: "clean",
    })

    render(<StorageWritebackPanel />)

    await waitFor(() => {
      expect(screen.getByText("Aligned 64 KiB Texture Baseline")).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText("Aligned 64 KiB Texture Baseline"))

    await waitFor(() => {
      expect(screen.getByText("Clean Write-Back (Zero Corruption)")).toBeInTheDocument()
    })
    expect(simulateSpy).toHaveBeenCalledWith({
      texture_address: 0x25E040000,
      texture_size: 0x40000,
    })
  })
})
