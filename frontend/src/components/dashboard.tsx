import React,{useState,useEffect}from"react"
import{useAuth}from"../hooks"
import{apiClient,Title}from"../api"
import{Link}from"react-router-dom"

export const Dashboard:React.FC=()=>{
  const{checkRole,isAuthenticated}=useAuth()
  const[titles,setTitles]=useState<Title[]>([])
  const[loading,setLoading]=useState(true)
  const[error,setError]=useState<string|null>(null)

  useEffect(()=>{
    const fetchData=async()=>{
      try{setLoading(true);const r=await apiClient.get<Title[]>("/titles");setTitles(r.data);setError(null)}
      catch(err){setError((err as Error).message);setTitles([])}
      finally{setLoading(false)}
    }
    if(isAuthenticated)fetchData()
    else setLoading(false)
  },[isAuthenticated])

  if(loading)return<div className="text-center py-8 animate-pulse">Loading titles...</div>
  if(error)return<div className="text-center text-red-500 py-8">Error: {error}</div>
  if(!isAuthenticated)return<div className="text-center py-8"><p>Please log in to view titles.</p></div>
  if(titles.length===0)return(<div className="text-center py-8"><p>No titles found. {checkRole("operator")?<Link to="/titles/new" className="text-blue-500 hover:underline">Import your first title</Link>:<span>Contact an operator to add titles.</span>}</p></div>)

  return(
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">Your Titles ({titles.length})</h2>
        {checkRole("operator")&&<Link to="/titles/new" className="btn btn-primary">Import New Title</Link>}
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50"><tr>{["Name","Status","Created","Actions"].map(h=><th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{h}</th>)}</tr></thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {titles.map(t=>(<tr key={t.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap"><div className="text-sm font-medium text-gray-900">{t.name}</div>{t.description&&<div className="text-sm text-gray-500">{t.description}</div>}</td>
              <td className="px-6 py-4 whitespace-nowrap"><span className={`px-2 text-xs rounded-full ${t.status==="active"?"bg-green-100 text-green-800":"bg-yellow-100 text-yellow-800"}`}>{t.status}</span></td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(t.created_at||"").toLocaleDateString()}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium"><Link to={`/titles/${t.id}`} className="text-indigo-600 hover:text-indigo-900">View</Link></td>
            </tr>))}
          </tbody>
        </table>
      </div>
    </div>
  )
}