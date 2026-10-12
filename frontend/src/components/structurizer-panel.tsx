import React,{useState,useEffect}from"react"
import{useAuth}from"../hooks"
import{CFGDiagnosticReport,CFGPresetItem,getStructurizerPresets,analyzeCFG}from"../api"

export const StructurizerPanel:React.FC=()=>{
  const{checkRole}=useAuth()
  const[presets,setPresets]=useState<CFGPresetItem[]>([])
  const[selectedPresetId,setSelectedPresetId]=useState("issue-2642-repro")
  const[report,setReport]=useState<CFGDiagnosticReport|null>(null)
  const[loading,setLoading]=useState(true)
  const[error,setError]=useState<string|null>(null)

  useEffect(()=>{
    if(!checkRole("viewer")){setLoading(false);return}
    getStructurizerPresets().then(pList=>{
      setPresets(pList)
      if(pList.length>0){
        setSelectedPresetId(pList[0].id)
        return analyzeCFG({name:pList[0].name,adjacency:pList[0].adjacency})
      }
    }).then(res=>{if(res)setReport(res)}).catch(err=>setError((err as Error).message)).finally(()=>setLoading(false))
  },[checkRole])

  const handleSelectPreset=async(preset:CFGPresetItem)=>{
    try{setSelectedPresetId(preset.id);setLoading(true)
      const res=await analyzeCFG({name:preset.name,adjacency:preset.adjacency})
      setReport(res);setError(null)}catch(err){setError((err as Error).message)}
    finally{setLoading(false)}
  }

  if(loading&&!report)return<div className="p-6 text-center text-gray-500 animate-pulse">Loading CFG structurizer diagnostics...</div>
  if(error&&!report)return<div className="p-6 text-center text-red-500">Error: {error}</div>

  const isExceeded=report?.status==="budget_exceeded"

  return(
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold text-gray-900">CFG Structurizer Diagnostics (Issue #2642)</h2>
          {report&&<span className={`px-3 py-1 rounded-full text-xs font-semibold ${isExceeded?"bg-red-100 text-red-800":"bg-green-100 text-green-800"}`}>{isExceeded?"Split Budget Exceeded":"Clean Structured"}</span>}
        </div>
        <p className="text-sm text-gray-600 mb-4">Diagnoses control-flow graphs for AnyPS5 Structurizer shared merge splitting loops in multi-latch loops with nested selection joins.</p>
        <div className="flex space-x-3 mb-6">{presets.map(p=>(<button key={p.id} onClick={()=>handleSelectPreset(p)} className={`px-3 py-1.5 rounded text-xs font-medium border ${selectedPresetId===p.id?"bg-blue-50 border-blue-500 text-blue-700":"bg-gray-50 text-gray-600"}`}>{p.name}</button>))}</div>
        {report&&(
          <div className="space-y-4">
            {report.matches_issue_2642&&(
              <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-800">
                <span className="font-bold">Issue #2642 Match: </span>Loop header 1 has two latches (4 and 5) with nested selection merge at block 4. Splitting cannot remove external predecessor 2.
              </div>
            )}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
              {[["Original Blocks",report.original_blocks],["Current Blocks",report.current_blocks],["Split Budget",report.split_budget],["Multi-Latch Loops",report.multi_latch_loops.filter(l=>l.is_multi_latch).length]].map(([lbl,val])=>(<div key={lbl} className="p-3 bg-gray-50 rounded border"><p className="text-gray-500">{lbl}</p><p className="font-bold">{val}</p></div>))}
            </div>
            {report.root_cause&&(
              <div className="p-4 bg-amber-50 border border-amber-200 rounded text-xs space-y-1">
                <div><span className="font-semibold">Root Cause: </span><span className="font-mono">{report.root_cause}</span></div>
                {report.recommendation&&<div><span className="font-semibold">Recommendation: </span><span>{report.recommendation}</span></div>}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}