import React, { useState, useEffect } from "react"
import { useAuth } from "../hooks"
import { apiClient } from "../api"

export const StatusPanel: React.FC = () => {
  const { checkRole } = useAuth()
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true)
        const response = await apiClient.get("/stats")
        setStats(response.data)
        setError(null)
      } catch (err) {
        setError((err as Error).message)
        setStats(null)
      } finally {
        setLoading(false)
      }
    }
    if (checkRole("viewer")) fetchStats()
    else setLoading(false)
  }, [checkRole])

  if (loading) return <div className="space-y-4"><h3 className="font-medium text-gray-900">System Status</h3><div className="animate-pulse text-sm">Loading...</div></div>
  if (error) return <div className="space-y-4"><h3 className="font-medium text-gray-900">System Status</h3><div className="text-center text-red-500 py-4">Error: {error}</div></div>
  if (!stats) return <div className="space-y-4"><h3 className="font-medium text-gray-900">System Status</h3><div className="text-center text-gray-500 py-4">No status data</div></div>

  return (
    <div className="space-y-4">
      <h3 className="font-medium text-gray-900">System Status</h3>
      <div className="space-y-2">
        <div className="flex justify-between items-center"><span className="text-sm text-gray-500">Active Titles</span><span className="font-mono text-sm font-bold text-gray-900">{stats.active_titles}</span></div>
        <div className="flex justify-between items-center"><span className="text-sm text-gray-500">Resolved Imports</span><span className="font-mono text-sm font-bold text-gray-900">{stats.total_imports}</span></div>
        <div className="flex justify-between items-center"><span className="text-sm text-gray-500">Resolution Rate</span><span className="font-mono text-sm font-bold text-gray-900">{stats.resolution_rate}</span></div>
        <div className="flex justify-between items-center"><span className="text-sm text-gray-500">Evaluation Count</span><span className="font-mono text-sm font-bold text-gray-900">{stats.evaluation_count}</span></div>
      </div>
    </div>
  )
}