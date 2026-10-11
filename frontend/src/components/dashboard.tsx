import React, { useState, useEffect } from "react"
import { useAuth } from "../hooks"
import { apiClient, Title } from "../api"
import { Link } from "react-router-dom"

export const Dashboard: React.FC = () => {
  const { user, checkRole, isAuthenticated } = useAuth()
  const [titles, setTitles] = useState<Title[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const response = await apiClient.get<Title[]>("/titles")
        setTitles(response.data)
        setError(null)
      } catch (err) {
        setError((err as Error).message)
        setTitles([])
      } finally {
        setLoading(false)
      }
    }

    if (isAuthenticated) {
      fetchData()
    } else {
      setLoading(false)
    }
  }, [isAuthenticated])

  if (loading) {
    return <div className="text-center py-8 animate-pulse">Loading titles...</div>
  }

  if (error) {
    return <div className="text-center text-red-500 py-8">Error: {error}</div>
  }

  if (!isAuthenticated) {
    return (
      <div className="text-center py-8">
        <p>Please log in to view titles.</p>
      </div>
    )
  }

  if (titles.length === 0) {
    return (
      <div className="text-center py-8">
        <p>
          No titles found.{" "}
          {checkRole("operator") ? (
            <Link to="/titles/new" className="text-blue-500 hover:underline">
              Import your first title
            </Link>
          ) : (
            <span>Please contact an operator to add titles.</span>
          )}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">Your Titles ({titles.length})</h2>
        {checkRole("operator") && (
          <Link to="/titles/new" className="btn btn-primary">
            Import New Title
          </Link>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {titles.map((title) => (
              <tr key={title.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{title.name}</div>
                  {title.description && (
                    <div className="text-sm text-gray-500">{title.description}</div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full
                      ${title.status === "active"
                        ? "bg-green-100 text-green-800"
                        : title.status === "archived"
                        ? "bg-gray-100 text-gray-800"
                        : "bg-yellow-100 text-yellow-800"}`}
                  >
                    {title.status.charAt(0).toUpperCase() + title.status.slice(1)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(title.created_at || "").toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <Link
                    to={`/titles/${title.id}`}
                    className="text-indigo-600 hover:text-indigo-900"
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}