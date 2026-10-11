import React from "react"
import { Outlet } from "react-router-dom"

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  )
}

const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-white border-r border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 rounded bg-blue-600 flex items-center justify-center text-white">
            LW
          </div>
          <span className="font-semibold text-lg">Lumen Workbench</span>
        </div>
      </div>
      <nav className="mt-6 space-y-1">
        <a
          href="/"
          className="block px-3 py-2 rounded-md text-sm font-medium
            bg-gray-50 text-gray-900"
        >
          Dashboard
        </a>
        <a
          href="/titles"
          className="block px-3 py-2 rounded-md text-sm font-medium
            hover:bg-gray-100 text-gray-700"
        >
          Titles
        </a>
        <a
          href="/evaluations"
          className="block px-3 py-2 rounded-md text-sm font-medium
            hover:bg-gray-100 text-gray-700"
        >
          Evaluations
        </a>
        <a
          href="/imports"
          className="block px-3 py-2 rounded-md text-sm font-medium
            hover:bg-gray-100 text-gray-700"
        >
          Imports
        </a>
        <a
          href="/settings"
          className="block px-3 py-2 rounded-md text-sm font-medium
            hover:bg-gray-100 text-gray-700"
        >
          Settings
        </a>
      </nav>
    </aside>
  )
}

export const Header: React.FC = () => {
  return (
    <header className="border-b border-gray-200 bg-white px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="text-sm font-medium text-gray-700">
          Lumen Workbench - AI/ML Developer Tools
        </div>
        <div className="flex items-center space-x-3">
          <span className="text-xs text-gray-500">v1.0.0</span>
        </div>
      </div>
    </header>
  )
}

export const MainContent: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="flex-1 flex flex-col space-y-6">
      <div className="flex-1 overflow-y-auto">{children}</div>
    </div>
  )
}

export const Aside: React.FC<{ children: React.ReactNode; side?: "left" | "right" }> = ({ children, side = "right" }) => {
  return (
    <aside className={`w-64 ${side === "left" ? "order-first" : "order-last"} 
      ${side === "left" ? "border-r" : "border-l"} border-gray-200`}>
      <div className="p-4">{children}</div>
    </aside>
  )
}

export const Section: React.FC<{
  title?: string
  children: React.ReactNode
  className?: string
}> = ({ title, children, className = "" }) => {
  return (
    <div className={`${className} space-y-4`}>
      {title && (
        <div className="flex items-center justify-between pb-2 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
      )}
      <div>{children}</div>
    </div>
  )
}