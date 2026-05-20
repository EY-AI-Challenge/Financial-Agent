import { Bell, Settings } from 'lucide-react'

function Navbar() {
  return (
    <nav className="bg-dark-800 border-b border-white/10 px-6 py-4 flex justify-between items-center">
      {/* Left: Title */}
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold text-accent-blue">Financial AI</h1>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-6">
        {/* Notifications */}
        <button className="relative hover:text-accent-blue transition-colors">
          <Bell size={20} />
          <span className="absolute top-0 right-0 w-2 h-2 bg-accent-red rounded-full"></span>
        </button>

        {/* Settings */}
        <button className="hover:text-accent-blue transition-colors">
          <Settings size={20} />
        </button>
      </div>
    </nav>
  )
}

export default Navbar
