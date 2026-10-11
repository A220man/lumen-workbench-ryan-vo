import axios from "axios"

const api = axios.create({ baseURL: "/api/v1", timeout: 10000 })
api.interceptors.response.use(r => r, e => Promise.reject(new Error(e.response?.data?.detail || "Request failed")))

export interface Title { id: number; name: string; description: string | null; status: "draft" | "active" | "archived"; created_at: string; updated_at: string; is_active: boolean }
export interface ImportRecord { id: number; title_name: string; version: string | null; file_path: string | null; status: string; imported_at: string; analyzed_by: string | null; analysis_result: string | null }
export interface EvaluationRecord { id: number; title_id: number; score: number; comments: string | null; created_at: string; updated_at: string }
export interface ResolutionReport { source_name: string; needed_libraries: string[]; imports: Array<{ name: string; nid: number; library: string | null; status: string }>; resolved_count: number; unresolved_count: number; missing_module_count: number; coverage: number; score: number; blockers: string[] }
export interface SystemStats { active_titles: number; total_imports: number; resolution_rate: string; evaluation_count: number }
export interface AnalyticsData { resolution_by_library: string; performance_trend: string; import_volume: string; per_library: Record<string, { tp: number; fp: number; fn: number }>; metrics: { precision: number; recall: number; f1: number; coverage: number; stability_score?: number }; adversarial_stability?: string; shader_diagnostics?: string; structurizer_diagnostics?: string; storage_writeback_diagnostics?: string }
export interface AdversarialSymbol { name: string; nid: number; predicted_status: string; category?: string; mutation_type?: string }
export interface AdversarialGenerationResponse { generated_count: number; symbols: AdversarialSymbol[] }
export interface StressTestResult { status: string; total_cases: number; passed_cases: number; failed_cases: number; stability_score: number; false_positive_rate: number; category_scores: Record<string, { total: number; passed: number; failed: number; score: number }>; vulnerabilities: string[] }

export const apiClient = api
export const getTitle = async (id: number): Promise<Title> => (await api.get(`/titles/${id}`)).data
export const getTitles = async (params?: { search?: string; status?: string; page?: number; page_size?: number }): Promise<Title[]> => (await api.get("/titles", { params })).data
export const createTitle = async (title: Partial<Title>): Promise<Title> => (await api.post("/titles", title)).data
export const analyzeImports = async (file: File): Promise<ResolutionReport> => {
  const fd = new FormData(); fd.append("file", file)
  return (await api.post("/imports/analyze", fd, { headers: { "Content-Type": "multipart/form-data" } })).data
}
export const runEvaluation = async (titleName?: string, titleId?: number): Promise<any> => (await api.post("/evaluations/run", { title_name: titleName, title_id: titleId })).data
export const getStats = async (): Promise<SystemStats> => (await api.get("/stats")).data
export const getAnalytics = async (): Promise<AnalyticsData> => (await api.get("/analytics")).data
export const generateAdversarialCases = async (params?: { prefix?: string; category?: string; count?: number }): Promise<AdversarialGenerationResponse> => (await api.post("/adversarial/generate", null, { params })).data
export const runStressTest = async (category?: string): Promise<StressTestResult> => (await api.post("/adversarial/stress-test", null, { params: category ? { category } : undefined })).data

export interface BitfieldLayoutItem { name: string; offset: number; length: number; modelede?: boolean; modeled: boolean; source_builtin: string | null; description: string }
export interface ShaderAnalysisResponse { shader_address: string; title_id: string; ancillary_vgpr: string; has_ancillary_access: boolean; extracted_fields: string[]; register_reused: boolean; live_use_chain: string[]; unsupported_bit_access: boolean; rebuildable_pr1179: boolean; rejection_reason: string | null; status: string; decoded_word?: Record<string, { offset: number; length: number; value: number; modeled: boolean; source: string | null }> }
export const getRDNA2Layout = async (): Promise<BitfieldLayoutItem[]> => (await api.get('/shaders/rdna2-layout')).data
export const analyzeShader = async (payload: any): Promise<ShaderAnalysisResponse> => (await api.post('/shaders/analyze', payload)).data
export const getStrayShadersBatch = async (): Promise<ShaderAnalysisResponse[]> => (await api.get('/shaders/stray-batch')).data

export interface CFGDiagnosticReport { name: string; original_blocks: number; current_blocks: number; split_budget: number; exceeded_budget: boolean; multi_latch_loops: Array<{ header: number; latches: number[]; is_multi_latch: boolean }>; selection_conflicts: Array<{ header: number; merge_block: number; external_preds: number[]; in_construct_preds: number[]; shares_latch_edge: boolean }>; synthetic_chain_steps: string[]; infinite_recursion_detected: boolean; root_cause: string | null; recommendation: string | null; matches_issue_2642: boolean; status: "budget_exceeded" | "clean" }
export interface CFGPresetItem { id: string; name: string; description: string; adjacency: number[][]; expected_status: string }
export const getStructurizerPresets = async (): Promise<CFGPresetItem[]> => (await api.get('/structurizer/presets')).data
export const analyzeCFG = async (payload: { name?: string; adjacency: number[][]; split_budget?: number }): Promise<CFGDiagnosticReport> => (await api.post('/structurizer/analyze', payload)).data

export interface UnitDiagnostic { unit_id: string; guest_start: number; guest_end: number; offset_in_texture: number; size_bytes: number; is_edge_block: boolean; block_index: number; gpu_generation: number; cpu_block_stamp: number; block_policy_stored_over: boolean; page_policy_stored_over: boolean; edge_reason: string | null }
export interface StorageWritebackReport { title_id: string; title_name: string; texture_address: string; texture_size: string; alignment_offset: string; total_blocks_spanned: number; total_pages_spanned: number; edge_blocks_count: number; units: UnitDiagnostic[]; block_policy_corrupted: boolean; block_policy_dropped_units: string[]; page_policy_corrupted: boolean; page_policy_dropped_units: string[]; eager_writeback_corrupted: boolean; corrupted_glyphs: string[]; warning_logged: string | null; root_cause: string; recommendation: string; status: string }
export interface StoragePresetItem { id: string; name: string; description: string; texture_address: number; texture_size: number; expected_status: string }
export const getStorageWritebackPresets = async (): Promise<StoragePresetItem[]> => (await api.get('/storage-writeback/presets')).data
export const simulateStorageWriteback = async (payload?: any): Promise<StorageWritebackReport> => (await api.post('/storage-writeback/simulate', payload || {})).data
