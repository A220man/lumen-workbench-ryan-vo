import React, { createContext, useContext, useReducer, useEffect } from "react"
import axios from "axios"

export interface User {
  id: string
  email: string
  name: string
  role: "viewer" | "operator" | "admin"
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
}

type AuthAction =
  | { type: "LOGIN"; payload: { token: string; user: User } }
  | { type: "LOGOUT" }

const AuthContext = createContext<{
  state: AuthState
  login: (token: string, user: User) => void
  logout: () => void
} | undefined>(undefined)

const initialState: AuthState = {
  user: null,
  token: localStorage.getItem("auth_token"),
  isAuthenticated: !!localStorage.getItem("auth_token"),
}

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case "LOGIN":
      localStorage.setItem("auth_token", action.payload.token)
      axios.defaults.headers.common["Authorization"] = `Bearer ${action.payload.token}`
      return { user: action.payload.user, token: action.payload.token, isAuthenticated: true }
    case "LOGOUT":
      localStorage.removeItem("auth_token")
      delete axios.defaults.headers.common["Authorization"]
      return { user: null, token: null, isAuthenticated: false }
    default:
      return state
  }
}

export const LumenWorkbenchProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState)

  useEffect(() => {
    const token = localStorage.getItem("auth_token")
    if (token) {
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`
    }
  }, [])

  const login = (token: string, user: User) => {
    dispatch({ type: "LOGIN", payload: { token, user } })
  }

  const logout = () => {
    dispatch({ type: "LOGOUT" })
  }

  return (
    <AuthContext.Provider value={{ state, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuthContext = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuthContext must be used within LumenWorkbenchProvider")
  }
  return context
}