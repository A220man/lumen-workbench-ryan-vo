import React from "react"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { LumenWorkbenchProvider } from "./context"
import { Layout } from "./layout"
import { Dashboard } from "./components/dashboard"
import { EvaluationTable } from "./components/evaluation-table"
import { AnalyticsPanel } from "./components/analytics"
import { StatusPanel } from "./components/status"
import { ProfilePanel } from "./components/profile"
import { ShaderAnalyzerPanel } from "./components/shader-analyzer"
import { StructurizerPanel } from "./components/structurizer-panel"
import { StorageWritebackPanel } from "./components/storage-writeback"

export default function App() {
  return (
    <LumenWorkbenchProvider>
      <BrowserRouter>
        <Layout>
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/titles" element={<Dashboard />} />
                  <Route path="/evaluations" element={<EvaluationTable />} />
                  <Route path="/shaders" element={<ShaderAnalyzerPanel />} />
                  <Route path="/structurizer" element={<StructurizerPanel />} />
                  <Route path="/storage-writeback" element={<StorageWritebackPanel />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </div>
              <div className="space-y-6">
                <ProfilePanel />
                <StatusPanel />
                <AnalyticsPanel />
              </div>
            </div>
          </div>
        </Layout>
      </BrowserRouter>
    </LumenWorkbenchProvider>
  )
}