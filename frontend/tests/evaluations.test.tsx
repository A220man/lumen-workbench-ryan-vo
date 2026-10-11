import React from "react"
import { render, screen, waitFor } from "@testing-library/react"
import { describe, it, expect, vi } from "vitest"
import { EvaluationTable } from "../src/components/evaluation-table"
import * as hooks from "../src/hooks"
import { apiClient } from "../src/api"
import { MemoryRouter } from "react-router-dom"

describe("EvaluationTable Component", () => {
  it("renders empty evaluations message when list is empty", async () => {
    vi.spyOn(hooks, "useAuth").mockReturnValue({
      user: { id: "1", email: "op@test.local", name: "Operator", role: "operator" },
      token: "dummy",
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      checkRole: vi.fn().mockReturnValue(true),
    })

    vi.spyOn(apiClient, "get").mockResolvedValue({ data: [] })

    render(
      <MemoryRouter>
        <EvaluationTable />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText("Add First Evaluation")).toBeInTheDocument()
    })
  })

  it("renders evaluations list when data is available", async () => {
    vi.spyOn(hooks, "useAuth").mockReturnValue({
      user: { id: "1", email: "op@test.local", name: "Operator", role: "operator" },
      token: "dummy",
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      checkRole: vi.fn().mockReturnValue(true),
    })

    vi.spyOn(apiClient, "get").mockResolvedValue({
      data: [
        {
          id: 1,
          title_id: 42,
          score: 8.5,
          comments: "High coverage in libkernel exports",
          created_at: "2026-03-01T12:00:00Z",
          updated_at: "2026-03-01T12:00:00Z",
        },
      ],
    })

    render(
      <MemoryRouter>
        <EvaluationTable />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText("8.5")).toBeInTheDocument()
    })
    expect(screen.getByText("High coverage in libkernel exports")).toBeInTheDocument()
  })
})
