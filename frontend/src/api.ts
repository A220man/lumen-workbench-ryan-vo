import axios from "axios"
const api = axios.create({ baseURL: "/api/v1", timeout: 10000 })
api.interceptors.response.use(r => r, e => Promise.reject(new Error(e.response?.data?.detail || "Request failed")))

export interface Title { id: number; name: string; description: string | null; status: string; created_at: string; updated_at: string; is_active: boolean }
export interface EvaluationRecord { id: number; title_id: number; score: number; comments: string | null; created_at: string; updated_at: string }
export interface ResolutionReport { source_name: string; needed_libraries: string[]; imports: Array<{ name: string; nid: number; library: string | null; status: string }>; resolved_count: number; unresolved_count: number; missing_module_count: number; coverage: number; score: number; blockers: string[] }
export interface BitfieldLayoutItem { name: string; offset: number; length: number; modeled: boolean; source_builtin: string | null; [k: string]: any }
export interface ShaderAnalysisResponse { shader_address: string; ancillary_vgpr: string; rejection_reason?: string | null; status: string; live_use_chain: string[]; decoded_word?: any; [k: string]: any }

export const apiClient = api
export const getTitle = async (id: number): Promise<Title> => (await api.get(`/titles/${id}`)).data
export const getTitles = async (params?: any): Promise<Title[]> => (await api.get("/titles", { params })).data
export const createTitle = async (title: Partial<Title>): Promise<Title> => (await api.post("/titles", title)).data
export const analyzeImports = async (file: File, explain = false): Promise<ResolutionReport> => { const fd = new FormData(); fd.append("file", file); if (explain) fd.append("explain", "true"); return (await api.post("/imports/analyze", fd, { headers: { "Content-Type": "multipart/form-data" } })).data }
export const runEvaluation = async (titleName?: string, titleId?: number): Promise<unknown> => (await api.post("/evaluations/run", { title_name: titleName, title_id: titleId })).data

export const getStats = async (): Promise<unknown> => (await api.get("/stats")).data
export const getAnalytics = async (): Promise<unknown> => (await api.get("/analytics")).data
export const getRDNA2Layout = async (): Promise<BitfieldLayoutItem[]> => (await api.get("/shaders/rdna2-layout")).data
export const analyzeShader = async (payload: unknown): Promise<ShaderAnalysisResponse> => (await api.post("/shaders/analyze", payload)).data
export const getStrayShadersBatch = async (): Promise<ShaderAnalysisResponse[]> => (await api.get("/shaders/stray-batch")).data

export interface CFGDiagnosticReport { name: string; original_blocks: number; current_blocks: number; split_budget: number; multi_latch_loops: any[]; matches_issue_2642?: boolean; status: string; synthetic_chain_steps: string[]; infinite_recursion_detected?: boolean; root_cause?: string | null; recommendation?: string | null; [k: string]: any }
export interface CFGPresetItem { id: string; name: string; adjacency: number[][]; [k: string]: any }
export const getStructurizerPresets = async (): Promise<CFGPresetItem[]> => (await api.get("/structurizer/presets")).data
export const analyzeCFG = async (payload: unknown): Promise<CFGDiagnosticReport> => (await api.post("/structurizer/analyze", payload)).data

export interface StorageWritebackReport { status: string; texture_address: string; alignment_offset: string; total_blocks_spanned: number; edge_blocks_count: number; warning_logged?: string | null; block_policy_corrupted: boolean; corrupted_glyphs: string[]; root_cause: string; recommendation: string; [k: string]: any }
export interface StoragePresetItem { id: string; name: string; texture_address: number; texture_size: number; [k: string]: any }
export const getStorageWritebackPresets = async (): Promise<StoragePresetItem[]> => (await api.get("/storage-writeback/presets")).data
export const simulateStorageWriteback = async (payload?: unknown): Promise<StorageWritebackReport> => (await api.post("/storage-writeback/simulate", payload || {})).data

export interface StopPRItem { number: number; url: string; commit: string; merged: boolean; description: string }
export interface StartupStopItem { index: number; description: string; error_text: string; shader_cache_misses: number | null; prs: StopPRItem[]; verified: boolean; notes: string }
export interface FirstLightReportResponse { title_id: string; title_name: string; version: string; stops: StartupStopItem[]; current_stop: number; passed_stops: number; failed_stops: number; status: string; regression_detected: boolean; regression_details: string[] }
export interface FirstLightPresetItem { name: string; applied_prs: number[]; description: string }
export const getFirstLightStops = async (): Promise<StartupStopItem[]> => (await api.get("/first-light/stops")).data
export const getFirstLightPresets = async (): Promise<FirstLightPresetItem[]> => (await api.get("/first-light/presets")).data
export const analyzeFirstLight = async (appliedPrs?: number[]): Promise<FirstLightReportResponse> => (await api.post("/first-light/analyze", { applied_prs: appliedPrs })).data

// Import Analysis
export const saveImportAnalysis = async (report: ResolutionReport): Promise<{ id: number }> =>
  (await api.post("/imports/analyze/save", report)).data