import React, { useState, useEffect } from "react"
import { useAuth } from "../hooks"
import { StorageWritebackReport, StoragePresetItem, getStorageWritebackPresets, simulateStorageWriteback } from "../api"

export const StorageWritebackPanel: React.FC = () => {
  const { checkRole } = useAuth()
  const [presets, setPresets] = useState<StoragePresetItem[]>([])
  const [selectedPresetId, setSelectedPresetId] = useState("silksong-sdf-atlas")
  const [report, setReport] = useState<StorageWritebackReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!checkRole("viewer")) { setLoading(false); return }
    getStorageWritebackPresets().then(pList => {
      setPresets(pList)
      if (pList.length > 0) {
        setSelectedPresetId(pList[0].id)
        return simulateStorageWriteback({ texture_address: pList[0].texture_address, texture_size: pList[0].texture_size })
      }
    }).then(res => { if (res) setReport(res) })
      .catch(err => setError((err as Error).message))
      .finally(() => setLoading(false))
  }, [checkRole])

  const handleSelectPreset = async (preset: StoragePresetItem) => {
    try { setSelectedPresetId(preset.id); setLoading(true)
      const res = await simulateStorageWriteback({ texture_address: preset.texture_address, texture_size: preset.texture_size })
      setReport(res); setError(null)
    } catch (err) { setError((err as Error).message) }
    finally { setLoading(false) }
  }

  if (loading && !report) return <div className="p-6 text-center text-gray-500 animate-pulse">Loading storage write-back diagnostics...</div>
  if (error && !report) return <div className="p-6 text-center text-red-500">Error: {error}</div>

  const isConflict = report?.status === "conflict_detected"

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold text-gray-900">Storage Write-Back Diagnostics (Issue #865)</h2>
          {report && <span className={`px-3 py-1 rounded-full text-xs font-semibold ${isConflict ? "bg-red-100 text-red-800" : "bg-green-100 text-green-800"}`}>
            {isConflict ? "Conflict Detected (Boxes in Menu Text)" : "Clean Write-Back (Zero Corruption)"}
          </span>}
        </div>
        <p className="text-sm text-gray-600 mb-4">Models 64 KiB block vs 4 KiB page write-back conflict detection for unaligned GPU storage textures in Silksong (PPSA12544).</p>
        <div className="flex space-x-3 mb-6">
          {presets.map(p => (
            <button key={p.id} onClick={() => handleSelectPreset(p)} className={`px-3 py-1.5 rounded text-xs font-medium border ${selectedPresetId === p.id ? "bg-blue-50 border-blue-500 text-blue-700" : "bg-gray-50 text-gray-600"}`}>
              {p.name}
            </button>
          ))}
        </div>
        {report && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
              {[["Texture Address", report.texture_address, true], ["Alignment Offset", report.alignment_offset, true], ["Blocks Spanned", report.total_blocks_spanned, false], ["Edge Blocks", report.edge_blocks_count, false]].map(([lbl, val, mono], idx) => (
                <div key={idx} className="p-3 bg-gray-50 rounded border"><p className="text-gray-500">{lbl}</p><p className={`font-bold ${mono ? "font-mono" : ""}`}>{val}</p></div>
              ))}
            </div>
            {report.warning_logged && <div className="p-3 bg-amber-50 border border-amber-200 rounded text-xs font-mono text-amber-900">{report.warning_logged}</div>}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className={`p-4 rounded border ${report.block_policy_corrupted ? "bg-red-50 border-red-200" : "bg-gray-50"}`}>
                <h4 className="font-semibold mb-1">64 KiB Block Policy (Legacy)</h4>
                <p className="font-bold text-red-700">{report.block_policy_corrupted ? "DROPPED (Corrupted into Solid Boxes)" : "PRESERVED"}</p>
                {report.corrupted_glyphs.length > 0 && <p className="text-[11px] text-red-600 mt-1 font-mono">Affected glyphs: {report.corrupted_glyphs.join(", ")}</p>}
              </div>
              <div className="p-4 rounded border bg-green-50 border-green-200">
                <h4 className="font-semibold text-green-900 mb-1">4 KiB Page Policy (Refined)</h4>
                <p className="font-bold text-green-800">PRESERVED (Zero Edge Drops)</p>
                <p className="text-[11px] text-green-700 mt-1">Filters out adjacent heap stamps</p>
              </div>
              <div className="p-4 rounded border bg-blue-50 border-blue-200">
                <h4 className="font-semibold text-blue-900 mb-1">Eager Write-Back (Workaround)</h4>
                <p className="font-bold text-blue-800">PRESERVED (Immediate Flush)</p>
                <p className="text-[11px] text-blue-700 mt-1">APS5_EAGER_WRITEBACK=1</p>
              </div>
            </div>
            <div className="p-4 bg-gray-50 border rounded text-xs space-y-1">
              <div><span className="font-semibold">Root Cause: </span><span>{report.root_cause}</span></div>
              <div><span className="font-semibold">Recommendation: </span><span>{report.recommendation}</span></div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}