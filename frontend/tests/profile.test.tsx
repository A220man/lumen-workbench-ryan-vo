import React from "react"
import { render, screen } from "@testing-library/react"
import { describe, it, expect, vi } from "vitest"
import { ProfilePanel } from "../src/components/profile"
import * as hooks from "../src/hooks"

describe("ProfilePanel Component", () => {
  it("renders empty state when no user is logged in", () => {
    vi.spyOn(hooks, "useAuth").mockReturnValue({
      user: null,
      token: null,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      checkRole: vi.fn().mockReturnValue(false),
    })

    render(<ProfilePanel />)
    expect(screen.getByText("No user logged in")).toBeInTheDocument()
  })

  it("renders user information and role badge when logged in", () => {
    const mockLogout = vi.fn()
    vi.spyOn(hooks, "useAuth").mockReturnValue({
      user: {
        id: "user-123",
        email: "ryan@test.local",
        name: "Ryan Vo",
        role: "operator",
      },
      token: "dummy-token",
      isAuthenticated: true,
      login: vi.fn(),
      logout: mockLogout,
      checkRole: vi.fn().mockReturnValue(true),
    })

    render(<ProfilePanel />)
    expect(screen.getByText("Ryan Vo")).toBeInTheDocument()
    expect(screen.getByText("Operator")).toBeInTheDocument()
    expect(screen.getByText("Logout")).toBeInTheDocument()
  })
})
