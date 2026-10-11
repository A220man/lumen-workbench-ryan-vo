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

export const runEvaluation = async (titleName: string): Promise<any> => {
  const response = await api.post("/evaluations/run", { title_name: titleName })
  return response.data
}