import React, { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { useRouter } from 'next/router'
import DashboardLayout from '../../components/DashboardLayout'
import { 
  Send, 
  CheckCircle, 
  Clock,
  AlertCircle,
  Eye,
  ExternalLink,
  Filter,
  RefreshCw,
  Play,
  Pause,
  Activity,
  TrendingUp,
  Users,
  Zap,
  FileText,
  Award,
  ThumbsUp
} from 'lucide-react'
import toast from 'react-hot-toast'
import apiClient from '../../lib/api'
import ApplicationMaterialsModal from '../../components/ApplicationMaterialsModal'

interface Application {
  id: string
  user_id: string
  job_id: string
  status: 'draft' | 'not_viable' | 'materials_ready' | 'submitted' | 'under_review' | 'interview' | 'rejected' | 'accepted' | 'pending' | 'applied' | 'failed' | 'skipped'
  created_at: string
  updated_at: string
  artifacts?: {
    cover_letter?: string
    match_analysis?: {
      match_score: number
      key_strengths: string[]
      areas_to_address: string[]
      gaps: string[]
      recommendations: string[]
      should_apply: boolean
      reasoning: string
    }
    resume_version?: string
  }
  attempt_meta?: {
    queued_at?: string
    applied_at?: string
    materials_generated_at?: string
    rejected_at?: string
    rejection_reason?: string
    method?: string
    match_score?: number
    ai_agent?: string
    note?: string
    ai_reasoning?: string
  }
  jobs?: Job
}

interface Job {
  id: string
  title: string
  company: string
  location?: string
  source: string
  raw?: any
}

interface WorkerStatus {
  status_counts: Record<string, number>
  recent_applications: Application[]
  worker_active: boolean
  last_updated?: string
}

export default function Applications() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [applications, setApplications] = useState<Application[]>([])
  const [statusGroups, setStatusGroups] = useState<Record<string, Application[]>>({})
  const [loadingApps, setLoadingApps] = useState(true)
  const [filter, setFilter] = useState('all')
  const [workerStatus, setWorkerStatus] = useState<WorkerStatus | null>(null)
  const [loadingWorker, setLoadingWorker] = useState(false)
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [detailsLoading, setDetailsLoading] = useState(false)
  const [detailsError, setDetailsError] = useState<string | null>(null)
  const [applicationDetails, setApplicationDetails] = useState<any | null>(null)
  const [workerHealth, setWorkerHealth] = useState<any | null>(null)
  const [workerControlLoading, setWorkerControlLoading] = useState(false)
  const [materialsModalOpen, setMaterialsModalOpen] = useState(false)
  const [selectedApplication, setSelectedApplication] = useState<Application | null>(null)

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      fetchApplications()
      fetchWorkerStatus()
      fetchWorkerHealth()
    }
  }, [user])

  useEffect(() => {
    // Auto-refresh worker health every 30 seconds
    const interval = setInterval(() => {
      if (user) {
        fetchWorkerHealth()
      }
    }, 30000)
    
    return () => clearInterval(interval)
  }, [user])

  const fetchApplications = async () => {
    if (!user?.id) return
    
    setLoadingApps(true)
    try {
      const response = await apiClient.getUserApplications(user.id)
      setApplications(response.applications || [])
      setStatusGroups(response.status_groups || {})
    } catch (error: any) {
      console.error('Error fetching applications:', error)
      toast.error(error.response?.data?.detail || 'Failed to fetch applications')
    } finally {
      setLoadingApps(false)
    }
  }

  const fetchWorkerStatus = async () => {
    setLoadingWorker(true)
    try {
      const response = await apiClient.getWorkerStatus()
      setWorkerStatus(response)
    } catch (error: any) {
      console.error('Error fetching worker status:', error)
      toast.error(error.response?.data?.detail || 'Failed to fetch worker status')
    } finally {
      setLoadingWorker(false)
    }
  }

  const fetchWorkerHealth = async () => {
    try {
      const health = await apiClient.getWorkerHealth()
      setWorkerHealth(health)
    } catch (error: any) {
      console.error('Error fetching worker health:', error)
    }
  }

  const startWorker = async () => {
    setWorkerControlLoading(true)
    try {
      await apiClient.startWorker(300, true)
      toast.success('Worker started successfully!')
      await fetchWorkerHealth()
      await fetchWorkerStatus()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to start worker')
    } finally {
      setWorkerControlLoading(false)
    }
  }

  const stopWorker = async () => {
    setWorkerControlLoading(true)
    try {
      await apiClient.stopWorker(false)
      toast.success('Worker stopped successfully!')
      await fetchWorkerHealth()
      await fetchWorkerStatus()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to stop worker')
    } finally {
      setWorkerControlLoading(false)
    }
  }

  const restartWorker = async () => {
    setWorkerControlLoading(true)
    try {
      await apiClient.restartWorker(300, true)
      toast.success('Worker restarted successfully!')
      await fetchWorkerHealth()
      await fetchWorkerStatus()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to restart worker')
    } finally {
      setWorkerControlLoading(false)
    }
  }

  const refreshData = async () => {
    await Promise.all([fetchApplications(), fetchWorkerStatus(), fetchWorkerHealth()])
  }

  const openDetails = async (applicationId: string) => {
    setDetailsError(null)
    setDetailsLoading(true)
    setDetailsOpen(true)
    try {
      const data = await apiClient.getApplicationDetails(applicationId)
      setApplicationDetails(data)
    } catch (error: any) {
      console.error('Error fetching application details:', error)
      setDetailsError(error.response?.data?.detail || 'Failed to load application details')
    } finally {
      setDetailsLoading(false)
    }
  }

  const openMaterialsModal = (application: Application) => {
    setSelectedApplication(application)
    setMaterialsModalOpen(true)
  }

  const handleMarkAsManuallySubmitted = async () => {
    if (!selectedApplication) return

    try {
      // Call backend to mark as manually submitted
      await apiClient.markApplicationAsManuallySubmitted(selectedApplication.id)
      
      toast.success('Application marked as manually submitted!')
      setMaterialsModalOpen(false)
      setSelectedApplication(null)
      
      // Refresh applications list
      await fetchApplications()
    } catch (error: any) {
      console.error('Error marking as manually submitted:', error)
      toast.error(error.response?.data?.detail || 'Failed to mark as submitted')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      case 'not_viable':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30'
      case 'materials_ready':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30'
      case 'submitted':
      case 'applied':
        return 'bg-green-500/20 text-green-400 border-green-500/30'
      case 'under_review':
        return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30'
      case 'interview':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
      case 'pending':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      case 'failed':
      case 'rejected':
        return 'bg-red-500/20 text-red-400 border-red-500/30'
      case 'accepted':
        return 'bg-teal-500/20 text-teal-400 border-teal-500/30'
      case 'skipped':
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'draft':
        return <Clock className="h-5 w-5 text-blue-400" />
      case 'not_viable':
        return <AlertCircle className="h-5 w-5 text-orange-400" />
      case 'materials_ready':
        return <FileText className="h-5 w-5 text-purple-400" />
      case 'submitted':
      case 'applied':
        return <CheckCircle className="h-5 w-5 text-green-400" />
      case 'under_review':
        return <Eye className="h-5 w-5 text-cyan-400" />
      case 'interview':
        return <Users className="h-5 w-5 text-emerald-400" />
      case 'accepted':
        return <Award className="h-5 w-5 text-teal-400" />
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-400" />
      case 'failed':
      case 'rejected':
        return <AlertCircle className="h-5 w-5 text-red-400" />
      case 'skipped':
        return <Pause className="h-5 w-5 text-gray-400" />
      default:
        return <Clock className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'draft':
        return 'Queued'
      case 'not_viable':
        return 'Not Recommended'
      case 'materials_ready':
        return 'Materials Ready'
      case 'submitted':
      case 'applied':
        return 'Submitted'
      case 'under_review':
        return 'Under Review'
      case 'interview':
        return 'Interview'
      case 'accepted':
        return 'Accepted'
      case 'rejected':
        return 'Rejected'
      case 'pending':
        return 'Pending'
      case 'failed':
        return 'Failed'
      case 'skipped':
        return 'Skipped'
      default:
        return status.charAt(0).toUpperCase() + status.slice(1)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  const calculateUptime = (startedAt: string) => {
    const start = new Date(startedAt)
    const now = new Date()
    const diffMs = now.getTime() - start.getTime()
    
    const hours = Math.floor(diffMs / (1000 * 60 * 60))
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  const filteredApplications = applications.filter(app => {
    if (filter === 'all') return true
    return app.status === filter
  })

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-cyan-600"></div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <>
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">
            APPLICATION MANAGEMENT
          </h1>
          <p className="mt-2 text-lg text-gray-300">
            Track and manage your job applications with AI-powered automation.
          </p>
        </div>

        {/* Worker Status Banner */}
        <div className="card-futuristic rounded-2xl p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Activity className={`h-6 w-6 ${workerHealth?.status?.running ? 'text-green-400' : 'text-gray-400'}`} />
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase">AI Worker Status</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`w-2 h-2 rounded-full ${workerHealth?.status?.running ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`}></span>
                  <span className={`text-lg font-bold ${workerHealth?.status?.running ? 'text-green-400' : 'text-gray-400'}`}>
                    {workerHealth?.status?.running ? 'ACTIVE' : 'INACTIVE'}
                  </span>
                  {workerHealth?.status?.running && workerHealth?.status?.pid && (
                    <span className="text-xs text-gray-500">
                      (PID: {workerHealth.status.pid})
                    </span>
                  )}
                </div>
              </div>
            </div>
            {workerHealth?.status?.running && (
              <div className="flex items-center gap-6 text-sm">
                <div>
                  <span className="text-gray-400">CPU:</span>
                  <span className="ml-2 font-bold text-cyan-400">{workerHealth.status.cpu_percent?.toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-gray-400">Memory:</span>
                  <span className="ml-2 font-bold text-purple-400">{workerHealth.status.memory_mb?.toFixed(0)} MB</span>
                </div>
                <div>
                  <span className="text-gray-400">Uptime:</span>
                  <span className="ml-2 font-bold text-green-400">
                    {workerHealth.status.started_at ? calculateUptime(workerHealth.status.started_at) : 'N/A'}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Application Statistics Dashboard */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {/* Draft (Queued) */}
          <div className="card-futuristic rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase">Queued</p>
                <p className="text-3xl font-bold text-blue-400 mt-2">
                  {applications.filter(a => a.status === 'draft').length}
                </p>
              </div>
              <Clock className="h-8 w-8 text-blue-400 opacity-50" />
            </div>
          </div>

          {/* Materials Ready */}
          <div className="card-futuristic rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase">Ready</p>
                <p className="text-3xl font-bold text-purple-400 mt-2">
                  {applications.filter(a => a.status === 'materials_ready').length}
                </p>
              </div>
              <FileText className="h-8 w-8 text-purple-400 opacity-50" />
            </div>
          </div>

          {/* Submitted */}
          <div className="card-futuristic rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase">Submitted</p>
                <p className="text-3xl font-bold text-green-400 mt-2">
                  {applications.filter(a => ['submitted', 'applied', 'under_review', 'interview'].includes(a.status)).length}
                </p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-400 opacity-50" />
            </div>
          </div>

          {/* Not Viable (Rejected by AI) */}
          <div className="card-futuristic rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase">Not Viable</p>
                <p className="text-3xl font-bold text-orange-400 mt-2">
                  {applications.filter(a => a.status === 'not_viable').length}
                </p>
              </div>
              <AlertCircle className="h-8 w-8 text-orange-400 opacity-50" />
            </div>
          </div>

          {/* Rejected by Employer */}
          <div className="card-futuristic rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase">Rejected</p>
                <p className="text-3xl font-bold text-red-400 mt-2">
                  {applications.filter(a => ['rejected', 'failed'].includes(a.status)).length}
                </p>
              </div>
              <AlertCircle className="h-8 w-8 text-red-400 opacity-50" />
            </div>
          </div>
        </div>

        {/* Worker Controls */}
        <div className="card-futuristic rounded-2xl p-8">
          <div className="flex items-center justify-between mb-6">
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-gray-200 flex items-center">
                <Zap className="h-8 w-8 text-cyan-400 mr-3" />
                AI APPLICATION WORKER
              </h2>
              <div className="flex items-center gap-3 mt-2">
                {workerHealth?.status?.running ? (
                  <>
                    <span className="flex items-center gap-2">
                      <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                      <span className="text-lg font-semibold text-green-400">Running</span>
                    </span>
                    {workerHealth?.status?.pid && (
                      <span className="text-sm text-gray-400">
                        (PID: {workerHealth.status.pid})
                      </span>
                    )}
                  </>
                ) : (
                  <>
                    <span className="flex items-center gap-2">
                      <span className="w-3 h-3 bg-gray-500 rounded-full"></span>
                      <span className="text-lg font-semibold text-gray-400">Stopped</span>
                    </span>
                  </>
                )}
              </div>
            </div>
            
            {/* Worker Control Buttons */}
            <div className="flex items-center gap-3">
              {workerHealth?.status?.running ? (
                <>
                  <button
                    onClick={restartWorker}
                    disabled={workerControlLoading}
                    className="btn-futuristic px-6 py-3 text-sm font-bold rounded-xl bg-yellow-600/20 hover:bg-yellow-600/30 border border-yellow-500/30 text-yellow-400 flex items-center gap-2"
                  >
                    <RefreshCw className={`h-5 w-5 ${workerControlLoading ? 'animate-spin' : ''}`} />
                    RESTART
                  </button>
                  <button
                    onClick={stopWorker}
                    disabled={workerControlLoading}
                    className="btn-futuristic px-6 py-3 text-sm font-bold rounded-xl bg-red-600/20 hover:bg-red-600/30 border border-red-500/30 text-red-400 flex items-center gap-2"
                  >
                    <Pause className="h-5 w-5" />
                    STOP
                  </button>
                </>
              ) : (
                <button
                  onClick={startWorker}
                  disabled={workerControlLoading}
                  className="btn-futuristic px-6 py-3 text-sm font-bold rounded-xl bg-green-600/20 hover:bg-green-600/30 border border-green-500/30 text-green-400 flex items-center gap-2"
                >
                  <Play className="h-5 w-5" />
                  START WORKER
                </button>
              )}
              <button
                onClick={refreshData}
                disabled={loadingApps || loadingWorker}
                className="btn-futuristic px-6 py-3 text-sm font-bold rounded-xl flex items-center gap-2"
              >
                <RefreshCw className={`h-5 w-5 ${loadingApps || loadingWorker ? 'animate-spin' : ''}`} />
                REFRESH
              </button>
            </div>
          </div>

          {/* Worker Health Metrics */}
          {workerHealth?.status?.running && (
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                <p className="text-xs font-medium text-gray-400 mb-1">CPU Usage</p>
                <p className="text-2xl font-bold text-cyan-400">
                  {workerHealth.status.cpu_percent?.toFixed(1)}%
                </p>
              </div>
              <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                <p className="text-xs font-medium text-gray-400 mb-1">Memory</p>
                <p className="text-2xl font-bold text-purple-400">
                  {workerHealth.status.memory_mb?.toFixed(0)} MB
                </p>
              </div>
              <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                <p className="text-xs font-medium text-gray-400 mb-1">Uptime</p>
                <p className="text-2xl font-bold text-green-400">
                  {workerHealth.status.started_at ? calculateUptime(workerHealth.status.started_at) : 'N/A'}
                </p>
              </div>
              <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                <p className="text-xs font-medium text-gray-400 mb-1">Status</p>
                <p className="text-2xl font-bold text-yellow-400">
                  {workerHealth.status.status || 'N/A'}
                </p>
              </div>
            </div>
          )}

          {loadingWorker && (
            <div className="mt-6 p-6 bg-gradient-to-r from-cyan-500/20 to-green-500/20 rounded-2xl border border-cyan-500/30">
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-cyan-400 mr-3"></div>
                <span className="text-lg font-medium text-cyan-400">
                  Fetching worker status and application data...
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Applications List */}
        <div className="card-futuristic rounded-2xl">
          <div className="px-8 py-6 border-b border-gray-700">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-200">
                YOUR APPLICATIONS ({filteredApplications.length})
              </h2>
              <div className="flex items-center space-x-4">
                <select
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  className="input-futuristic px-4 py-2 rounded-lg text-gray-200"
                >
                  <option value="all">All Status</option>
                  <option value="draft">Draft (Queued)</option>
                  <option value="not_viable">Not Recommended (AI Rejected)</option>
                  <option value="materials_ready">Materials Ready</option>
                  <option value="submitted">Submitted</option>
                  <option value="under_review">Under Review</option>
                  <option value="interview">Interview</option>
                  <option value="accepted">Accepted</option>
                  <option value="rejected">Rejected</option>
                  <option value="pending">Pending</option>
                  <option value="applied">Applied</option>
                  <option value="failed">Failed</option>
                  <option value="skipped">Skipped</option>
                </select>
              </div>
            </div>
          </div>

          {loadingApps ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400 mx-auto"></div>
              <p className="mt-4 text-lg text-gray-300">Loading applications...</p>
            </div>
          ) : filteredApplications.length === 0 ? (
            <div className="p-12 text-center">
              <Send className="h-16 w-16 text-gray-500 mx-auto mb-4" />
              <p className="text-lg text-gray-300">
                {filter === 'all' 
                  ? 'No applications found. Queue some jobs to get started!'
                  : `No applications with status "${filter}" found.`
                }
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-700">
              {filteredApplications.map((application) => (
                <div key={application.id} className="p-8 hover:bg-gray-800/30 transition-all duration-300">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-6">
                      <div className="flex-shrink-0">
                        {getStatusIcon(application.status)}
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center space-x-4 mb-3">
                          <h3 className="text-xl font-bold text-gray-200">
                            {application.jobs?.title || 'Unknown Position'}
                          </h3>
                          <span className={`inline-flex items-center px-4 py-2 rounded-xl text-sm font-bold border ${getStatusColor(application.status)}`}>
                            {getStatusLabel(application.status)}
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-6 text-sm text-gray-400 mb-4">
                          <span className="font-medium">{application.jobs?.company || 'Unknown Company'}</span>
                          {application.jobs?.location && (
                            <>
                              <span>•</span>
                              <span>{application.jobs.location}</span>
                            </>
                          )}
                          <span>•</span>
                          <span>Applied {formatDate(application.created_at)}</span>
                          {application.updated_at !== application.created_at && (
                            <>
                              <span>•</span>
                              <span>Updated {formatDate(application.updated_at)}</span>
                            </>
                          )}
                        </div>

                        {/* Show AI Analysis only for materials_ready or not_viable status */}
                        {(application.status === 'materials_ready' || application.status === 'not_viable') && application.artifacts?.match_analysis && (
                          <div className="mt-4 p-4 bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl border border-gray-600">
                            <div className="text-sm">
                              <div className="flex items-center space-x-4 mb-3">
                                <span className="font-bold text-cyan-400">
                                  AI Analysis
                                </span>
                                <div className="flex items-center gap-3">
                                  <span className="text-gray-400 text-xs">Match Score:</span>
                                  <div className={`px-3 py-1 rounded-lg text-xs font-bold ${
                                    (application.artifacts.match_analysis.match_score || 0) >= 80 
                                      ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                                      : (application.artifacts.match_analysis.match_score || 0) >= 60
                                      ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                                      : 'bg-red-500/20 text-red-400 border border-red-500/30'
                                  }`}>
                                    {application.artifacts.match_analysis.match_score}/100
                                  </div>
                                </div>
                              </div>
                              
                              {application.artifacts.match_analysis.reasoning && (
                                <p className="text-gray-400 text-xs mt-2 line-clamp-2">
                                  {application.artifacts.match_analysis.reasoning}
                                </p>
                              )}

                              {application.artifacts.cover_letter && (
                                <div className="mt-3 pt-3 border-t border-gray-700">
                                  <p className="text-gray-300 text-xs font-medium mb-1">✓ Cover Letter Generated ({application.artifacts.cover_letter.length} chars)</p>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Show Processing Info for materials_ready */}
                        {application.status === 'materials_ready' && application.attempt_meta?.materials_generated_at && (
                          <div className="mt-3 p-3 bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-lg border border-purple-500/30">
                            <p className="text-xs text-purple-400">
                              <span className="font-bold">AI Processed:</span> {formatDate(application.attempt_meta.materials_generated_at)}
                              {application.attempt_meta.ai_agent && (
                                <span className="ml-3 text-gray-400">
                                  ({application.attempt_meta.ai_agent})
                                </span>
                              )}
                            </p>
                          </div>
                        )}

                        {/* Show Rejection Info for not_viable */}
                        {application.status === 'not_viable' && application.attempt_meta && (
                          <div className="mt-3 p-3 bg-gradient-to-r from-orange-500/10 to-red-500/10 rounded-lg border border-orange-500/30">
                            <p className="text-xs text-orange-400">
                              <span className="font-bold">AI Rejected:</span> {application.attempt_meta.rejected_at ? formatDate(application.attempt_meta.rejected_at) : 'Recently'}
                              <br />
                              <span className="text-gray-400 italic">{application.attempt_meta.rejection_reason || 'Not a good match'}</span>
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="ml-6 flex flex-col items-end space-y-3">
                      {/* Show View Materials button for applications with materials_ready status */}
                      {application.status === 'materials_ready' && (
                        <button
                          onClick={() => openMaterialsModal(application)}
                          className="text-purple-400 hover:text-purple-300 text-sm font-bold flex items-center px-4 py-2 rounded-lg border border-purple-500/30 hover:bg-purple-500/10 transition-all duration-300"
                        >
                          <FileText className="h-4 w-4 mr-2" />
                          VIEW AI MATERIALS
                        </button>
                      )}
                      
                      <button
                        onClick={() => openDetails(application.id)}
                        className="text-cyan-400 hover:text-cyan-300 text-sm font-bold flex items-center px-4 py-2 rounded-lg border border-cyan-500/30 hover:bg-cyan-500/10 transition-all duration-300"
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        VIEW DETAILS
                      </button>
                      
                      {application.jobs?.raw?.url && (
                        <a
                          href={application.jobs.raw.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-green-400 hover:text-green-300 text-sm font-bold flex items-center px-4 py-2 rounded-lg border border-green-500/30 hover:bg-green-500/10 transition-all duration-300"
                        >
                          <ExternalLink className="h-4 w-4 mr-2" />
                          VIEW JOB
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>

    {/* Details Modal */}
    {detailsOpen && (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div className="absolute inset-0 bg-black/70" onClick={() => setDetailsOpen(false)} />
        <div className="relative z-10 w-full max-w-3xl card-futuristic rounded-2xl border border-gray-700 p-0 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-700 flex items-center justify-between">
            <h3 className="text-xl font-bold text-gray-200">Application Details</h3>
            <button
              onClick={() => setDetailsOpen(false)}
              className="text-gray-400 hover:text-gray-200"
            >
              ✕
            </button>
          </div>

          <div className="p-6 max-h-[70vh] overflow-y-auto">
            {detailsLoading ? (
              <div className="flex items-center justify-center py-10">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-cyan-400" />
                <span className="ml-3 text-gray-300">Loading...</span>
              </div>
            ) : detailsError ? (
              <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-300">
                {detailsError}
              </div>
            ) : applicationDetails ? (
              <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Status</p>
                    <span className={`inline-flex items-center px-3 py-1 rounded-lg text-xs font-bold border ${getStatusColor(applicationDetails.application?.status || 'draft')}`}>
                      {(applicationDetails.application?.status || 'draft').toUpperCase()}
                    </span>
                  </div>
                  {applicationDetails.job && (
                    <div className="text-right">
                      <p className="text-sm text-gray-400">Job</p>
                      <p className="text-lg font-semibold text-gray-200">{applicationDetails.job.title}</p>
                      <p className="text-gray-400">{applicationDetails.job.company}</p>
                    </div>
                  )}
                </div>

                {/* Attempt Meta */}
                {applicationDetails.application?.attempt_meta && (
                  <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                    <p className="text-sm text-blue-300 font-bold mb-2">Attempt Metadata</p>
                    <pre className="text-xs text-gray-300 whitespace-pre-wrap">
{JSON.stringify(applicationDetails.application.attempt_meta, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Artifacts */}
                {applicationDetails.application?.artifacts && (
                  <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                    <p className="text-sm text-green-300 font-bold mb-2">Artifacts</p>
                    <pre className="text-xs text-gray-300 whitespace-pre-wrap">
{JSON.stringify(applicationDetails.application.artifacts, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Raw */}
                {applicationDetails.job?.raw && (
                  <div className="p-4 bg-gray-800/50 border border-gray-700 rounded-lg">
                    <p className="text-sm text-gray-400 font-bold mb-2">Job Raw</p>
                    <pre className="text-xs text-gray-300 whitespace-pre-wrap">
{JSON.stringify(applicationDetails.job.raw, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-gray-400">No details available.</div>
            )}
          </div>
        </div>
      </div>
    )}

    {/* Application Materials Modal */}
    {selectedApplication && (
      <ApplicationMaterialsModal
        isOpen={materialsModalOpen}
        onClose={() => {
          setMaterialsModalOpen(false)
          setSelectedApplication(null)
        }}
        application={selectedApplication}
        onMarkAsManuallySubmitted={handleMarkAsManuallySubmitted}
      />
    )}
    </>
  )
}
