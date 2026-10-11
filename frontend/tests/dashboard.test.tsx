import React from "react"
import { render, screen, waitFor } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { Dashboard } from "../src/components/dashboard"
import * as hooks from "../src/hooks"
import { apiClient } from "../src/api"
import { MemoryRouter } from "react-router-dom"

describe("Dashboard Component", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("prompts to log in when user is not authenticated", () => {
    vi.spyOn(hooks, "useAuth").mockReturnValue({
      user: null,
      token: null,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      checkRole: vi.fn().mockReturnValue(false),
    })

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    )

    expect(screen.getByText("Please log in to view titles.")).toBeInTheDocument()
  })

  it("renders titles list successfully when authenticated", async () => {
    vi.spyOn(hooks, "useAuth").mockReturnValue({
      user: {
        id: "user-1",
        email: "ryan@test.local",
        name: "Ryan Vo",
        role: "operator",
      },
      token: "dummy-token",
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      checkRole: vi.fn().mockReturnValue(true),
    })

    vi.spyOn(apiClient, "get").mockResolvedValue({
      data: [
        {
          id: 101,
          name: "Bloodborne PS5 Remaster",
          description: "Porting analysis test target",
          status: "active",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-02T00:00:00Z",
          is_active: true,
        },
      ],
    })

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText("Bloodborne PS5 Remaster")).toBeInTheDocument()
    })
    expect(screen.getByText("Your Titles (1)")).toBeInTheDocument()
    expect(screen.getByText("Import New Title")).toBeInTheDocument()
  })
})
