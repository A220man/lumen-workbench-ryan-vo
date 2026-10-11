import { useContext } from "react"
import { LumenWorkbenchProvider, useAuthContext, User } from "./context"
import axios from "axios"

export const useAuth = () => {
  const { state, login, logout } = useAuthContext()
  
  const authenticate = async (username: string, password: string) => {
    try {
      const response = await axios.post("/api/v1/auth/login", { username, password })
      const token = response.data.access_token
      const user = await axios.get("/api/v1/auth/me", {
        headers: { Authorization: `Bearer ${token}` }
      })
      login(token, user.data)
      return { success: true }
    } catch (error) {
      return { success: false, error: "Authentication failed" }
    }
  }

  const checkRole = (requiredRole: "viewer" | "operator" | "admin") => {
    const roleHierarchy = ["viewer", "operator", "admin"]
    if (!state.user) return false
    return roleHierarchy.indexOf(state.user.role) >= roleHierarchy.indexOf(requiredRole)
  }

  return {
    user: state.user,
    token: state.token,
    isAuthenticated: state.isAuthenticated,
    login: authenticate,
    logout,
    checkRole
  }
}

export const apiClient = axios.create({
  baseURL: "/api/v1",
  timeout: 10000
})

apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Redirect to login or show auth error
    }
    return Promise.reject(error)
  }
)