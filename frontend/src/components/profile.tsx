import React, { useState } from "react"
import { useAuth } from "../hooks"

export const ProfilePanel: React.FC = () => {
  const { user, logout, checkRole } = useAuth()
  const [showDetails, setShowDetails] = useState<boolean>(false)

  if (!user) {
    return (
      <div className="p-4">
        <div className="text-center">
          <p className="text-sm text-gray-500">No user logged in</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <div className="h-6 w-6 rounded-full bg-gray-300 flex items-center justify-center">
              <span className="text-xs font-medium text-gray-700">
                {user.name?.charAt(0) || user.email?.charAt(0) || "?"}
              </span>
            </div>
            <span className="text-sm font-medium text-gray-900">{user.name || user.email}</span>
          </div>
          <div className="mt-1 flex items-center space-x-2">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
              ${user.role === "admin" ? "bg-red-100 text-red-800"
                : user.role === "operator" ? "bg-blue-100 text-blue-800"
                : "bg-green-100 text-green-800"}`}>
              {user.role?.charAt(0).toUpperCase() + (user.role?.slice(1) || "")}
            </span>
          </div>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-gray-400 hover:text-gray-600 text-xs"
          >
            Details
          </button>
          <button
            onClick={() => logout()}
            className="text-gray-400 hover:text-red-600 text-xs"
          >
            Logout
          </button>
        </div>
      </div>

      {showDetails && (
        <div className="mt-3 pt-3 border-t border-gray-200 space-y-1">
          <div className="text-xs text-gray-600">
            <span className="font-medium">Email:</span> {user.email}
          </div>
          <div className="text-xs text-gray-600">
            <span className="font-medium">Role:</span> {user.role}
          </div>
          <div className="text-xs text-gray-600">
            <span className="font-medium">Permissions:</span>
            {" "}
            {checkRole("admin") ? "Full access"
              : checkRole("operator") ? "Edit & analyze"
              : "Read only"}
          </div>
        </div>
      )}
    </div>
  )
}