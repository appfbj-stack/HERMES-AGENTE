import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Register() {
  const { register } = useAuth()
  const nav = useNavigate()
  const [tenantName, setTenantName] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setErr('')
    setLoading(true)
    try {
      await register(tenantName, name, email, password)
      nav('/chat')
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Erro ao registrar'
      setErr(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-wa-bg p-4">
      <form
        onSubmit={onSubmit}
        className="bg-white p-8 rounded-2xl shadow w-full max-w-sm space-y-4"
      >
        <h1 className="text-2xl font-bold text-wa-greenDark">Criar conta</h1>
        <input
          className="w-full border rounded-lg px-3 py-2"
          placeholder="Nome da empresa"
          value={tenantName}
          onChange={(e) => setTenantName(e.target.value)}
          required
        />
        <input
          className="w-full border rounded-lg px-3 py-2"
          placeholder="Seu nome"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <input
          className="w-full border rounded-lg px-3 py-2"
          placeholder="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          className="w-full border rounded-lg px-3 py-2"
          placeholder="Senha"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {err && <p className="text-red-600 text-sm">{err}</p>}
        <button
          disabled={loading}
          className="w-full bg-wa-green text-white py-2 rounded-lg hover:bg-wa-greenDark disabled:opacity-60"
        >
          {loading ? 'Criando...' : 'Criar conta'}
        </button>
        <p className="text-sm text-center">
          Já tem conta?{' '}
          <Link to="/login" className="text-wa-greenDark font-semibold">
            Entrar
          </Link>
        </p>
      </form>
    </div>
  )
}
