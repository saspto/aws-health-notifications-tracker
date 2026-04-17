import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Bell, LogOut } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

interface LayoutProps {
  children: React.ReactNode
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const { user, logout } = useAuth()

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/notifications', label: 'Notifications', icon: Bell },
  ]

  return (
    <div className="flex min-h-screen bg-gray-50">
      <aside className="w-64 bg-[#232F3E] flex flex-col">
        <div className="p-4 border-b border-gray-600">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#FF9900] rounded flex items-center justify-center">
              <Bell size={16} className="text-white" />
            </div>
            <div>
              <p className="text-white text-sm font-bold leading-tight">Health Tracker</p>
              <p className="text-gray-400 text-xs">AWS Organizations</p>
            </div>
          </div>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className={`flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors ${
                location.pathname === to
                  ? 'bg-[#FF9900] text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              <Icon size={16} />
              {label}
            </Link>
          ))}
        </nav>
        {user && (
          <div className="p-4 border-t border-gray-600">
            <p className="text-gray-400 text-xs truncate mb-2">{user.email || user.username}</p>
            <button
              onClick={() => void logout()}
              className="flex items-center gap-2 text-gray-300 hover:text-white text-sm"
            >
              <LogOut size={14} />
              Sign out
            </button>
          </div>
        )}
      </aside>
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  )
}
