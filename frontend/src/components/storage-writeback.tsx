import React, { useState, useEffect } from "react"
import { useAuth } from "../hooks"
import { StorageWritebackReport, StoragePresetItem, getStorageWritebackPresets, simulateStorageWriteback } from "../api"

export const StorageWritebackPanel: React.FC = () => {
  const { checkRole } = useAuth()
  const [presets, setPresets] = useState<StoragePresetItem[]>([])
  const [selectedPresetId, setSelectedPresetId] = useState<string>("silksong-sdf-atlas")
  const [report, setReport] = useState<StorageWritebackReport | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true)
        const pList = await getStorageWritebackPresets()
        setPresets(pList)
        if (pList.length > 0) {
          setSelectedPresetId(pList[0].id)
          const res = await simulateStorageWriteback({ texture_address: pList[0].texture_address, texture_size: pList[0].texture_size })
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

  const handleSelectPreset = async (preset: StoragePresetItem) => {
    try {
      setSelectedPresetId(preset.id)
      setLoading(true)
      const res = await simulateStorageWriteback({ texture_address: preset.texture_address, texture_size: preset.texture_size })
      setReport(res)
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  if (loading && !report) return <div className="p-6 text-center text-gray-500 animate-pulse">Loading storage write-back diagnostics...</div>
  if (error && !report) return <div className="p-6 text-center text-red-500">Error: {error}</div>

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold text-gray-900">Storage Texture Write-Back Diagnostics (Issue #865)</h2>
          {report && (
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${report.status === "conflict_detected" ? "bg-red-100 text-red-800" : "bg-green-100 text-green-800"}`}>
              {report.status === "conflict_detected" ? "Conflict Detected (Boxes in Menu Text)" : "Clean Write-Back (Zero Corruption)"}
            </span>
          )}
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Models 64 KiB block vs 4 KiB page granularity write-back cache conflict detection for unaligned GPU storage textures in Hollow Knight: Silksong (PPSA12544).
        </p>

        <div className="flex space-x-3 mb-6">
          {presets.map((p) => (
            <button key={p.id} onClick={() => handleSelectPreset(p)} className={`px-3 py-1.5 rounded text-xs font-medium border ${selectedPresetId === p.id ? "bg-blue-50 border-blue-500 text-blue-700" : "bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100"}`}>
              {p.name}
            </button>
          ))}
        </div>

        {report && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-3 bg-gray-50 rounded border"><p className="text-xs text-gray-500">Texture Address</p><p className="text-sm font-mono font-bold text-gray-900">{report.texture_address}</p></div>
              <div className="p-3 bg-gray-50 rounded border"><p className="text-xs text-gray-500">Alignment Offset</p><p className="text-sm font-mono font-bold text-gray-900">{report.alignment_offset}</p></div>
              <div className="p-3 bg-gray-50 rounded border"><p className="text-xs text-gray-500">64 KiB Blocks Spanned</p><p className="text-sm font-bold text-gray-900">{report.total_blocks_spanned}</p></div>
              <div className="p-3 bg-gray-50 rounded border"><p className="text-xs text-gray-500">Edge Blocks Count</p><p className="text-sm font-bold text-gray-900">{report.edge_blocks_count}</p></div>
            </div>

            {report.warning_logged && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded text-xs font-mono text-amber-900">
                <span className="font-bold">Driver Warning: </span>{report.warning_logged}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className={`p-4 rounded border ${report.block_policy_corrupted ? "bg-red-50 border-red-200" : "bg-gray-50"}`}>
                <h4 className="font-semibold text-xs text-gray-900 mb-1">64 KiB Block Policy (Legacy)</h4>
                <p className="text-xs text-gray-600 mb-2">Unit: 64 KiB block</p>
                <p className="text-xs font-bold text-red-700">{report.block_policy_corrupted ? "DROPPED (Corrupted into Solid Boxes)" : "PRESERVED"}</p>
                {report.corrupted_glyphs.length > 0 && <p className="text-[11px] text-red-600 mt-1 font-mono">Affected glyphs: {report.corrupted_glyphs.join(", ")}</p>}
              </div>
              <div className="p-4 rounded border bg-green-50 border-green-200">
                <h4 className="font-semibold text-xs text-green-900 mb-1">4 KiB Page Policy (Refined)</h4>
                <p className="text-xs text-green-700 mb-2">Unit: 4 KiB page</p>
                <p className="text-xs font-bold text-green-800">PRESERVED (Zero Edge Drops)</p>
                <p className="text-[11px] text-green-700 mt-1">Filters out adjacent heap stamps</p>
              </div>
              <div className="p-4 rounded border bg-blue-50 border-blue-200">
                <h4 className="font-semibold text-xs text-blue-900 mb-1">Eager Write-Back (Workaround)</h4>
                <p className="text-xs text-blue-700 mb-2">APS5_EAGER_WRITEBACK=1</p>
                <p className="text-xs font-bold text-blue-800">PRESERVED (Immediate Flush)</p>
                <p className="text-[11px] text-blue-700 mt-1">Flushes before CPU race</p>
              </div>
            </div>

            <div className="p-4 bg-gray-50 border rounded text-xs space-y-2">
              <div><span className="font-semibold text-gray-900">Root Cause: </span><span className="text-gray-700">{report.root_cause}</span></div>
              <div><span className="font-semibold text-gray-900">Recommendation: </span><span className="text-gray-700">{report.recommendation}</span></div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
