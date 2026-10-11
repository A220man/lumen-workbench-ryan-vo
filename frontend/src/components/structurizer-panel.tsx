import React, { useState, useEffect } from "react"
import { useAuth } from "../hooks"
import { CFGDiagnosticReport, CFGPresetItem, getStructurizerPresets, analyzeCFG } from "../api"

export const StructurizerPanel: React.FC = () => {
  const { checkRole } = useAuth()
  const [presets, setPresets] = useState<CFGPresetItem[]>([])
  const [selectedPresetId, setSelectedPresetId] = useState<string>("issue-2642-repro")
  const [report, setReport] = useState<CFGDiagnosticReport | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true)
        const pList = await getStructurizerPresets()
        setPresets(pList)
        if (pList.length > 0) {
          setSelectedPresetId(pList[0].id)
          const res = await analyzeCFG({ name: pList[0].name, adjacency: pList[0].adjacency })
          setReport(res)
        }
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }
    if (checkRole("viewer")) init()
    else setLoading(false)
  }, [checkRole])

  const handleSelectPreset = async (preset: CFGPresetItem) => {
    try {
      setSelectedPresetId(preset.id)
      setLoading(true)
      const res = await analyzeCFG({ name: preset.name, adjacency: preset.adjacency })
      setReport(res)
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  if (loading && !report) return <div className="p-6 text-center text-gray-500 animate-pulse">Loading CFG structurizer diagnostics...</div>
  if (error && !report) return <div className="p-6 text-center text-red-500">Error: {error}</div>

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold text-gray-900">CFG Structurizer Diagnostics (Issue #2642)</h2>
          {report && (
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${report.status === "budget_exceeded" ? "bg-red-100 text-red-800" : "bg-green-100 text-green-800"}`}>
              {report.status === "budget_exceeded" ? "Split Budget Exceeded" : "Clean Structured"}
            </span>
          )}
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Diagnoses control-flow graphs for AnyPS5 Structurizer shared merge splitting loops in multi-latch loops with nested selection joins.
        </p>

        <div className="flex space-x-3 mb-6">
          {presets.map((p) => (
            <button
              key={p.id}
              onClick={() => handleSelectPreset(p)}
              className={`px-3 py-1.5 rounded text-xs font-medium border ${selectedPresetId === p.id ? "bg-blue-50 border-blue-500 text-blue-700" : "bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100"}`}
            >
              {p.name}
            </button>
          ))}
        </div>

        {report && (
          <div className="space-y-4">
            {report.matches_issue_2642 && (
              <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-800">
                <span className="font-bold">Issue #2642 Match: </span>Loop header 1 has two latches (4 and 5) with nested selection merge at block 4. Splitting cannot remove external predecessor 2.
              </div>
            )}

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-3 bg-gray-50 rounded border"><p className="text-xs text-gray-500">Original Blocks</p><p className="text-lg font-bold text-gray-900">{report.original_blocks}</p></div>
              <div className="p-3 bg-gray-50 rounded border"><p className="text-xs text-gray-500">Current Blocks</p><p className="text-lg font-bold text-gray-900">{report.current_blocks}</p></div>
              <div className="p-3 bg-gray-50 rounded border"><p className="text-xs text-gray-500">Split Budget</p><p className="text-lg font-bold text-gray-900">{report.split_budget}</p></div>
              <div className="p-3 bg-gray-50 rounded border"><p className="text-xs text-gray-500">Multi-Latch Loops</p><p className="text-lg font-bold text-gray-900">{report.multi_latch_loops.filter((l) => l.is_multi_latch).length}</p></div>
            </div>

            {report.synthetic_chain_steps.length > 0 && (
              <div className="mt-4">
                <h4 className="text-xs font-semibold text-gray-700 uppercase mb-2">Synthetic Merge Splitting Chain</h4>
                <div className="bg-gray-900 text-gray-100 p-3 rounded font-mono text-xs space-y-1 overflow-x-auto">
                  {report.synthetic_chain_steps.map((step, idx) => (
                    <div key={idx} className="whitespace-nowrap">{step}</div>
                  ))}
                  {report.infinite_recursion_detected && (
                    <div className="text-red-400 font-bold">
                      [FATAL] CFG shared merge splitting exceeded budget: originalBlocks={report.original_blocks} currentBlocks={report.current_blocks} splitBudget={report.split_budget}
                    </div>
                  )}
                </div>
              </div>
            )}

            {report.root_cause && (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded text-xs space-y-2">
                <div><span className="font-semibold text-amber-900">Root Cause: </span><span className="text-amber-800 font-mono">{report.root_cause}</span></div>
                {report.recommendation && <div><span className="font-semibold text-amber-900">Recommendation: </span><span className="text-amber-800">{report.recommendation}</span></div>}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
