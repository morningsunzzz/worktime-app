import { NavLink, useLocation } from 'react-router-dom'
import { Clock, List, BarChart3, Settings } from 'lucide-react'

const tabs = [
  { to: '/', icon: Clock, label: '打卡' },
  { to: '/history', icon: List, label: '记录' },
  { to: '/stats', icon: BarChart3, label: '统计' },
  { to: '/settings', icon: Settings, label: '设置' },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()

  return (
    <div className="flex flex-col h-full max-w-md mx-auto bg-white shadow-lg">
      <main className="flex-1 overflow-y-auto">{children}</main>
      <nav className="flex items-center justify-around h-16 bg-white border-t border-gray-200 shrink-0">
        {tabs.map(({ to, icon: Icon, label }) => {
          const active = to === '/' ? location.pathname === '/' : location.pathname.startsWith(to)
          return (
            <NavLink
              key={to}
              to={to}
              className={`flex flex-col items-center gap-0.5 text-xs ${
                active ? 'text-blue-500' : 'text-gray-400'
              }`}
            >
              <Icon size={22} />
              <span>{label}</span>
            </NavLink>
          )
        })}
      </nav>
    </div>
  )
}
