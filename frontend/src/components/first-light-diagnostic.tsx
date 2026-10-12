import React,{useState,useEffect}from"react"
import{useAuth}from"../hooks"
import{StartupStopItem,FirstLightReportResponse,FirstLightPresetItem,getFirstLightStops,getFirstLightPresets,analyzeFirstLight}from"../api"
export const FirstLightDiagnostic:React.FC=()=>{const{isAuthenticated}=useAuth()
const[loading,setLoading]=useState(false);const[error,setError]=useState<string|null>(null)
const[stops,setStops]=useState<StartupStopItem[]>([]);const[presets,setPresets]=useState<FirstLightPresetItem[]>([])
const[selectedPreset,setSelectedPreset]=useState("");const[report,setReport]=useState<FirstLightReportResponse|null>(null)
const[customPRs,setCustomPRs]=useState("")
useEffect(()=>{if(!isAuthenticated)return
Promise.all([getFirstLightStops(),getFirstLightPresets()]).then(([s,p])=>{setStops(s);setPresets(p)}).catch(e=>setError((e as Error).message))},[isAuthenticated])
const handleAnalyze=async()=>{if(!isAuthenticated)return;setLoading(true);setError(null)
try{let prs:number[]|undefined;if(selectedPreset){const p=presets.find(x=>x.name===selectedPreset);if(p)prs=p.applied_prs}
else if(customPRs.trim()){prs=customPRs.split(",").map(s=>parseInt(s.trim(),10)).filter(n=>!isNaN(n))}
setReport(await analyzeFirstLight(prs))}catch(err){setError((err as Error).message)}finally{setLoading(false)}}
if(!isAuthenticated)return<div className="text-center py-8">Please log in to view First Light diagnostics.</div>
return(<div className="space-y-6"><h2 className="text-xl font-bold">007 First Light Startup Diagnostic (Issue #2523)</h2>
<p className="text-gray-600">Analyze the 13-stop startup sequence for PPSA11386 on Linux. Select a preset or enter custom PR numbers.</p>
<div className="space-y-4 p-4 border rounded-lg bg-gray-50"><div><label className="block text-sm font-medium mb-2">Preset Configuration</label>
<select value={selectedPreset} onChange={e=>{setSelectedPreset(e.target.value);setCustomPRs("")}} className="w-full md:w-1/2 px-3 py-2 border rounded">
<option value="">-- Select a preset --</option>{presets.map(p=><option key={p.name} value={p.name}>{p.name} — {p.description}</option>)}</select></div>
<div><label className="block text-sm font-medium mb-2">Or Custom PR Numbers (comma-separated)</label>
<input type="text" value={customPRs} onChange={e=>{setCustomPRs(e.target.value);setSelectedPreset("")}} placeholder="e.g., 2830, 2831, 2946, 1964" className="w-full md:w-1/2 px-3 py-2 border rounded"/></div>
<button onClick={handleAnalyze} disabled={loading} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">{loading?"Analyzing...":"Run Analysis"}</button>
{error&&<p className="text-red-600">Error: {error}</p>}</div>
{report&&(<div className="space-y-6"><div className="p-4 border rounded-lg bg-white"><div className="flex flex-wrap gap-4 items-center">
<div><span className="font-medium">Title:</span> {report.title_name} ({report.title_id})</div>
<div><span className="font-medium">Version:</span> {report.version}</div>
<div><span className="font-medium">Status:</span> <span className={`ml-2 px-2 py-1 rounded text-sm ${report.status==="passed"?"text-green-600 bg-green-100":report.status==="blocked"?"text-red-600 bg-red-100":report.status==="running"?"text-yellow-600 bg-yellow-100":"text-gray-600 bg-gray-100"}`}>{report.status.toUpperCase()}</span></div>
<div><span className="font-medium">Current Stop:</span> {report.current_stop} / {report.stops.length}</div>
<div><span className="font-medium">Passed:</span> {report.passed_stops}</div>
<div><span className="font-medium">Failed:</span> {report.failed_stops}</div>
{report.regression_detected&&<div className="w-full text-red-600"><span className="font-medium">⚠ Regression detected:</span> {report.regression_details.join("; ")}</div>}</div></div>
<div className="space-y-3"><h3 className="font-semibold">Stop Progression</h3>
{report.stops.map(stop=>{const status=stop.index<report.current_stop?"passed":stop.index===report.current_stop?"current":"pending"
const clr={passed:"bg-green-100 text-green-800 border-green-300",current:"bg-blue-100 text-blue-800 border-blue-300",pending:"bg-gray-100 text-gray-600 border-gray-300"}[status]
return(<div key={stop.index} className={`border rounded-lg p-4 ${clr}`}><div className="flex flex-wrap gap-4 items-start">
<div className="flex-1 min-w-[200px]"><div className="font-mono text-sm">Stop {stop.index}</div>
<div className="mt-1 text-sm">{stop.description}</div><div className="mt-1 text-xs text-gray-500 font-mono">{stop.error_text}</div>
{stop.shader_cache_misses!==null&&<div className="mt-1 text-xs text-gray-500">Shader cache misses: {stop.shader_cache_misses}</div>}</div>
<div className="flex-1 min-w-[200px]"><div className="font-medium text-sm">PRs ({stop.prs.length})</div>
{stop.prs.length===0?<div className="text-sm text-gray-500">No PRs yet</div>:(<ul className="mt-1 space-y-1 text-sm">{stop.prs.map(pr=><li key={pr.number} className="flex items-center gap-2">
<a href={pr.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">#{pr.number}</a>
<span className={pr.merged?"text-green-600":"text-yellow-600"}>{pr.merged?"✓ merged":"pending"}</span>
<span className="text-gray-500">({pr.commit.slice(0,8)})</span><span className="text-gray-600">{pr.description}</span></li>)}</ul>)}</div>
<div className="flex-1 min-w-[200px]"><div className="font-medium text-sm">{stop.verified?"✓ Verified":"⟳ Unverified"}</div>
{stop.notes&&<div className="mt-1 text-sm text-gray-600">{stop.notes}</div>}</div></div></div>)})}</div></div>)}</div>)}