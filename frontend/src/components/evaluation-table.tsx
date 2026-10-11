import React, { useState, useEffect } from "react"
import { useAuth } from "../hooks"
import { apiClient, EvaluationRecord } from "../api"
import { Link } from "react-router-dom"

export const EvaluationTable: React.FC = () => {
  const { checkRole } = useAuth()
  const [evaluations, setEvaluations] = useState<EvaluationRecord[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const response = await apiClient.get<EvaluationRecord[]>("/evaluations")
        setEvaluations(response.data)
        setError(null)
      } catch (err) {
        setError((err as Error).message)
        setEvaluations([])
      } finally {
        setLoading(false)
      }
    }
    if (checkRole("operator")) fetchData()
    else setLoading(false)
  }, [checkRole])

  if (loading) return <div className="text-center py-8 animate-pulse">Loading evaluations...</div>
  if (error) return <div className="text-center text-red-500 py-8">Error: {error}</div>
  if (evaluations.length === 0) {
    return (
      <div className="text-center py-8">
        <p>No evaluations yet. {checkRole("operator") ? <Link to="/evaluations/new" className="text-blue-500 hover:underline">Add First Evaluation</Link> : <span>No evaluations found.</span>}</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>{["Title", "Score", "Comments", "Created", "Actions"].map((h) => <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{h}</th>)}</tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {evaluations.map((e) => (
            <tr key={e.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Title #{e.title_id}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-bold">{e.score}</td>
              <td className="px-6 py-4 text-sm text-gray-500">{e.comments}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(e.created_at || "").toLocaleDateString()}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium"><Link to={`/evaluations/${e.id}`} className="text-indigo-600 hover:text-indigo-900">View</Link></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}