import React from "react"
import { Link } from "react-router-dom"

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <div className="flex h-screen">
        <aside className="w-64 bg-white border-r border-gray-200">
          <div className="p-4 border-b border-gray-200 flex items-center space-x-3">
            <div className="h-8 w-8 rounded bg-blue-600 flex items-center justify-center text-white font-bold">LW</div>
            <span className="font-semibold text-lg">Lumen Workbench</span>
          </div>
          <nav className="mt-6 space-y-1">
            <Link to="/" className="block px-3 py-2 rounded-md text-sm font-medium bg-gray-50 text-gray-900">Dashboard</Link>
            <Link to="/titles" className="block px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 text-gray-700">Titles</Link>
            <Link to="/evaluations" className="block px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 text-gray-700">Evaluations</Link>
            <Link to="/shaders" className="block px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 text-gray-700">Shaders</Link>
            <Link to="/structurizer" className="block px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 text-gray-700">Structurizer</Link>
            <Link to="/storage-writeback" className="block px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 text-gray-700">Writeback</Link>
            <Link to="/intel-gpu" className="block px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-100 text-gray-700">GPU Compat</Link>
          </nav>
        </aside>
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  )
}