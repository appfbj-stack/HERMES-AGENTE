import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import {
  LayoutDashboard,
  MessageSquare,
  Users,
  CheckSquare,
  Coins,
  Settings as SettingsIcon,
  LogOut,
} from 'lucide-react'

const items = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/chat', icon: MessageSquare, label: 'Conversas' },
  { to: '/leads', icon: Users, label: 'Leads' },
  { to: '/tasks', icon: CheckSquare, label: 'Tarefas' },
  { to: '/credits', icon: Coins, label: 'Créditos' },
  { to: '/settings', icon: SettingsIcon, label: 'Configurações' },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const nav = useNavigate()

  return (
    <div className="flex h-screen bg-wa-bg">
      <aside className="hidden md:flex w-60 bg-white border-r border-wa-border flex-col">
        <div className="px-4 py-4 border-b border-wa-border">
          <div className="font-bold text-wa-greenDark">Agente SaaS</div>
          <div className="text-xs text-wa-subtext truncate">{user?.name}</div>
        </div>
        <nav className="p-3 space-y-1 flex-1">
          {items.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
                  isActive
                    ? 'bg-wa-green text-white'
                    : 'text-wa-text hover:bg-wa-bg'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <button
          onClick={() => {
            logout()
            nav('/login')
          }}
          className="m-3 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm bg-wa-bg hover:bg-wa-border"
        >
          <LogOut size={16} /> Sair
        </button>
      </aside>

      {/* Mobile bottom nav */}
      <nav className="md:hidden fixed bottom-0 inset-x-0 bg-white border-t border-wa-border z-30 flex">
        {items.slice(0, 5).map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center py-2 text-[11px] ${
                isActive ? 'text-wa-greenDark' : 'text-wa-subtext'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      <main className="flex-1 overflow-hidden pb-12 md:pb-0">
        <Outlet />
      </main>
    </div>
  )
}
