import React from "react"
import { render, screen, waitFor } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { AnalyticsPanel } from "../src/components/analytics"
import * as hooks from "../src/hooks"
import { apiClient } from "../src/api"

describe("AnalyticsPanel Component", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("renders analytics metrics when authenticated", async () => {
    vi.spyOn(hooks, "useAuth").mockReturnValue({
      user: { id: "1", email: "viewer@test.local", name: "Viewer", role: "viewer" },
      token: "dummy-token",
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      checkRole: vi.fn().mockReturnValue(true),
    })

    vi.spyOn(apiClient, "get").mockResolvedValue({
      data: {
        resolution_by_library: "Lead module: libkernel (31 symbols)",
        performance_trend: "F1=0.985 (coverage 97.2%)",
        import_volume: "42 records analyzed",
      },
    })

    render(<AnalyticsPanel />)

    await waitFor(() => {
      expect(screen.getByText("Analytics")).toBeInTheDocument()
    })
    expect(screen.getByText("Lead module: libkernel (31 symbols)")).toBeInTheDocument()
    expect(screen.getByText("F1=0.985 (coverage 97.2%)")).toBeInTheDocument()
    expect(screen.getByText("42 records analyzed")).toBeInTheDocument()
  })

  it("handles empty analytics response", async () => {
    vi.spyOn(hooks, "useAuth").mockReturnValue({
      user: { id: "1", email: "viewer@test.local", name: "Viewer", role: "viewer" },
      token: "dummy-token",
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      checkRole: vi.fn().mockReturnValue(true),
    })

    vi.spyOn(apiClient, "get").mockResolvedValue({ data: null })

    render(<AnalyticsPanel />)

    await waitFor(() => {
      expect(screen.getByText("No analytics data")).toBeInTheDocument()
    })
  })

  it("renders adversarial stability metric when present", async () => {
    vi.spyOn(hooks, "useAuth").mockReturnValue({
      user: { id: "1", email: "viewer@test.local", name: "Viewer", role: "viewer" },
      token: "dummy-token",
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      checkRole: vi.fn().mockReturnValue(true),
    })

    vi.spyOn(apiClient, "get").mockResolvedValue({
      data: {
        resolution_by_library: "Lead module: libkernel (31 symbols)",
        performance_trend: "F1=0.985 (coverage 97.2%)",
        import_volume: "42 records analyzed",
        adversarial_stability: "100.0% stability (19/19 boundary probes)",
      },
    })

    render(<AnalyticsPanel />)

    await waitFor(() => {
      expect(screen.getByText("Adversarial Stability")).toBeInTheDocument()
    })
    expect(screen.getByText("100.0% stability (19/19 boundary probes)")).toBeInTheDocument()
  })
})
