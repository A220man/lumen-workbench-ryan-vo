import React, { useState, useEffect } from "react"
import { useAuth } from "../hooks"
import {
  GpuDeviceProfile, IntelGpuDiagnosticReport,
  getIntelGpuProfiles, getIntelGpuDiagnostics, simulateIntelGpuTest,
} from "../api"

export const IntelGpuPanel: React.FC = () => {
  const { checkRole } = useAuth()
  const [profiles, setProfiles] = useState<GpuDeviceProfile[]>([])
  const [selectedGpu, setSelectedGpu] = useState("intel_uhd_770")
  const [applyFixes, setApplyFixes] = useState(false)
  const [report, setReport] = useState<IntelGpuDiagnosticReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = async (gpuId: string, fixes: boolean) => {
    try {
      setLoading(true)
      const data = await getIntelGpuDiagnostics(gpuId, fixes)
      setReport(data); setError(null)
    } catch (err) { setError((err as Error).message) }
    finally { setLoading(false) }
  }

  useEffect(() => {
    if (!checkRole("viewer")) { setLoading(false); return }
    getIntelGpuProfiles().then(p => {
      setProfiles(p)
      const g = p[0]?.gpu_id || "intel_uhd_770"
      setSelectedGpu(g)
      return getIntelGpuDiagnostics(g, false)
    }).then(d => { setReport(d); setError(null) })
      .catch(e => setError((e as Error).message))
      .finally(() => setLoading(false))
  }, [checkRole])

  const handleSimulate = async (tid: string) => {
    try {
      const res = await simulateIntelGpuTest({ test_id: tid, gpu_id: selectedGpu, apply_fix: !applyFixes })
      alert(`Simulation ${tid}: ${res.status.toUpperCase()} (${res.observed_output})`)
    } catch (err) { setError((err as Error).message) }
  }

  if (loading && !report) return <div className="p-6 text-center text-gray-500 animate-pulse">Loading Intel GPU diagnostics...</div>
  if (error && !report) return <div className="p-6 text-center text-red-500">Error: {error}</div>

  const isFailed = report && report.baseline_failed > 0 && !applyFixes

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold text-gray-900">Intel UHD 770 Execution Diagnostics (Issue #2114)</h2>
          {report && (
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${isFailed ? "bg-red-100 text-red-800" : "bg-green-100 text-green-800"}`}>
              {isFailed ? `${report.baseline_failed} Failures Detected` : "Clean"}
            </span>
          )}
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Models 4 failing execution tests on Intel UHD 770 vs RTX 4080: VOP1 fract 1-ULP drift, SDWA byte leak, f16 unordered NaN compare, and 64-bit atomics.
        </p>
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div className="flex space-x-2">
            {profiles.map(p => (
              <button key={p.gpu_id} onClick={() => { setSelectedGpu(p.gpu_id); loadData(p.gpu_id, applyFixes) }} className={`px-3 py-1.5 rounded text-xs border ${selectedGpu === p.gpu_id ? "bg-blue-50 border-blue-500 text-blue-700 font-bold" : "bg-gray-50 text-gray-600"}`}>
                {p.name}
              </button>
            ))}
          </div>
          <label className="flex items-center space-x-2 text-xs cursor-pointer bg-gray-50 px-3 py-1.5 rounded border">
            <input type="checkbox" checked={applyFixes} onChange={() => { const n = !applyFixes; setApplyFixes(n); loadData(selectedGpu, n) }} />
            <span>Apply Workbench Fixes (PR #1250, SDWA mask, Unordered NaN, Caps check)</span>
          </label>
        </div>
        {report && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
              {[["Device:", report.device_id, "font-mono"], ["Driver:", report.driver_version, ""], ["Int64 Atomics:", report.has_int64_atomics ? "Yes" : "No", ""], ["Passing:", `${report.baseline_passed}/${report.total_diagnosed}`, ""]].map(([lbl, val, cls]) => (
                <div key={lbl} className="p-2 bg-gray-50 rounded border"><span className="text-gray-500">{lbl}</span> <span className={`font-bold ${cls}`}>{val}</span></div>
              ))}
            </div>
            <div className="space-y-2">
              {report.diagnostics.map(d => (
                <div key={d.test_id} className={`p-3 rounded border text-xs ${d.status === "failed" ? "bg-red-50 border-red-200" : "bg-green-50 border-green-200"}`}>
                  <div className="flex justify-between font-mono font-bold mb-1">
                    <span>{d.test_name}</span>
                    <span className={d.status === "failed" ? "text-red-700" : "text-green-700"}>{d.status.toUpperCase()}</span>
                  </div>
                  <div className="font-mono text-gray-700 bg-white p-2 rounded border mb-1">
                    <div>Observed: <span className={d.status === "failed" ? "text-red-600 font-bold" : "text-green-600"}>{d.observed_output}</span> {d.ulp_drift ? `(${d.ulp_drift} ULP drift)` : ""}</div>
                    <div>Expected: {d.expected_output}</div>
                  </div>
                  <div className="text-gray-600">Cause: {d.root_cause}</div>
                  <div className="text-blue-700">Fix: {d.resolution}</div>
                  <div className="mt-1 text-right">
                    <button onClick={() => handleSimulate(d.test_id)} className="text-blue-600 hover:underline">Simulate Single →</button>
                  </div>
                </div>
              ))}
            </div>
            {report.recommendations.length > 0 && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded text-xs space-y-1">
                <p className="font-bold text-blue-900">Action Recommendations:</p>
                {report.recommendations.map((r, i) => <p key={i} className="text-blue-800">• {r}</p>)}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
