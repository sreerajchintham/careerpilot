import React, { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { useRouter } from 'next/router'
import DashboardLayout from '../../components/DashboardLayout'
import { 
  Search, 
  Play, 
  CheckCircle, 
  AlertCircle,
  Clock,
  ExternalLink,
  Filter,
  RefreshCw
} from 'lucide-react'
import toast from 'react-hot-toast'
import { supabase, Job } from '../../lib/supabase'
import apiClient from '../../lib/api'

interface JobWithMatch extends Job {
  matchScore?: number
  matchPercentage?: number
}

export default function JobScraping() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [scraping, setScraping] = useState(false)
  const [jobs, setJobs] = useState<JobWithMatch[]>([])
  const [loadingJobs, setLoadingJobs] = useState(true)
  const [queueingJobs, setQueueingJobs] = useState<Set<string>>(new Set())
  const [loadingMatches, setLoadingMatches] = useState(false)
  const [filters, setFilters] = useState({
    keywords: 'Software Engineer',
    location: 'Remote',
    source: 'all',
    maxResults: 50
  })

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      fetchJobs()
      fetchJobMatches()
    }
  }, [user])

  const fetchJobs = async () => {
    setLoadingJobs(true)
    try {
      const { data, error } = await supabase
        .from('jobs')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(100)

      if (error) throw error
      setJobs(data || [])
    } catch (error) {
      console.error('Error fetching jobs:', error)
      toast.error('Failed to fetch jobs')
    } finally {
      setLoadingJobs(false)
    }
  }

  const fetchJobMatches = async () => {
    if (!user) return
    
    setLoadingMatches(true)
    try {
      const matchData = await apiClient.getUserJobMatches(user.id, 100)
      
      if (matchData.matches && matchData.matches.length > 0) {
        // Create a map of job ID to match score
        const matchScores = new Map<string, { score: number; percentage: number }>()
        matchData.matches.forEach((match: any) => {
          matchScores.set(match.job.id, {
            score: match.score,
            percentage: match.match_percentage
          })
        })
        
        // Update jobs with match scores
        setJobs(prevJobs => 
          prevJobs.map(job => ({
            ...job,
            matchScore: matchScores.get(job.id)?.score,
            matchPercentage: matchScores.get(job.id)?.percentage
          }))
        )
        
        toast.success(`Computed match scores for ${matchData.matches.length} jobs`)
      }
    } catch (error) {
      console.error('Error fetching job matches:', error)
      // Don't show error toast - matching is optional
    } finally {
      setLoadingMatches(false)
    }
  }

  const startScraping = async () => {
    setScraping(true)
    try {
      const res = await apiClient.startScraping({ api: 'all', keywords: filters.keywords, location: filters.location, max_results: filters.maxResults })
      toast.success(`${res.message} (sources: ${res.sources.join(', ') || 'n/a'})`)
      await fetchJobs()
      await fetchJobMatches() // Recompute matches after scraping
    } catch (error: any) {
      console.error('Scrape error:', error)
      toast.error(error.response?.data?.detail || 'Failed to start scraping')
    } finally {
      setScraping(false)
    }
  }

  const getMatchColor = (percentage?: number) => {
    if (!percentage) return 'bg-gray-100 text-gray-800'
    if (percentage >= 80) return 'bg-green-100 text-green-800 border-green-300'
    if (percentage >= 60) return 'bg-blue-100 text-blue-800 border-blue-300'
    if (percentage >= 40) return 'bg-yellow-100 text-yellow-800 border-yellow-300'
    return 'bg-orange-100 text-orange-800 border-orange-300'
  }

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'remoteok':
        return 'bg-green-100 text-green-800'
      case 'themuse':
        return 'bg-blue-100 text-blue-800'
      case 'adzuna':
        return 'bg-purple-100 text-purple-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  const queueJobForApplication = async (jobId: string) => {
    if (!user) {
      toast.error('Please log in to queue applications')
      return
    }

    // Find the job to validate it has a URL
    const job = jobs.find(j => j.id === jobId)
    
    if (!job) {
      toast.error('Job not found')
      return
    }

    // CRITICAL: Check if job has an application URL
    if (!job.raw?.url || !job.raw.url.trim()) {
      toast.error(
        `Cannot queue "${job.title}" - This job has no application URL. ` +
        `Please contact the company directly or find a different posting.`,
        { duration: 6000 }
      )
      return
    }

    // Add job to queueing set
    setQueueingJobs(prev => new Set(prev).add(jobId))

    try {
      // Call the backend API to queue the application
      await apiClient.queueApplications({
        user_id: user.id,
        job_ids: [jobId]
      })

      toast.success('Job queued for application! Check the Applications page.')
    } catch (error: any) {
      console.error('Error queueing job:', error)
      
      // Handle URL validation errors from backend
      const errorDetail = error.response?.data?.detail
      if (errorDetail && typeof errorDetail === 'object' && errorDetail.jobs_without_urls) {
        const jobsWithoutUrls = errorDetail.jobs_without_urls
        toast.error(
          `Cannot queue jobs without application URLs:\n${jobsWithoutUrls.map((j: any) => `• ${j.title} at ${j.company}`).join('\n')}`,
          { duration: 8000 }
        )
      } else {
        toast.error(errorDetail?.error || errorDetail || 'Failed to queue job for application')
      }
    } finally {
      // Remove job from queueing set
      setQueueingJobs(prev => {
        const newSet = new Set(prev)
        newSet.delete(jobId)
        return newSet
      })
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

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Job Scraping</h1>
          <p className="mt-1 text-sm text-gray-500">
            Discover new job opportunities from multiple sources.
          </p>
        </div>

        {/* Scraping Controls */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Start Job Scraping</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Keywords
              </label>
              <input
                type="text"
                value={filters.keywords}
                onChange={(e) => setFilters(prev => ({ ...prev, keywords: e.target.value }))}
                className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="e.g., Python Developer"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Location
              </label>
              <input
                type="text"
                value={filters.location}
                onChange={(e) => setFilters(prev => ({ ...prev, location: e.target.value }))}
                className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="e.g., Remote, San Francisco"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source
              </label>
              <select
                value={filters.source}
                onChange={(e) => setFilters(prev => ({ ...prev, source: e.target.value }))}
                className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="all">All Sources</option>
                <option value="remoteok">Remote OK</option>
                <option value="themuse">The Muse</option>
                <option value="adzuna">Adzuna</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Results
              </label>
              <select
                value={filters.maxResults}
                onChange={(e) => setFilters(prev => ({ ...prev, maxResults: parseInt(e.target.value) }))}
                className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value={25}>25 jobs</option>
                <option value={50}>50 jobs</option>
                <option value={100}>100 jobs</option>
              </select>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <button
              onClick={startScraping}
              disabled={scraping}
              className="bg-indigo-600 text-white px-6 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {scraping ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Scraping...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Start Scraping
                </>
              )}
            </button>

            <button
              onClick={fetchJobs}
              disabled={loadingJobs}
              className="bg-gray-600 text-white px-6 py-2 rounded-md text-sm font-medium hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loadingJobs ? 'animate-spin' : ''}`} />
              Refresh Jobs
            </button>
          </div>

          {scraping && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center">
                <Clock className="h-5 w-5 text-blue-400" />
                <span className="ml-2 text-sm font-medium text-blue-800">
                  Scraping in progress... This may take a few minutes.
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Jobs List */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-medium text-gray-900">
                Available Jobs ({jobs.length})
              </h2>
              <div className="flex items-center space-x-2">
                <Filter className="h-4 w-4 text-gray-400" />
                <span className="text-sm text-gray-500">Latest first</span>
              </div>
            </div>
          </div>

          {loadingJobs ? (
            <div className="p-6 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
              <p className="mt-2 text-sm text-gray-500">Loading jobs...</p>
            </div>
          ) : jobs.length === 0 ? (
            <div className="p-6 text-center">
              <AlertCircle className="h-12 w-12 text-gray-400 mx-auto" />
              <p className="mt-2 text-sm text-gray-500">No jobs found. Start scraping to discover opportunities!</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {jobs.map((job) => (
                <div key={job.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="text-lg font-medium text-gray-900">
                          {job.title}
                        </h3>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSourceColor(job.source)}`}>
                          {job.source}
                        </span>
                        {job.matchPercentage !== undefined && (
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold border ${getMatchColor(job.matchPercentage)}`}>
                            {job.matchPercentage}% Match
                          </span>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-4 text-sm text-gray-500 mb-2">
                        <span className="font-medium">{job.company}</span>
                        {job.location && (
                          <>
                            <span>•</span>
                            <span>{job.location}</span>
                          </>
                        )}
                        {job.posted_at && (
                          <>
                            <span>•</span>
                            <span>Posted {formatDate(job.posted_at)}</span>
                          </>
                        )}
                      </div>

                      {job.raw.description && (
                        <p className="text-sm text-gray-600 line-clamp-2">
                          {job.raw.description.substring(0, 200)}...
                        </p>
                      )}

                      {job.raw.requirements && job.raw.requirements.length > 0 && (
                        <div className="mt-2">
                          <div className="flex flex-wrap gap-1">
                            {job.raw.requirements.slice(0, 5).map((req, index) => (
                              <span
                                key={index}
                                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                              >
                                {req}
                              </span>
                            ))}
                            {job.raw.requirements.length > 5 && (
                              <span className="text-xs text-gray-500">
                                +{job.raw.requirements.length - 5} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="ml-4 flex flex-col items-end space-y-2">
                      {job.raw.url ? (
                        <>
                          <a
                            href={job.raw.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-indigo-600 hover:text-indigo-500 text-sm font-medium flex items-center"
                          >
                            <ExternalLink className="h-4 w-4 mr-1" />
                            View Job
                          </a>
                          
                          <button
                            onClick={() => queueJobForApplication(job.id)}
                            disabled={queueingJobs.has(job.id)}
                            className="bg-indigo-600 text-white px-3 py-1 rounded-md text-xs font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                          >
                            {queueingJobs.has(job.id) ? (
                              <>
                                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                                Queueing...
                              </>
                            ) : (
                              'Queue for Application'
                            )}
                          </button>
                        </>
                      ) : (
                        <>
                          <div className="text-xs text-red-500 font-medium flex items-center">
                            <AlertCircle className="h-3 w-3 mr-1" />
                            No URL Available
                          </div>
                          <button
                            disabled
                            className="bg-gray-400 text-gray-200 px-3 py-1 rounded-md text-xs font-medium cursor-not-allowed flex items-center opacity-50"
                            title="Cannot queue: Job has no application URL"
                          >
                            Cannot Queue
                          </button>
                        </>
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
  )
}
