import React from "react"
import { render, screen, fireEvent } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { ImportAnalysis } from "../src/components/import-analysis"
import * as hooks from "../src/hooks"
import { MemoryRouter } from "react-router-dom"

describe("ImportAnalysis Component", () => {
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
        <ImportAnalysis />
      </MemoryRouter>
    )

    expect(screen.getByText("Please log in to analyze imports.")).toBeInTheDocument()
  })

  it("renders upload form when authenticated", () => {
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

    render(
      <MemoryRouter>
        <ImportAnalysis />
      </MemoryRouter>
    )

    expect(screen.getByText("Import Analysis")).toBeInTheDocument()
    expect(screen.getByText(/Upload a PS5 ELF binary/i)).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Analyze Imports" })).toBeDisabled()

    const fileInput = screen.getByTestId("elf-file-input") as HTMLInputElement
    const file = new File(["fake elf content"], "test.elf", { type: "application/octet-stream" })
    fireEvent.change(fileInput, { target: { files: [file] } })

    expect(screen.getAllByText((_, element) => element.textContent?.includes("Selected:") ?? false).length).toBeGreaterThan(0)
    expect(screen.getByRole("button", { name: "Analyze Imports" })).not.toBeDisabled()
  })

  it("keeps analyze button disabled when no file selected", () => {
    vi.spyOn(hooks, "useAuth").mockReturnValue({
      user: { id: "user-1", email: "test@test.com", name: "Test", role: "operator" },
      token: "dummy-token",
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      checkRole: vi.fn().mockReturnValue(true),
    })

    render(
      <MemoryRouter>
        <ImportAnalysis />
      </MemoryRouter>
    )

    expect(screen.getByRole("button", { name: "Analyze Imports" })).toBeDisabled()
  })
})