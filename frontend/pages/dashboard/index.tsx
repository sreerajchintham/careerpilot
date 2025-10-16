import React, { useEffect, useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { useRouter } from 'next/router'
import DashboardLayout from '../../components/DashboardLayout'
import { 
  Upload, 
  Search, 
  Send, 
  FileText, 
  TrendingUp, 
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import { supabase, Application, Job } from '../../lib/supabase'

export default function Dashboard() {
  const { user, appUser, loading } = useAuth()
  const router = useRouter()
  const [stats, setStats] = useState({
    totalJobs: 0,
    totalApplications: 0,
    pendingApplications: 0,
    recentApplications: 0,
  })
  const [recentApplications, setRecentApplications] = useState<Application[]>([])

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      fetchDashboardData()
    }
  }, [user])

  const fetchDashboardData = async () => {
    if (!user) return

    try {
      // Fetch total jobs
      const { count: totalJobs } = await supabase
        .from('jobs')
        .select('*', { count: 'exact', head: true })

      // Fetch user applications
      const { data: applications } = await supabase
        .from('applications')
        .select(`
          *,
          jobs (
            id,
            title,
            company,
            source
          )
        `)
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })

      // Fetch recent applications (last 7 days)
      const sevenDaysAgo = new Date()
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)
      
      const { data: recentApps } = await supabase
        .from('applications')
        .select(`
          *,
          jobs (
            id,
            title,
            company,
            source
          )
        `)
        .eq('user_id', user.id)
        .gte('created_at', sevenDaysAgo.toISOString())
        .order('created_at', { ascending: false })
        .limit(5)

      setStats({
        totalJobs: totalJobs || 0,
        totalApplications: applications?.length || 0,
        pendingApplications: applications?.filter(app => app.status === 'draft').length || 0,
        recentApplications: recentApps?.length || 0,
      })

      setRecentApplications(recentApps || [])
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  const quickActions = [
    {
      name: 'Upload Resume',
      description: 'Upload and parse your resume',
      href: '/dashboard/resume',
      icon: Upload,
      color: 'bg-blue-500',
    },
    {
      name: 'Scrape Jobs',
      description: 'Find new job opportunities',
      href: '/dashboard/jobs',
      icon: Search,
      color: 'bg-green-500',
    },
    {
      name: 'View Applications',
      description: 'Manage your applications',
      href: '/dashboard/applications',
      icon: Send,
      color: 'bg-purple-500',
    },
    {
      name: 'Resume Drafts',
      description: 'Edit and improve your resume',
      href: '/dashboard/drafts',
      icon: FileText,
      color: 'bg-orange-500',
    },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'submitted':
        return 'bg-green-100 text-green-800'
      case 'draft':
        return 'bg-yellow-100 text-yellow-800'
      case 'under_review':
        return 'bg-blue-100 text-blue-800'
      case 'interview':
        return 'bg-purple-100 text-purple-800'
      case 'rejected':
        return 'bg-red-100 text-red-800'
      case 'accepted':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">
            WELCOME BACK, {appUser?.profile?.name || user.email?.split('@')[0].toUpperCase()}!
          </h1>
          <p className="mt-2 text-lg text-gray-300">
            Here's what's happening with your job search today.
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <div className="card-futuristic overflow-hidden rounded-2xl">
            <div className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="h-12 w-12 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-xl flex items-center justify-center glow-blue">
                    <Search className="h-7 w-7 text-white" />
                  </div>
                </div>
                <div className="ml-6 w-0 flex-1">
                  <dl>
                    <dt className="text-lg font-semibold text-gray-300 truncate">
                      TOTAL JOBS
                    </dt>
                    <dd className="text-3xl font-bold text-cyan-400">
                      {stats.totalJobs.toLocaleString()}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="card-futuristic overflow-hidden rounded-2xl">
            <div className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="h-12 w-12 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center glow-green">
                    <Send className="h-7 w-7 text-white" />
                  </div>
                </div>
                <div className="ml-6 w-0 flex-1">
                  <dl>
                    <dt className="text-lg font-semibold text-gray-300 truncate">
                      TOTAL APPLICATIONS
                    </dt>
                    <dd className="text-3xl font-bold text-green-400">
                      {stats.totalApplications}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="card-futuristic overflow-hidden rounded-2xl">
            <div className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="h-12 w-12 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-xl flex items-center justify-center">
                    <Clock className="h-7 w-7 text-white" />
                  </div>
                </div>
                <div className="ml-6 w-0 flex-1">
                  <dl>
                    <dt className="text-lg font-semibold text-gray-300 truncate">
                      PENDING
                    </dt>
                    <dd className="text-3xl font-bold text-yellow-400">
                      {stats.pendingApplications}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="card-futuristic overflow-hidden rounded-2xl">
            <div className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="h-12 w-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
                    <TrendingUp className="h-7 w-7 text-white" />
                  </div>
                </div>
                <div className="ml-6 w-0 flex-1">
                  <dl>
                    <dt className="text-lg font-semibold text-gray-300 truncate">
                      THIS WEEK
                    </dt>
                    <dd className="text-3xl font-bold text-purple-400">
                      {stats.recentApplications}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div>
          <h2 className="text-3xl font-bold text-gray-200 mb-8">QUICK ACTIONS</h2>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {quickActions.map((action) => {
              const Icon = action.icon
              return (
                <a
                  key={action.name}
                  href={action.href}
                  className="relative group card-futuristic p-8 rounded-2xl transition-all duration-300 hover:scale-105"
                >
                  <div className="flex flex-col items-center text-center">
                    <div className="mb-6">
                      <span className={`rounded-2xl inline-flex p-4 ${action.color} text-white glow-green`}>
                        <Icon className="h-10 w-10" />
                      </span>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-200 mb-3">
                        {action.name.toUpperCase()}
                      </h3>
                      <p className="text-gray-400 text-lg">
                        {action.description}
                      </p>
                    </div>
                  </div>
                  <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="w-3 h-3 bg-cyan-400 rounded-full animate-pulse"></div>
                  </div>
                </a>
              )
            })}
          </div>
        </div>

        {/* Recent Applications */}
        {recentApplications.length > 0 && (
          <div>
            <h2 className="text-3xl font-bold text-gray-200 mb-8">RECENT APPLICATIONS</h2>
            <div className="card-futuristic overflow-hidden rounded-2xl">
              <ul className="divide-y divide-gray-700">
                {recentApplications.map((application) => (
                  <li key={application.id}>
                    <div className="px-6 py-6 flex items-center justify-between hover:bg-gray-800/30 transition-colors">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          {application.status === 'submitted' ? (
                            <div className="h-12 w-12 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center glow-green">
                              <CheckCircle className="h-7 w-7 text-white" />
                            </div>
                          ) : application.status === 'draft' ? (
                            <div className="h-12 w-12 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-xl flex items-center justify-center">
                              <Clock className="h-7 w-7 text-white" />
                            </div>
                          ) : (
                            <div className="h-12 w-12 bg-gradient-to-br from-gray-500 to-gray-600 rounded-xl flex items-center justify-center">
                              <AlertCircle className="h-7 w-7 text-white" />
                            </div>
                          )}
                        </div>
                        <div className="ml-6">
                          <div className="text-lg font-bold text-gray-200">
                            {application.jobs?.title || 'Unknown Position'}
                          </div>
                          <div className="text-gray-400 text-lg">
                            {application.jobs?.company || 'Unknown Company'}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <span className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-bold ${getStatusColor(application.status)}`}>
                          {application.status.replace('_', ' ').toUpperCase()}
                        </span>
                        <div className="text-gray-400 text-lg">
                          {new Date(application.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
