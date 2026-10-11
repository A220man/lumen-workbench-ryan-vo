import axios from "axios"

const api = axios.create({
  baseURL: "/api/v1",
  timeout: 10000
})

api.interceptors.response.use(
  response => response,
  error => {
    const message = error.response?.data?.detail || "Request failed"
    return Promise.reject(new Error(message))
  }
)

export interface Title {
  id: number
  name: string
  description: string | null
  status: "draft" | "active" | "archived"
  created_at: string
  updated_at: string
  is_active: boolean
}

export interface ImportRecord {
  id: number
  title_name: string
  version: string | null
  file_path: string | null
  status: string
  imported_at: string
  analyzed_by: string | null
  analysis_result: string | null
}

export interface EvaluationRecord {
  id: number
  title_id: number
  score: number
  comments: string | null
  created_at: string
  updated_at: string
}

export interface ResolutionReport {
  source_name: string
  needed_libraries: string[]
  imports: Array<{
    name: string
    nid: number
    library: string | null
    status: string
  }>
  resolved_count: number
  unresolved_count: number
  missing_module_count: number
  coverage: number
  score: number
  blockers: string[]
}

export interface SystemStats {
  active_titles: number
  total_imports: number
  resolution_rate: string
  evaluation_count: number
}

export interface AnalyticsData {
  resolution_by_library: string
  performance_trend: string
  import_volume: string
  per_library: Record<string, { tp: number; fp: number; fn: number }>
  metrics: {
    precision: number
    recall: number
    f1: number
    coverage: number
    stability_score?: number
  }
  adversarial_stability?: string
  shader_diagnostics?: string
  structurizer_diagnostics?: string
}

export interface AdversarialSymbol {
  name: string
  nid: number
  predicted_status: string
  category?: string
  mutation_type?: string
}

export interface AdversarialGenerationResponse {
  generated_count: number
  symbols: AdversarialSymbol[]
}

export interface StressTestResult {
  status: string
  total_cases: number
  passed_cases: number
  failed_cases: number
  stability_score: number
  false_positive_rate: number
  category_scores: Record<string, { total: number; passed: number; failed: number; score: number }>
  vulnerabilities: string[]
}

export const apiClient = api

export const getTitle = async (id: number): Promise<Title> => {
  const response = await api.get(`/titles/${id}`)
  return response.data
}

export const getTitles = async (params?: {
  search?: string
  status?: string
  page?: number
  page_size?: number
}): Promise<Title[]> => {
  const response = await api.get("/titles", { params })
  return response.data
}

export const createTitle = async (title: Partial<Title>): Promise<Title> => {
  const response = await api.post("/titles", title)
  return response.data
}

export const analyzeImports = async (file: File): Promise<ResolutionReport> => {
  const formData = new FormData()
  formData.append("file", file)
  const response = await api.post("/imports/analyze", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  })
  return response.data
}

export const runEvaluation = async (titleName?: string, titleId?: number): Promise<any> => {
  const response = await api.post("/evaluations/run", { title_name: titleName, title_id: titleId })
  return response.data
}

export const getStats = async (): Promise<SystemStats> => {
  const response = await api.get("/stats")
  return response.data
}

export const getAnalytics = async (): Promise<AnalyticsData> => {
  const response = await api.get("/analytics")
  return response.data
}

export const generateAdversarialCases = async (params?: {
  prefix?: string
  category?: string
  count?: number
}): Promise<AdversarialGenerationResponse> => {
  const response = await api.post("/adversarial/generate", null, { params })
  return response.data
}

export const runStressTest = async (category?: string): Promise<StressTestResult> => {
  const response = await api.post("/adversarial/stress-test", null, {
    params: category ? { category } : undefined
  })
  return response.data
}

export interface BitfieldLayoutItem {
  name: string
  offset: number
  length: number
  modeled: boolean
  source_builtin: string | null
  description: string
}

export interface ShaderAnalysisResponse {
  shader_address: string
  title_id: string
  ancillary_vgpr: string
  has_ancillary_access: boolean
  extracted_fields: string[]
  register_reused: boolean
  live_use_chain: string[]
  unsupported_bit_access: boolean
  rebuildable_pr1179: boolean
  rejection_reason: string | null
  status: string
  decoded_word?: Record<string, { offset: number; length: number; value: number; modeled: boolean; source: string | null }>
}

export const getRDNA2Layout = async (): Promise<BitfieldLayoutItem[]> => {
  const response = await api.get('/shaders/rdna2-layout')
  return response.data
}

export const analyzeShader = async (payload: {
  shader_address?: string
  title_id?: string
  ancillary_vgpr?: string
  instructions?: Array<{
    index: number
    opcode: string
    dest?: string | null
    sources: string[]
    bit_offset?: number | null
    bit_length?: number | null
    condition?: string | null
  }>
  raw_word?: number | null
}): Promise<ShaderAnalysisResponse> => {
  const response = await api.post('/shaders/analyze', payload)
  return response.data
}

export const getStrayShadersBatch = async (): Promise<ShaderAnalysisResponse[]> => {
  const response = await api.get('/shaders/stray-batch')
  return response.data
}

export interface CFGDiagnosticReport {
  name: string
  original_blocks: number
  current_blocks: number
  split_budget: number
  exceeded_budget: boolean
  multi_latch_loops: Array<{ header: number; latches: number[]; is_multi_latch: boolean }>
  selection_conflicts: Array<{
    header: number
    merge_block: number
    external_preds: number[]
    in_construct_preds: number[]
    shares_latch_edge: boolean
  }>
  synthetic_chain_steps: string[]
  infinite_recursion_detected: boolean
  root_cause: string | null
  recommendation: string | null
  matches_issue_2642: boolean
  status: "budget_exceeded" | "clean"
}

export interface CFGPresetItem {
  id: string
  name: string
  description: string
  adjacency: number[][]
  expected_status: string
}

export const getStructurizerPresets = async (): Promise<CFGPresetItem[]> => {
  const response = await api.get('/structurizer/presets')
  return response.data
}

export const analyzeCFG = async (payload: {
  name?: string
  adjacency: number[][]
  split_budget?: number
}): Promise<CFGDiagnosticReport> => {
  const response = await api.post('/structurizer/analyze', payload)
  return response.data
}
