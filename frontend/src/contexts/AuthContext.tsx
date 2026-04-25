import { createContext, useContext, useState, ReactNode } from 'react'
import api from '../api/client'
import type { AuthUser } from '../types'

interface AuthCtx {
  user: AuthUser | null
  login: (email: string, password: string) => Promise<void>
  register: (tenant_name: string, name: string, email: string, password: string) => Promise<void>
  logout: () => void
}

const Ctx = createContext<AuthCtx | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const raw = localStorage.getItem('user')
    return raw ? (JSON.parse(raw) as AuthUser) : null
  })

  function persist(token: string, u: AuthUser) {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(u))
    setUser(u)
  }

  async function login(email: string, password: string) {
    const { data } = await api.post('/api/auth/login', { email, password })
    persist(data.access_token, {
      id: data.user_id,
      name: data.name,
      email: data.email,
      tenantId: data.tenant_id,
    })
  }

  async function register(tenant_name: string, name: string, email: string, password: string) {
    const { data } = await api.post('/api/auth/register', { tenant_name, name, email, password })
    persist(data.access_token, {
      id: data.user_id,
      name: data.name,
      email: data.email,
      tenantId: data.tenant_id,
    })
  }

  function logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  return <Ctx.Provider value={{ user, login, register, logout }}>{children}</Ctx.Provider>
}

export function useAuth() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useAuth fora do AuthProvider')
  return ctx
}
