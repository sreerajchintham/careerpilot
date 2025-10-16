import React, { ReactNode } from 'react'
import { useRouter } from 'next/router'
import { useAuth } from '../contexts/AuthContext'
import { 
  Home, 
  Upload, 
  Search, 
  Send, 
  FileText, 
  LogOut, 
  User,
  Menu,
  X,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import { useState } from 'react'

interface DashboardLayoutProps {
  children: ReactNode
}

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Resume Upload', href: '/dashboard/resume', icon: Upload },
  { name: 'Job Scraping', href: '/dashboard/jobs', icon: Search },
  { name: 'Applications', href: '/dashboard/applications', icon: Send },
  { name: 'Resume Drafting', href: '/dashboard/drafts', icon: FileText },
]

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const { user, appUser, signOut } = useAuth()
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const handleSignOut = async () => {
    try {
      await signOut()
      router.push('/login')
    } catch (error) {
      console.error('Error signing out:', error)
    }
  }

  const isActive = (href: string) => {
    return router.pathname === href
  }

  return (
    <div className="h-screen flex overflow-hidden animated-bg">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 z-40 lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 bg-black bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="relative flex-1 flex flex-col max-w-xs w-full card-futuristic">
          <div className="absolute top-0 right-0 -mr-12 pt-2">
            <button
              type="button"
              className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-6 w-6 text-white" />
            </button>
          </div>
          <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
            <div className="flex-shrink-0 flex items-center px-4">
              <div className="h-12 w-12 bg-gradient-to-br from-cyan-400 to-green-400 rounded-xl flex items-center justify-center glow-green">
                <Home className="h-7 w-7 text-black" />
              </div>
              <span className="ml-3 text-2xl font-bold bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">CareerPilot</span>
            </div>
            <nav className="mt-8 px-2 space-y-2">
              {navigation.map((item) => {
                const Icon = item.icon
                return (
                  <a
                    key={item.name}
                    href={item.href}
                    className={`${
                      isActive(item.href)
                        ? 'bg-gradient-to-r from-cyan-500/20 to-green-500/20 text-cyan-400 border-l-4 border-cyan-400'
                        : 'text-gray-300 hover:bg-gray-800/50 hover:text-cyan-400 hover:border-l-4 hover:border-cyan-400/50'
                    } group flex items-center px-4 py-4 text-lg font-semibold rounded-lg transition-all duration-300`}
                  >
                    <Icon className="mr-4 h-7 w-7" />
                    {item.name}
                  </a>
                )
              })}
            </nav>
          </div>
          <div className="flex-shrink-0 flex border-t border-gray-700 p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="h-10 w-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                  <User className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-3">
                <p className="text-base font-semibold text-gray-200">{user?.email}</p>
                <button
                  onClick={handleSignOut}
                  className="text-sm font-medium text-gray-400 hover:text-red-400 flex items-center transition-colors"
                >
                  <LogOut className="h-4 w-4 mr-1" />
                  Sign out
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:flex lg:flex-shrink-0">
        <div className={`flex flex-col transition-all duration-300 ${sidebarCollapsed ? 'w-20' : 'w-72'}`}>
          <div className="flex flex-col h-0 flex-1 border-r border-gray-700 card-futuristic">
            <div className="flex-1 flex flex-col pt-6 pb-4 overflow-y-auto">
              <div className="flex items-center flex-shrink-0 px-6">
                <div className="h-12 w-12 bg-gradient-to-br from-cyan-400 to-green-400 rounded-xl flex items-center justify-center glow-green">
                  <Home className="h-7 w-7 text-black" />
                </div>
                {!sidebarCollapsed && (
                  <span className="ml-3 text-2xl font-bold bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">CareerPilot</span>
                )}
              </div>
              
              {/* Collapse Toggle Button */}
              <div className="mt-6 px-4">
                <button
                  onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                  className="w-full flex items-center justify-center p-3 text-gray-400 hover:text-cyan-400 hover:bg-gray-800/50 rounded-lg transition-all duration-300"
                >
                  {sidebarCollapsed ? (
                    <ChevronRight className="h-6 w-6" />
                  ) : (
                    <ChevronLeft className="h-6 w-6" />
                  )}
                </button>
              </div>

              <nav className="mt-4 flex-1 px-4 space-y-2">
                {navigation.map((item) => {
                  const Icon = item.icon
                  return (
                    <a
                      key={item.name}
                      href={item.href}
                      className={`${
                        isActive(item.href)
                          ? 'bg-gradient-to-r from-cyan-500/20 to-green-500/20 text-cyan-400 border-l-4 border-cyan-400'
                          : 'text-gray-300 hover:bg-gray-800/50 hover:text-cyan-400 hover:border-l-4 hover:border-cyan-400/50'
                      } group flex items-center px-4 py-4 text-lg font-semibold rounded-lg transition-all duration-300 ${
                        sidebarCollapsed ? 'justify-center' : ''
                      } relative`}
                      title={sidebarCollapsed ? item.name : undefined}
                    >
                      <Icon className={`h-7 w-7 ${sidebarCollapsed ? '' : 'mr-4'}`} />
                      {!sidebarCollapsed && item.name}
                      
                      {/* Tooltip for collapsed state */}
                      {sidebarCollapsed && (
                        <div className="absolute left-full ml-2 px-3 py-2 bg-gray-800 text-white text-sm font-medium rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50">
                          {item.name}
                          <div className="absolute left-0 top-1/2 transform -translate-y-1/2 -translate-x-1 w-2 h-2 bg-gray-800 rotate-45"></div>
                        </div>
                      )}
                    </a>
                  )
                })}
              </nav>
            </div>
            <div className="flex-shrink-0 flex border-t border-gray-700 p-4">
              <div className="flex items-center w-full">
                <div className="flex-shrink-0 relative group">
                  <div className="h-10 w-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                    <User className="h-6 w-6 text-white" />
                  </div>
                  
                  {/* User tooltip for collapsed state */}
                  {sidebarCollapsed && (
                    <div className="absolute left-full ml-2 px-3 py-2 bg-gray-800 text-white text-sm font-medium rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50">
                      {user?.email}
                      <div className="absolute left-0 top-1/2 transform -translate-y-1/2 -translate-x-1 w-2 h-2 bg-gray-800 rotate-45"></div>
                    </div>
                  )}
                </div>
                {!sidebarCollapsed && (
                  <div className="ml-3 flex-1">
                    <p className="text-sm font-semibold text-gray-200">{user?.email}</p>
                    <button
                      onClick={handleSignOut}
                      className="text-xs font-medium text-gray-400 hover:text-red-400 flex items-center transition-colors"
                    >
                      <LogOut className="h-3 w-3 mr-1" />
                      Sign out
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Toggle buttons - absolute positioned to not affect layout flow */}
        <div className="absolute top-2 left-2 z-10 flex items-center space-x-2 lg:left-auto lg:right-2">
          {/* Mobile menu button */}
          <button
            type="button"
            className="lg:hidden h-10 w-10 inline-flex items-center justify-center rounded-md bg-black/50 backdrop-blur-sm text-gray-400 hover:text-cyan-400 hover:bg-black/70 focus:outline-none transition-all border border-gray-700 hover:border-cyan-500"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </button>
        </div>
        
        {/* Main scrollable content */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8 py-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
