import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, TrendingUp, Zap, BarChart3, ChevronDown } from 'lucide-react'

function Sidebar() {
  const location = useLocation()
  const [isWatchlistExpanded, setIsWatchlistExpanded] = useState(true)

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/')

  const menuItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Assets', path: '/assets', icon: TrendingUp },
    { label: 'Simulator', path: '/simulator', icon: Zap },
    { label: 'Smart Advisor', path: '/advisor', icon: BarChart3 },
  ]

  const watchlist = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'BTC-USD', 'ETH-USD']

  return (
    <aside className="w-64 bg-dark-800 border-r border-white/10 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-white/10">
        <h2 className="text-xl font-bold text-accent-blue">📊 FinanceAI</h2>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                    isActive(item.path)
                      ? 'bg-accent-blue text-white'
                      : 'text-gray-300 hover:bg-dark-700'
                  }`}
                >
                  <Icon size={20} />
                  <span className="font-medium">{item.label}</span>
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Watchlist Section */}
      <div className="border-t border-white/10 p-4">
        <button
          onClick={() => setIsWatchlistExpanded(!isWatchlistExpanded)}
          className="flex items-center justify-between w-full text-sm font-semibold text-gray-400 hover:text-white transition-colors mb-3"
        >
          <span>WATCHLIST</span>
          <ChevronDown
            size={16}
            className={`transition-transform ${isWatchlistExpanded ? 'rotate-180' : ''}`}
          />
        </button>

        {isWatchlistExpanded && (
          <ul className="space-y-2">
            {watchlist.map((ticker) => (
              <li key={ticker}>
                <Link
                  to={`/assets/${ticker}`}
                  className="text-sm text-gray-400 hover:text-accent-blue transition-colors px-3 py-1 block rounded hover:bg-dark-700"
                >
                  {ticker}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-white/10 p-4 text-center text-xs text-gray-500">
        <p>© 2026 FinanceAI</p>
      </div>
    </aside>
  )
}

export default Sidebar
