import React, { useState } from "react"
import { useAuth } from "../hooks"
import { ResolutionReport, analyzeImports, saveImportAnalysis } from "../api"

export const ImportAnalysis: React.FC = () => {
  const { isAuthenticated } = useAuth()
  const [file, setFile] = useState<File | null>(null)
  const [explain, setExplain] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [report, setReport] = useState<ResolutionReport | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState<string | null>(null)

  const exportReport = () => {
    if (!report) return
    const base = report.source_name.replace(/\.[^/.]+$/, "") + "-import-report"
    const a = document.createElement("a")
    a.href = URL.createObjectURL(new Blob([JSON.stringify({ ...report, exported_at: new Date().toISOString() }, null, 2)], { type: "application/json" }))
    a.download = `${base}.json`; a.click()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) { setError("Please select an ELF file to analyze"); return }
    setLoading(true); setError(null)
    try { setReport(await analyzeImports(file, explain)); setSaveMsg(null) }
    catch (err) { setError((err as Error).message) }
    finally { setLoading(false) }
  }

  const handleSave = async () => {
    if (!report) return
    setSaving(true); setSaveMsg(null)
    try { await saveImportAnalysis(report); setSaveMsg("Analysis saved!") }
    catch (err) { setSaveMsg(`Save failed: ${(err as Error).message}`) }
    finally { setSaving(false) }
  }

  if (!isAuthenticated) return <div className="text-center py-8">Please log in to analyze imports.</div>

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">Import Analysis</h2>
      <p className="text-gray-600">Upload a PS5 ELF binary to analyze imports against the host export database.</p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div><label className="block text-sm font-medium text-gray-700 mb-2">ELF Binary File</label>
          <input type="file" accept=".elf,.bin,.so" data-testid="elf-file-input" onChange={e => setFile(e.target.files?.[0] || null)} className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" disabled={loading} required />
        </div>
        {file && <p className="mt-1 text-sm text-gray-500">Selected: {file.name} ({file.size} bytes)</p>}
        <label className="flex items-center gap-2 text-sm text-gray-700"><input type="checkbox" checked={explain} onChange={e => setExplain(e.target.checked)} className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" /> Generate advisory explanation (requires LLM_API_KEY)</label>
        <button type="submit" disabled={loading || !file} className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed">{loading ? "Analyzing..." : "Analyze Imports"}</button>
        {error && <div className="text-red-500">{error}</div>}
      </form>

      {report && (
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <h3 className="text-lg font-semibold">Import Resolution Report</h3>
            <div className="flex gap-2 ml-auto">
              <button onClick={exportReport} className="btn btn-secondary text-sm">Export JSON</button>
              <button onClick={handleSave} disabled={saving} className="btn btn-success text-sm">{saving ? "Saving..." : "Save Analysis"}</button>
            </div>
          </div>
          {saveMsg && <div className="text-sm text-green-600">{saveMsg}</div>}

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg border border-gray-200"><p className="text-sm text-gray-500">Coverage</p><p className="text-3xl font-bold text-blue-600">{(report.coverage*100).toFixed(1)}%</p></div>
            <div className="bg-white p-4 rounded-lg border border-gray-200"><p className="text-sm text-gray-500">Resolved</p><p className="text-3xl font-bold text-green-600">{report.resolved_count}</p></div>
            <div className="bg-white p-4 rounded-lg border border-gray-200"><p className="text-sm text-gray-500">Unresolved</p><p className="text-3xl font-bold text-red-600">{report.unresolved_count}</p></div>
            <div className="bg-white p-4 rounded-lg border border-gray-200"><p className="text-sm text-gray-500">Score</p><p className="text-3xl font-bold text-indigo-600">{report.score}/100</p></div>
          </div>

          {report.blockers.length > 0 && <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4"><h3 className="font-semibold text-yellow-800 mb-2">Top Blockers</h3><ul className="space-y-1">{report.blockers.slice(0, 10).map((b, i) => <li key={i} className="text-sm text-yellow-700 font-mono">{b}</li>)} {report.blockers.length > 10 && <li className="text-sm text-yellow-600">... and {report.blockers.length - 10} more</li>}</ul></div>}


          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden"><h3 className="px-4 py-3 border-b border-gray-200 font-semibold">Import Resolution Details</h3>
            <div className="overflow-x-auto"><table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50"><tr>{["Symbol","NID","Library","Status"].map(h => <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{h}</th>)}</tr></thead>
              <tbody className="bg-white divide-y divide-gray-200">{report.imports.map((imp, i) => <tr key={i} className="hover:bg-gray-50"><td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">{imp.name}</td><td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">0x{imp.nid.toString(16).toUpperCase()}</td><td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{imp.library || "—"}</td><td className="px-6 py-4 whitespace-nowrap"><span className={`px-2 text-xs rounded-full ${imp.status==="resolved"?"bg-green-100 text-green-800":imp.status==="missing-module"?"bg-red-100 text-red-800":"bg-yellow-100 text-yellow-800"}`}>{imp.status}</span></td></tr>)}</tbody>
            </table></div>
          </div>
        </div>
      )}
    </div>
  )
}