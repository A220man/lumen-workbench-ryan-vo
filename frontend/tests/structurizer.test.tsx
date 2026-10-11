import React from "react"
import { render, screen, waitFor, fireEvent } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { StructurizerPanel } from "../src/components/structurizer-panel"
import * as hooks from "../src/hooks"
import * as api from "../src/api"

describe("StructurizerPanel Component", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("renders presets and triggers CFG analysis displaying issue #2642 budget exhaustion", async () => {
    vi.spyOn(hooks, "useAuth").mockReturnValue({
      user: { id: "1", email: "viewer@test.local", name: "Viewer", role: "viewer" },
      token: "dummy-token",
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      checkRole: vi.fn().mockReturnValue(true),
    })

    vi.spyOn(api, "getStructurizerPresets").mockResolvedValue([
      {
        id: "issue-2642-repro",
        name: "Issue #2642 Minimal Reproduction",
        description: "Reproduction graph from AnyPS5 issue #2642",
        adjacency: [[1], [2, 4], [3, 4], [4, 5], [1, 6], [1], []],
        expected_status: "budget_exceeded",
      },
      {
        id: "clean-baseline",
        name: "Clean Structured Baseline",
        description: "Single-latch reducible CFG",
        adjacency: [[1], [2, 3], [4], [4], [1, 5], []],
        expected_status: "clean",
      },
    ])

    vi.spyOn(api, "analyzeCFG").mockResolvedValue({
      name: "Issue #2642 Minimal Reproduction",
      original_blocks: 7,
      current_blocks: 28,
      split_budget: 28,
      exceeded_budget: true,
      matches_issue_2642: true,
      status: "budget_exceeded",
      multi_latch_loops: [
        {
          header: 1,
          latches: [4, 5],
          is_multi_latch: true,
        },
      ],
      selection_conflicts: [
        {
          header: 2,
          merge_block: 4,
          external_preds: [2],
          in_construct_preds: [3],
          shares_latch_edge: true,
        },
      ],
      synthetic_chain_steps: [
        "header=2 merge=4 preds=ext:[2] in:[3] -> split(synth=7)",
        "header=2 merge=5 preds=ext:[2] in:[3] -> split(synth=8)",
      ],
      infinite_recursion_detected: true,
      root_cause: "nested_selection_in_multi_latch_loop_with_shared_merge",
      recommendation: "Decouple loop latch join before Structurize; avoid synthetic splitting on identity branch",
    })

    render(<StructurizerPanel />)

    await waitFor(() => {
      expect(
        screen.getByText("CFG Structurizer Diagnostics (Issue #2642)")
      ).toBeInTheDocument()
    })

    expect(screen.getByText("Issue #2642 Minimal Reproduction")).toBeInTheDocument()
    expect(screen.getByText("Split Budget Exceeded")).toBeInTheDocument()
    expect(screen.getByText(/Loop header 1 has two latches/)).toBeInTheDocument()
    expect(screen.getByText(/nested_selection_in_multi_latch_loop_with_shared_merge/)).toBeInTheDocument()
    expect(screen.getByText(/Decouple loop latch join before Structurize/)).toBeInTheDocument()
  })

  it("handles switching presets", async () => {
    vi.spyOn(hooks, "useAuth").mockReturnValue({
      user: { id: "1", email: "viewer@test.local", name: "Viewer", role: "viewer" },
      token: "dummy-token",
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      checkRole: vi.fn().mockReturnValue(true),
    })

    vi.spyOn(api, "getStructurizerPresets").mockResolvedValue([
      {
        id: "issue-2642-repro",
        name: "Issue #2642 Minimal Reproduction",
        description: "Reproduction graph",
        adjacency: [[1], [2, 4], [3, 4], [4, 5], [1, 6], [1], []],
        expected_status: "budget_exceeded",
      },
      {
        id: "clean-baseline",
        name: "Clean Structured Baseline",
        description: "Clean baseline",
        adjacency: [[1], [2, 3], [4], [4], [1, 5], []],
        expected_status: "clean",
      },
    ])

    const analyzeSpy = vi.spyOn(api, "analyzeCFG").mockResolvedValueOnce({
      name: "Issue #2642 Minimal Reproduction",
      original_blocks: 7,
      current_blocks: 28,
      split_budget: 28,
      exceeded_budget: true,
      matches_issue_2642: true,
      status: "budget_exceeded",
      multi_latch_loops: [],
      selection_conflicts: [],
      synthetic_chain_steps: [],
      infinite_recursion_detected: false,
      root_cause: null,
      recommendation: null,
    }).mockResolvedValueOnce({
      name: "Clean Structured Baseline",
      original_blocks: 6,
      current_blocks: 6,
      split_budget: 24,
      exceeded_budget: false,
      matches_issue_2642: false,
      status: "clean",
      multi_latch_loops: [],
      selection_conflicts: [],
      synthetic_chain_steps: [],
      infinite_recursion_detected: false,
      root_cause: null,
      recommendation: null,
    })

    render(<StructurizerPanel />)

    await waitFor(() => {
      expect(screen.getByText("Clean Structured Baseline")).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText("Clean Structured Baseline"))

    await waitFor(() => {
      expect(screen.getByText("Clean Structured")).toBeInTheDocument()
    })

    expect(analyzeSpy).toHaveBeenCalledTimes(2)
  })
})
