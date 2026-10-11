import React from "react"
import { render, screen, waitFor } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { StatusPanel } from "../src/components/status"
import * as hooks from "../src/hooks"
import { apiClient } from "../src/api"

describe("StatusPanel Component", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("renders system telemetry metrics when authenticated", async () => {
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
        active_titles: 7,
        total_imports: 42,
        resolution_rate: "94.5%",
        evaluation_count: 12,
      },
    })

    render(<StatusPanel />)

    await waitFor(() => {
      expect(screen.getByText("System Status")).toBeInTheDocument()
    })
    expect(screen.getByText("7")).toBeInTheDocument()
    expect(screen.getByText("42")).toBeInTheDocument()
    expect(screen.getByText("94.5%")).toBeInTheDocument()
    expect(screen.getByText("12")).toBeInTheDocument()
  })

  it("handles API error state gracefully", async () => {
    vi.spyOn(hooks, "useAuth").mockReturnValue({
      user: { id: "1", email: "viewer@test.local", name: "Viewer", role: "viewer" },
      token: "dummy-token",
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      checkRole: vi.fn().mockReturnValue(true),
    })

    vi.spyOn(apiClient, "get").mockRejectedValue(new Error("Telemetry service unavailable"))

    render(<StatusPanel />)

    await waitFor(() => {
      expect(screen.getByText("Error: Telemetry service unavailable")).toBeInTheDocument()
    })
  })
})
