import React, { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { useRouter } from 'next/router'
import DashboardLayout from '../../components/DashboardLayout'
import { 
  TrendingUp,
  TrendingDown,
  Activity,
  Target,
  Award,
  Briefcase,
  Calendar,
  BarChart3,
  PieChart,
  Info,
  AlertCircle,
  Lightbulb,
  Star,
  RefreshCw
} from 'lucide-react'
import toast from 'react-hot-toast'
import apiClient from '../../lib/api'

interface Analytics {
  summary: {
    total_applications: number
    success_rate: number
    days_active: number
    avg_applications_per_day: number
  }
  status_breakdown: Record<string, number>
  timeline: {
    labels: string[]
    data: number[]
  }
  top_companies: Array<{company: string, count: number}>
  top_skills: Array<{skill: string, count: number}>
  recent_activity: Array<{
    date: string
    status: string
    job_title: string
    company: string
  }>
  insights: Array<{
    type: string
    message: string
    icon: string
  }>
}

export default function Analytics() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [loadingAnalytics, setLoadingAnalytics] = useState(true)
  const [timeRange, setTimeRange] = useState(30)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      fetchAnalytics()
    }
  }, [user, timeRange])

  const fetchAnalytics = async () => {
    if (!user?.id) return
    
    setLoadingAnalytics(true)
    try {
      const response = await apiClient.getUserAnalytics(user.id, timeRange)
      setAnalytics(response)
    } catch (error: any) {
      console.error('Error fetching analytics:', error)
      toast.error('Failed to load analytics')
    } finally {
      setLoadingAnalytics(false)
    }
  }

  const refreshAnalytics = async () => {
    setRefreshing(true)
    await fetchAnalytics()
    setRefreshing(false)
    toast.success('Analytics refreshed!')
  }

  const getInsightIcon = (iconName: string) => {
    const icons: Record<string, any> = {
      'trending_up': TrendingUp,
      'info': Info,
      'alert': AlertCircle,
      'lightbulb': Lightbulb,
      'star': Star,
      'target': Target
    }
    return icons[iconName] || Info
  }

  const getInsightColor = (type: string) => {
    const colors: Record<string, string> = {
      'positive': 'from-green-500 to-emerald-500',
      'neutral': 'from-blue-500 to-cyan-500',
      'warning': 'from-yellow-500 to-orange-500',
      'tip': 'from-purple-500 to-pink-500'
    }
    return colors[type] || 'from-gray-500 to-gray-600'
  }

  if (loading || loadingAnalytics) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
        </div>
      </DashboardLayout>
    )
  }

  if (!analytics) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-screen">
          <p className="text-gray-400">No analytics data available</p>
        </div>
      </DashboardLayout>
    )
  }

  const statusColors: Record<string, string> = {
    draft: 'bg-blue-500',
    submitted: 'bg-yellow-500',
    under_review: 'bg-purple-500',
    interview: 'bg-green-500',
    rejected: 'bg-red-500',
    accepted: 'bg-emerald-500'
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">
              ANALYTICS & INSIGHTS
            </h1>
            <p className="mt-2 text-lg text-gray-300">
              Track your job search performance and get AI-powered insights
            </p>
          </div>

          <div className="flex items-center space-x-4">
            {/* Time Range Selector */}
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(parseInt(e.target.value))}
              className="px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-gray-200 focus:border-cyan-500"
            >
              <option value={7}>Last 7 Days</option>
              <option value={30}>Last 30 Days</option>
              <option value={90}>Last 90 Days</option>
              <option value={365}>Last Year</option>
            </select>

            {/* Refresh Button */}
            <button
              onClick={refreshAnalytics}
              disabled={refreshing}
              className="btn-futuristic px-6 py-2 rounded-lg font-bold flex items-center"
            >
              <RefreshCw className={`h-5 w-5 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              REFRESH
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card-futuristic rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">TOTAL APPLICATIONS</p>
                <p className="text-3xl font-bold text-cyan-400 mt-2">
                  {analytics.summary.total_applications}
                </p>
              </div>
              <Briefcase className="h-12 w-12 text-cyan-400 opacity-50" />
            </div>
          </div>

          <div className="card-futuristic rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">SUCCESS RATE</p>
                <p className="text-3xl font-bold text-green-400 mt-2">
                  {analytics.summary.success_rate}%
                </p>
              </div>
              <TrendingUp className="h-12 w-12 text-green-400 opacity-50" />
            </div>
          </div>

          <div className="card-futuristic rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">AVG PER DAY</p>
                <p className="text-3xl font-bold text-purple-400 mt-2">
                  {analytics.summary.avg_applications_per_day}
                </p>
              </div>
              <Activity className="h-12 w-12 text-purple-400 opacity-50" />
            </div>
          </div>

          <div className="card-futuristic rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">DAYS ACTIVE</p>
                <p className="text-3xl font-bold text-yellow-400 mt-2">
                  {analytics.summary.days_active}
                </p>
              </div>
              <Calendar className="h-12 w-12 text-yellow-400 opacity-50" />
            </div>
          </div>
        </div>

        {/* AI Insights */}
        {analytics.insights && analytics.insights.length > 0 && (
          <div className="card-futuristic rounded-2xl p-8">
            <h2 className="text-2xl font-bold text-gray-200 mb-6 flex items-center">
              <Lightbulb className="h-6 w-6 mr-2 text-cyan-400" />
              AI-POWERED INSIGHTS
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {analytics.insights.map((insight, index) => {
                const Icon = getInsightIcon(insight.icon)
                const gradientClass = getInsightColor(insight.type)
                
                return (
                  <div
                    key={index}
                    className={`p-6 rounded-xl bg-gradient-to-r ${gradientClass} bg-opacity-10 border border-gray-700`}
                  >
                    <div className="flex items-start space-x-4">
                      <Icon className={`h-6 w-6 flex-shrink-0 mt-1 bg-gradient-to-r ${gradientClass} bg-clip-text text-transparent`} />
                      <p className="text-gray-200">{insight.message}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Applications Timeline */}
        <div className="card-futuristic rounded-2xl p-8">
          <h2 className="text-2xl font-bold text-gray-200 mb-6 flex items-center">
            <BarChart3 className="h-6 w-6 mr-2 text-cyan-400" />
            APPLICATIONS TIMELINE
          </h2>

          <div className="h-64 flex items-end justify-between space-x-2">
            {analytics.timeline.data.map((value, index) => {
              const maxValue = Math.max(...analytics.timeline.data, 1)
              const height = (value / maxValue) * 100
              const label = analytics.timeline.labels[index]
              
              return (
                <div key={index} className="flex-1 flex flex-col items-center">
                  <div className="w-full bg-gray-800 rounded-t-lg relative group cursor-pointer">
                    <div
                      className="w-full bg-gradient-to-t from-cyan-500 to-green-500 rounded-t-lg transition-all duration-300 hover:from-cyan-400 hover:to-green-400"
                      style={{ height: `${height}%` }}
                    >
                      {/* Tooltip */}
                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="bg-gray-900 px-3 py-2 rounded-lg text-sm whitespace-nowrap border border-gray-700">
                          <p className="text-gray-400">{label}</p>
                          <p className="text-cyan-400 font-bold">{value} apps</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2 rotate-45 origin-left">
                    {label.slice(5)}
                  </p>
                </div>
              )
            })}
          </div>
        </div>

        {/* Status Breakdown & Top Companies */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Status Breakdown */}
          <div className="card-futuristic rounded-2xl p-8">
            <h2 className="text-2xl font-bold text-gray-200 mb-6 flex items-center">
              <PieChart className="h-6 w-6 mr-2 text-cyan-400" />
              STATUS BREAKDOWN
            </h2>

            <div className="space-y-4">
              {Object.entries(analytics.status_breakdown).map(([status, count]) => {
                const total = Object.values(analytics.status_breakdown).reduce((a, b) => a + b, 0)
                const percentage = (count / total * 100).toFixed(1)
                const colorClass = statusColors[status] || 'bg-gray-500'
                
                return (
                  <div key={status}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-300 capitalize">{status.replace(/_/g, ' ')}</span>
                      <span className="text-gray-400 font-mono">{count} ({percentage}%)</span>
                    </div>
                    <div className="w-full bg-gray-800 rounded-full h-3">
                      <div
                        className={`${colorClass} h-3 rounded-full transition-all duration-300`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Top Companies */}
          <div className="card-futuristic rounded-2xl p-8">
            <h2 className="text-2xl font-bold text-gray-200 mb-6 flex items-center">
              <Award className="h-6 w-6 mr-2 text-cyan-400" />
              TOP COMPANIES
            </h2>

            <div className="space-y-4">
              {analytics.top_companies.slice(0, 8).map((item, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-green-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                      {index + 1}
                    </div>
                    <span className="text-gray-200">{item.company}</span>
                  </div>
                  <span className="text-cyan-400 font-bold">{item.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Top Skills */}
        <div className="card-futuristic rounded-2xl p-8">
          <h2 className="text-2xl font-bold text-gray-200 mb-6 flex items-center">
            <Target className="h-6 w-6 mr-2 text-cyan-400" />
            TOP SKILLS IN APPLIED JOBS
          </h2>

          <div className="flex flex-wrap gap-3">
            {analytics.top_skills.slice(0, 20).map((item, index) => (
              <div
                key={index}
                className="px-4 py-2 bg-gradient-to-r from-cyan-500/20 to-green-500/20 rounded-lg border border-cyan-500/30 hover:border-cyan-500 transition-all cursor-pointer"
              >
                <span className="text-gray-200">{item.skill}</span>
                <span className="ml-2 text-cyan-400 font-bold">×{item.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="card-futuristic rounded-2xl p-8">
          <h2 className="text-2xl font-bold text-gray-200 mb-6 flex items-center">
            <Activity className="h-6 w-6 mr-2 text-cyan-400" />
            RECENT ACTIVITY
          </h2>

          <div className="space-y-4">
            {analytics.recent_activity.map((activity, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg hover:bg-gray-900 transition-all"
              >
                <div className="flex items-center space-x-4">
                  <div className={`w-3 h-3 rounded-full ${statusColors[activity.status] || 'bg-gray-500'}`} />
                  <div>
                    <p className="text-gray-200 font-medium">{activity.job_title}</p>
                    <p className="text-sm text-gray-400">{activity.company}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-400">
                    {new Date(activity.date).toLocaleDateString()}
                  </p>
                  <p className={`text-xs capitalize ${
                    activity.status === 'accepted' ? 'text-green-400' :
                    activity.status === 'rejected' ? 'text-red-400' :
                    'text-gray-500'
                  }`}>
                    {activity.status.replace(/_/g, ' ')}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}

