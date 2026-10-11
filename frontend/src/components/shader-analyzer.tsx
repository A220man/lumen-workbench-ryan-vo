import React, { useState, useEffect } from "react"
import { useAuth } from "../hooks"
import { BitfieldLayoutItem, ShaderAnalysisResponse, getRDNA2Layout, getStrayShadersBatch, analyzeShader } from "../api"

export const ShaderAnalyzerPanel: React.FC = () => {
  const { checkRole } = useAuth()
  const [layout, setLayout] = useState<BitfieldLayoutItem[]>([])
  const [strayShaders, setStrayShaders] = useState<ShaderAnalysisResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sampleId, setSampleId] = useState(2)
  const [layer, setLayer] = useState(4)
  const [decodedResult, setDecodedResult] = useState<ShaderAnalysisResponse | null>(null)

  useEffect(() => {
    if (!checkRole("viewer")) { setLoading(false); return }
    Promise.all([getRDNA2Layout(), getStrayShadersBatch()])
      .then(([l, b]) => { setLayout(l); setStrayShaders(b); setError(null) })
      .catch(e => setError((e as Error).message))
      .finally(() => setLoading(false))
  }, [checkRole])

  const handleRebuildAndDecode = async () => {
    try {
      const rawWord = ((sampleId & 0xf) << 8) | ((layer & 0x7ff) << 16)
      const res = await analyzeShader({
        shader_address: "0x1000_interactive", title_id: "INTERACTIVE", ancillary_vgpr: "v4",
        instructions: [
          { index: 0, opcode: "BitFieldUExtract", dest: "v0", sources: ["v4"], bit_offset: 16, bit_length: 11 },
          { index: 1, opcode: "BitFieldUExtract", dest: "v1", sources: ["v4"], bit_offset: 8, bit_length: 4 },
        ],
        raw_word: rawWord,
      })
      setDecodedResult(res)
    } catch (err) { setError((err as Error).message) }
  }

  if (loading) return <div className="p-6 text-center text-gray-500 animate-pulse">Loading shader diagnostics...</div>
  if (error) return <div className="p-6 text-center text-red-500">Error: {error}</div>

  const rawReconstructed = ((sampleId & 0xf) << 8) | ((layer & 0x7ff) << 16)

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h2 className="text-xl font-bold text-gray-900 mb-2">RDNA2 Shader Recompiler Diagnostics (Issue #2548)</h2>
        <p className="text-sm text-gray-600 mb-4">
          Models RDNA2 packed pixel ancillary register bitfield extraction (render target index and sample index) and detects register reuse patterns triggering unsupported live use errors in UE4 shaders.
        </p>
        <div className="mt-4">
          <h3 className="text-md font-semibold text-gray-800 mb-2">RDNA2 Ancillary Register (v4) Bit Layout</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>{["Field", "Bits", "Length", "Status", "Vulkan Mapping"].map(h => <th key={h} className="px-4 py-2 text-left text-gray-500">{h}</th>)}</tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {layout.map(item => (
                  <tr key={item.name}>
                    <td className="px-4 py-2 font-mono text-gray-900">{item.name}</td>
                    <td className="px-4 py-2 text-gray-600">[{item.offset}..{item.offset + item.length - 1}]</td>
                    <td className="px-4 py-2 text-gray-600">{item.length} bits</td>
                    <td className="px-4 py-2"><span className={`px-2 py-0.5 text-xs rounded ${item.modeled ? "bg-green-100 text-green-800" : "bg-amber-100 text-amber-800"}`}>{item.modeled ? "Modelled (PR #1179)" : "Unmodelled"}</span></td>
                    <td className="px-4 py-2 text-gray-600 font-mono text-xs">{item.source_builtin || "None"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-4">
        <h3 className="text-md font-semibold text-gray-800">Interactive PR #1179 Bitfield Reconstruction</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-700">Sample Index (0-15)</label>
            <input type="number" min={0} max={15} value={sampleId} onChange={e => setSampleId(Number(e.target.value))} className="mt-1 block w-full rounded border p-2 text-sm" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700">Render Target Layer (0-2047)</label>
            <input type="number" min={0} max={2047} value={layer} onChange={e => setLayer(Number(e.target.value))} className="mt-1 block w-full rounded border p-2 text-sm" />
          </div>
          <div className="flex items-end">
            <button onClick={handleRebuildAndDecode} className="w-full bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 font-medium">Reconstruct & Decode</button>
          </div>
        </div>
        <div className="p-3 bg-gray-50 rounded border text-sm font-mono flex items-center justify-between">
          <span>Reconstructed Ancillary Word:</span>
          <span className="font-bold text-blue-700">0x{rawReconstructed.toString(16).padStart(8, "0").toUpperCase()}</span>
        </div>
        {decodedResult?.decoded_word && (
          <div className="p-3 bg-blue-50 border border-blue-200 rounded text-xs space-y-1">
            <p className="font-semibold text-blue-900">Decoded Bitfield Values:</p>
            <p>• Sample Index (bits 8-11): {decodedResult.decoded_word.sample_index?.value}</p>
            <p>• Render Target Layer (bits 16-26): {decodedResult.decoded_word.render_target_index?.value}</p>
            <p className="text-gray-500">• Rebuild Status: {decodedResult.status}</p>
          </div>
        )}
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-md font-semibold text-gray-800">Stray (PPSA02100 v1.05) UE4 Pixel Shaders ({strayShaders.length})</h3>
          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-800">Deferred on Issue #2548</span>
        </div>
        <div className="max-h-64 overflow-y-auto divide-y divide-gray-100 border rounded">
          {strayShaders.map(s => (
            <div key={s.shader_address} className="p-3 text-xs flex justify-between hover:bg-gray-50">
              <div>
                <span className="font-mono font-bold text-gray-900">{s.shader_address}</span>
                <span className="ml-2 text-gray-500 font-mono">VGPR: {s.ancillary_vgpr}</span>
                <p className="text-red-600 mt-0.5">{s.rejection_reason}</p>
              </div>
              <div className="text-right">
                <span className="px-2 py-0.5 rounded text-xs bg-red-50 text-red-700 font-medium">{s.status}</span>
                <p className="text-gray-400 text-[10px] mt-0.5">Flow: {s.live_use_chain.slice(0, 3).join(" → ")}...</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
