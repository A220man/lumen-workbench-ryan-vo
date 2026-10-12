import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor, fireEvent } from "@testing-library/react"
import { BrowserRouter } from "react-router-dom"
import { FirstLightDiagnostic } from "../src/components/first-light-diagnostic"
import { LumenWorkbenchProvider } from "../src/context"

vi.mock("../src/hooks", () => ({
  useAuth: () => ({ isAuthenticated: true }),
}))

vi.mock("../src/api", () => ({
  getFirstLightStops: vi.fn(),
  getFirstLightPresets: vi.fn(),
  analyzeFirstLight: vi.fn(),
}))

import { getFirstLightStops, getFirstLightPresets, analyzeFirstLight } from "../src/api"
import type { StartupStopItem, FirstLightPresetItem, FirstLightReportResponse } from "../src/api"

const mockStops: StartupStopItem[] = [
  {
    index: 1,
    description: "loader: undefined symbol sceSslGetCaList",
    error_text: "loader: undefined symbol: qOn+wm28wmA (sceSslGetCaList)",
    shader_cache_misses: null,
    prs: [{ number: 2830, url: "https://github.com/boykopovar/AnyPS5/pull/2830", commit: "33184a1b", merged: true, description: "sceSslGetCaList implementation" }],
    verified: true,
    notes: "Both PRs merged",
  },
  {
    index: 2,
    description: "sceSharePlayInitialize: invalid argument",
    error_text: "sceSharePlayInitialize: invalid argument (null heap, size 0x1800)",
    shader_cache_misses: null,
    prs: [{ number: 2946, url: "https://github.com/boykopovar/AnyPS5/pull/2946", commit: "60148c0e", merged: true, description: "Handle null heap" }],
    verified: true,
    notes: "PR merged",
  },
  {
    index: 13,
    description: "ShaderRecompiler::Recompile: static bindless image capacity exceeded",
    error_text: "ShaderRecompiler::Recompile: static bindless image capacity exceeded",
    shader_cache_misses: 733,
    prs: [],
    verified: false,
    notes: "No PR yet",
  },
]

const mockPresets: FirstLightPresetItem[] = [
  { name: "main (no fixes)", applied_prs: [], description: "Base main branch" },
  { name: "stops 1-3 fixed", applied_prs: [2830, 2831, 2946, 1964], description: "Through stop 3" },
  { name: "all merged PRs", applied_prs: [2830, 2831, 2946, 1964, 3134, 2455, 2282, 2463, 2471, 1184, 1893], description: "All PRs" },
]

const mockReport: FirstLightReportResponse = {
  title_id: "PPSA11386",
  title_name: "007 First Light",
  version: "v01.018.000",
  stops: mockStops,
  current_stop: 4,
  passed_stops: 3,
  failed_stops: 9,
  status: "blocked",
  regression_detected: true,
  regression_details: ["Stop 4: expected PRs [3134] not all applied"],
}

const renderComponent = () => {
  return render(
    <BrowserRouter>
      <LumenWorkbenchProvider>
        <FirstLightDiagnostic />
      </LumenWorkbenchProvider>
    </BrowserRouter>
  )
}

describe("FirstLightDiagnostic Component", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getFirstLightStops.mockResolvedValue(mockStops)
    getFirstLightPresets.mockResolvedValue(mockPresets)
    analyzeFirstLight.mockResolvedValue(mockReport)
  })

  it("renders loading state and then displays diagnostic form", async () => {
    renderComponent()
    await waitFor(() => expect(screen.getByText("007 First Light Startup Diagnostic (Issue #2523)")).toBeInTheDocument())
    await waitFor(() => expect(screen.getByText(/Select a preset or enter custom PR numbers/i)).toBeInTheDocument())
    expect(screen.getByRole("combobox")).toBeInTheDocument()
    expect(screen.getByPlaceholderText("e.g., 2830, 2831, 2946, 1964")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Run Analysis" })).toBeInTheDocument()
  })

  it("loads presets into dropdown", async () => {
    renderComponent()
    await waitFor(() => expect(screen.getByRole("combobox")).toBeInTheDocument())
    const select = screen.getByRole("combobox")
    fireEvent.click(select)
    expect(screen.getByText("main (no fixes) — Base main branch")).toBeInTheDocument()
    expect(screen.getByText("stops 1-3 fixed — Through stop 3")).toBeInTheDocument()
    expect(screen.getByText("all merged PRs — All PRs")).toBeInTheDocument()
  })

  it("runs analysis with selected preset and displays report", async () => {
    renderComponent()
    await waitFor(() => expect(screen.getByRole("combobox")).toBeInTheDocument())

    const select = screen.getByRole("combobox")
    fireEvent.click(select)
    fireEvent.change(select, { target: { value: "stops 1-3 fixed" } })

    const runButton = screen.getByRole("button", { name: "Run Analysis" })
    fireEvent.click(runButton)

    await waitFor(() => expect(screen.getByText("BLOCKED")).toBeInTheDocument())
    await waitFor(() => {
      const currentStopLabel = screen.getByText("Current Stop:")
      expect(currentStopLabel.parentElement?.textContent).toMatch(/Current Stop:\s*4\s*\/\s*3/i)
    })
    expect(screen.getByText("Passed:").parentElement?.textContent).toMatch(/Passed:\s*3/)
    expect(screen.getByText("Failed:").parentElement?.textContent).toMatch(/Failed:\s*9/)
    expect(screen.getByText(/⚠ Regression detected:/i)).toBeInTheDocument()

    expect(screen.getByText("Stop 1")).toBeInTheDocument()
    expect(screen.getByText("Stop 13")).toBeInTheDocument()
    expect(screen.getByText("loader: undefined symbol sceSslGetCaList")).toBeInTheDocument()
    expect(screen.getAllByText(/static bindless image capacity exceeded/i).length).toBeGreaterThan(0)

    expect(screen.getByText("#2830")).toBeInTheDocument()
    expect(screen.getByText("#2946")).toBeInTheDocument()

    expect(screen.getAllByText("✓ Verified").length).toBeGreaterThan(0)
    expect(screen.getByText("⟳ Unverified")).toBeInTheDocument()
  })

  it("runs analysis with custom PR input", async () => {
    renderComponent()
    await waitFor(() => expect(screen.getByPlaceholderText("e.g., 2830, 2831, 2946, 1964")).toBeInTheDocument())

    const input = screen.getByPlaceholderText("e.g., 2830, 2831, 2946, 1964")
    fireEvent.change(input, { target: { value: "2830, 2831, 2946, 1964" } })

    const runButton = screen.getByRole("button", { name: "Run Analysis" })
    fireEvent.click(runButton)

    await waitFor(() => expect(screen.getByText("BLOCKED")).toBeInTheDocument())
    await waitFor(() => {
      const currentStopLabel = screen.getByText("Current Stop:")
      expect(currentStopLabel.parentElement?.textContent).toMatch(/4\s*\/\s*3/)
    })
    expect(analyzeFirstLight).toHaveBeenCalledWith([2830, 2831, 2946, 1964])

    await waitFor(() => expect(screen.getByText("BLOCKED")).toBeInTheDocument())
    await waitFor(() => {
      const currentStopLabel = screen.getByText("Current Stop:")
      expect(currentStopLabel.parentElement?.textContent).toMatch(/Current Stop:\s*4\s*\/\s*3/i)
    })
    expect(analyzeFirstLight).toHaveBeenCalledWith([2830, 2831, 2946, 1964])

    await waitFor(() => {
      const statusLabel = screen.getByText("Status:")
      expect(statusLabel.parentElement?.textContent).toMatch(/Status:\s*BLOCKED/i)
    })
    await waitFor(() => {
      const currentStopLabel = screen.getByText("Current Stop:")
      expect(currentStopLabel.parentElement?.textContent).toMatch(/Current Stop:\s*4\s*\/\s*3/i)
    })
    expect(analyzeFirstLight).toHaveBeenCalledWith([2830, 2831, 2946, 1964])
  })

  it("displays error when API call fails", async () => {
    analyzeFirstLight.mockRejectedValueOnce(new Error("Network error"))
    renderComponent()
    await waitFor(() => expect(screen.getByRole("button", { name: "Run Analysis" })).toBeInTheDocument())

    const runButton = screen.getByRole("button", { name: "Run Analysis" })
    fireEvent.click(runButton)

    await waitFor(() => expect(screen.getByText("Error: Network error")).toBeInTheDocument())
  })
})