import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setErr('')
    setLoading(true)
    try {
      await login(email, password)
      nav('/chat')
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Erro ao entrar'
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
        <h1 className="text-2xl font-bold text-wa-greenDark">Entrar</h1>
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
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
        <p className="text-sm text-center">
          Não tem conta?{' '}
          <Link to="/register" className="text-wa-greenDark font-semibold">
            Criar agora
          </Link>
        </p>
      </form>
    </div>
  )
}
