import React, { useState, useEffect } from "react"
import { useAuth } from "../hooks"
import { apiClient } from "../api"

export const AnalyticsPanel: React.FC = () => {
  const { user, checkRole } = useAuth()
  const [analytics, setAnalytics] = useState<any>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true)
        const response = await apiClient.get("/analytics")
        setAnalytics(response.data)
        setError(null)
      } catch (err) {
        setError((err as Error).message)
        setAnalytics(null)
      } finally {
        setLoading(false)
      }
    }

    if (checkRole("viewer")) {
      fetchAnalytics()
    }
  }, [checkRole])

  if (loading) {
    return (
      <div className="space-y-4">
        <h3 className="font-medium text-gray-900">Analytics</h3>
        <div className="space-y-2 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-full">
            <div className="h-4 bg-blue-500 rounded" style={{ width: "30%" }} />
          </div>
          <div className="h-4 bg-gray-200 rounded w-full">
            <div className="h-4 bg-green-500 rounded" style={{ width: "50%" }} />
          </div>
          <div className="h-4 bg-gray-200 rounded w-full">
            <div className="h-4 bg-purple-500 rounded" style={{ width: "70%" }} />
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h3 className="font-medium text-gray-900">Analytics</h3>
        <div className="text-center text-red-500 py-4">Error: {error}</div>
      </div>
    )
  }

  if (!analytics) {
    return (
      <div className="space-y-4">
        <h3 className="font-medium text-gray-900">Analytics</h3>
        <div className="text-center text-gray-500 py-4">No analytics data</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="font-medium text-gray-900">Analytics</h3>
      <div className="space-y-2">
        <div className="flex items-start">
          <div className="flex-shrink-0 h-8 w-8 rounded bg-blue-100 text-blue-600 flex items-center justify-center">
            📊
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-900">Resolution by Library</p>
            <p className="text-xs text-gray-500">{analytics.resolution_by_library || "N/A"}</p>
          </div>
        </div>
        <div className="flex items-start">
          <div className="flex-shrink-0 h-8 w-8 rounded bg-green-100 text-green-600 flex items-center justify-center">
            ⚡
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-900">Performance Trend</p>
            <p className="text-xs text-gray-500">{analytics.performance_trend || "N/A"}</p>
          </div>
        </div>
        <div className="flex items-start">
          <div className="flex-shrink-0 h-8 w-8 rounded bg-purple-100 text-purple-600 flex items-center justify-center">
            📈
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-900">Import Volume</p>
            <p className="text-xs text-gray-500">{analytics.import_volume || "N/A"}</p>
          </div>
        </div>
      </div>
    </div>
  )
}