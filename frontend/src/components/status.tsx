import React, { useState, useEffect } from "react"
import { useAuth } from "../hooks"
import { apiClient } from "../api"

export const StatusPanel: React.FC = () => {
  const { user, checkRole } = useAuth()
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

    if (checkRole("viewer")) {
      fetchStats()
    }
  }, [checkRole])

  if (loading) {
    return (
      <div className="space-y-4">
        <h3 className="font-medium text-gray-900">System Status</h3>
        <div className="space-y-2 animate-pulse">
          <div className="flex justify-between">
            <span className="text-sm">Active Titles</span>
            <span className="font-mono">Loading...</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm">Resolved Imports</span>
            <span className="font-mono">Loading...</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm">Evaluation Count</span>
            <span className="font-mono">Loading...</span>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h3 className="font-medium text-gray-900">System Status</h3>
        <div className="text-center text-red-500 py-4">Error: {error}</div>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="space-y-4">
        <h3 className="font-medium text-gray-900">System Status</h3>
        <div className="text-center text-gray-500 py-4">No data available</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="font-medium text-gray-900">System Status</h3>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Active Titles</span>
          <span className="font-mono">{stats.active_titles || 0}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span>Total Imports</span>
          <span className="font-mono">{stats.total_imports || 0}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span>Resolution Rate</span>
          <span className="font-mono">{stats.resolution_rate || "0%"}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span>Evaluations</span>
          <span className="font-mono">{stats.evaluation_count || 0}</span>
        </div>
      </div>
    </div>
  )
}