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
  Zap
} from 'lucide-react'
import toast from 'react-hot-toast'
import apiClient from '../../lib/api'

interface Application {
  id: string
  user_id: string
  job_id: string
  status: 'pending' | 'applied' | 'failed' | 'skipped'
  created_at: string
  updated_at: string
  artifacts?: any
  attempt_meta?: any
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

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      fetchApplications()
      fetchWorkerStatus()
    }
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

  const refreshData = async () => {
    await Promise.all([fetchApplications(), fetchWorkerStatus()])
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      case 'applied':
        return 'bg-green-500/20 text-green-400 border-green-500/30'
      case 'pending':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      case 'failed':
        return 'bg-red-500/20 text-red-400 border-red-500/30'
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
      case 'applied':
        return <CheckCircle className="h-5 w-5 text-green-400" />
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-400" />
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-400" />
      case 'skipped':
        return <Pause className="h-5 w-5 text-gray-400" />
      default:
        return <Clock className="h-5 w-5 text-gray-400" />
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
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

        {/* Worker Status Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Worker Status Card */}
          <div className="card-futuristic rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">WORKER STATUS</p>
                <div className="flex items-center mt-2">
                  <div className={`h-3 w-3 rounded-full mr-2 ${workerStatus?.worker_active ? 'bg-green-400 glow-green' : 'bg-red-400'}`}></div>
                  <span className="text-lg font-bold text-gray-200">
                    {workerStatus?.worker_active ? 'ACTIVE' : 'INACTIVE'}
                  </span>
                </div>
              </div>
              <Activity className="h-8 w-8 text-cyan-400" />
            </div>
          </div>

          {/* Pending Applications */}
          <div className="card-futuristic rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">PENDING</p>
                <p className="text-2xl font-bold text-yellow-400">
                  {workerStatus?.status_counts?.pending || 0}
                </p>
              </div>
              <Clock className="h-8 w-8 text-yellow-400" />
            </div>
          </div>

          {/* Applied Applications */}
          <div className="card-futuristic rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">APPLIED</p>
                <p className="text-2xl font-bold text-green-400">
                  {workerStatus?.status_counts?.applied || 0}
                </p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-400" />
            </div>
          </div>

          {/* Failed Applications */}
          <div className="card-futuristic rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">FAILED</p>
                <p className="text-2xl font-bold text-red-400">
                  {workerStatus?.status_counts?.failed || 0}
                </p>
              </div>
              <AlertCircle className="h-8 w-8 text-red-400" />
            </div>
          </div>
        </div>

        {/* Worker Controls */}
        <div className="card-futuristic rounded-2xl p-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-200 flex items-center">
                <Zap className="h-8 w-8 text-cyan-400 mr-3" />
                AI APPLICATION WORKER
              </h2>
              <p className="text-lg text-gray-300 mt-2">
                Automatically process applications with AI analysis and submission.
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={refreshData}
                disabled={loadingApps || loadingWorker}
                className="btn-futuristic px-8 py-4 text-lg font-bold rounded-xl flex items-center"
              >
                <RefreshCw className={`h-6 w-6 mr-3 ${loadingApps || loadingWorker ? 'animate-spin' : ''}`} />
                REFRESH DATA
              </button>
            </div>
          </div>

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
                  <option value="draft">Draft</option>
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
                            {application.job_id || 'Unknown Position'}
                          </h3>
                          <span className={`inline-flex items-center px-4 py-2 rounded-xl text-sm font-bold border ${getStatusColor(application.status)}`}>
                            {application.status.toUpperCase()}
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-6 text-lg text-gray-400 mb-4">
                          <span className="font-medium">Job ID: {application.job_id}</span>
                          <span>•</span>
                          <span>Created {formatDate(application.created_at)}</span>
                          {application.updated_at !== application.created_at && (
                            <>
                              <span>•</span>
                              <span>Updated {formatDate(application.updated_at)}</span>
                            </>
                          )}
                        </div>

                        {application.artifacts && (
                          <div className="mt-4 p-4 bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-xl border border-gray-600">
                            <div className="text-sm">
                              <div className="flex items-center space-x-4 mb-3">
                                <span className="font-bold text-cyan-400">
                                  AI Analysis Available
                                </span>
                                <span className="px-3 py-1 rounded-lg text-xs font-bold bg-green-500/20 text-green-400 border border-green-500/30">
                                  PROCESSED
                                </span>
                              </div>
                              
                              {application.artifacts.match_analysis && (
                                <div className="mb-3">
                                  <p className="text-gray-300 text-sm">
                                    Match Score: <span className="font-bold text-cyan-400">{application.artifacts.match_analysis.match_score}%</span>
                                  </p>
                                  {application.artifacts.match_analysis.reasoning && (
                                    <p className="text-gray-400 text-xs mt-1">
                                      {application.artifacts.match_analysis.reasoning}
                                    </p>
                                  )}
                                </div>
                              )}

                              {application.artifacts.cover_letter && (
                                <div className="mt-3">
                                  <p className="text-gray-300 text-sm font-medium mb-1">Cover Letter Generated:</p>
                                  <p className="text-gray-400 text-xs line-clamp-2">
                                    {application.artifacts.cover_letter.substring(0, 200)}...
                                  </p>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {application.attempt_meta && (
                          <div className="mt-3 p-3 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-lg border border-blue-500/30">
                            <p className="text-sm text-blue-400">
                              <span className="font-bold">Attempts:</span> {application.attempt_meta.attempt_count || 0}
                              {application.attempt_meta.queued_at && (
                                <span className="ml-4">
                                  <span className="font-bold">Queued:</span> {formatDate(application.attempt_meta.queued_at)}
                                </span>
                              )}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="ml-6 flex flex-col items-end space-y-3">
                      <button
                        onClick={() => openDetails(application.id)}
                        className="text-cyan-400 hover:text-cyan-300 text-sm font-bold flex items-center px-4 py-2 rounded-lg border border-cyan-500/30 hover:bg-cyan-500/10 transition-all duration-300"
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        VIEW DETAILS
                      </button>
                      
                      <button
                        onClick={() => {
                          // This would show job details
                          toast.success('Job details would open here')
                        }}
                        className="text-green-400 hover:text-green-300 text-sm font-bold flex items-center px-4 py-2 rounded-lg border border-green-500/30 hover:bg-green-500/10 transition-all duration-300"
                      >
                        <ExternalLink className="h-4 w-4 mr-2" />
                        VIEW JOB
                      </button>
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
    </>
  )
}
