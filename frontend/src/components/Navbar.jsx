import { useState } from 'react'
import { Bell, User, Settings, Menu } from 'lucide-react'

function Navbar() {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)

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

        {/* User Profile Dropdown */}
        <div className="relative">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-2 hover:text-accent-blue transition-colors"
          >
            <User size={20} />
            <span className="text-sm">Profile</span>
          </button>

          {isDropdownOpen && (
            <div className="absolute right-0 mt-2 w-48 bg-dark-800 border border-white/10 rounded-lg shadow-lg z-50">
              <a href="#" className="block px-4 py-2 hover:bg-dark-700 rounded-t-lg">
                My Profile
              </a>
              <a href="#" className="block px-4 py-2 hover:bg-dark-700">
                Settings
              </a>
              <a href="#" className="block px-4 py-2 hover:bg-dark-700 text-accent-red rounded-b-lg">
                Logout
              </a>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}

export default Navbar
