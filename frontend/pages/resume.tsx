import { useState } from 'react'
import ResumeDiffModal from '../components/ResumeDiffModal'

// TypeScript interfaces for type safety
interface JobMatch {
  job_id: string
  title: string
  company: string
  score: number
  top_keywords: string[]
  missing_skills: string[]
}

interface JobMatchResponse {
  matches: JobMatch[]
  total_jobs_searched: number
  user_skills: string[]
}

interface ParsedResume {
  name: string | null
  email: string | null
  phone: string | null
  skills: string[]
}

interface SuggestionItem {
  text: string
  confidence: 'low' | 'med' | 'high'
}

// Resume upload page with file input, upload progress, parsing, and job matching
export default function ResumePage() {
  // File upload states
  const [fileName, setFileName] = useState<string>("")
  const [fileObj, setFileObj] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [resultPath, setResultPath] = useState<string>("")
  const [error, setError] = useState<string>("")
  const [success, setSuccess] = useState(false)

  // Resume parsing states
  const [parsing, setParsing] = useState(false)
  const [parsedData, setParsedData] = useState<ParsedResume | null>(null)
  const [resumeText, setResumeText] = useState<string>("")

  // Job matching states
  const [matching, setMatching] = useState(false)
  const [jobMatches, setJobMatches] = useState<JobMatch[]>([])
  const [userSkills, setUserSkills] = useState<string[]>([])

  // Resume edit proposal states
  const [proposingEdits, setProposingEdits] = useState<Set<string>>(new Set())
  const [editSuggestions, setEditSuggestions] = useState<{[jobId: string]: SuggestionItem[]}>({})
  
  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedJob, setSelectedJob] = useState<{title: string, company: string} | null>(null)

  // Handle file selection from input
  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    setFileName(file ? file.name : "")
    setFileObj(file ?? null)
    // Reset all previous states when new file is selected
    setError("")
    setResultPath("")
    setSuccess(false)
    setUploadProgress(0)
    setParsedData(null)
    setResumeText("")
    setJobMatches([])
    setUserSkills([])
    setProposingEdits(new Set())
    setEditSuggestions({})
    setIsModalOpen(false)
    setSelectedJob(null)
  }

  // Handle file upload to backend
  async function handleSubmit() {
    if (!fileObj) {
      setError("Please select a file first")
      return
    }

    // Reset states
    setError("")
    setResultPath("")
    setSuccess(false)
    setUploadProgress(0)
    setParsedData(null)
    setResumeText("")
    setJobMatches([])
    setUserSkills([])
    setEditSuggestions({})
    setIsModalOpen(false)
    setSelectedJob(null)

    try {
      setUploading(true)
      const form = new FormData()
      // Backend expects field name 'file'
      form.append('file', fileObj)

      // Create XMLHttpRequest for upload progress tracking
      const xhr = new XMLHttpRequest()
      
      // Track upload progress
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percentComplete = Math.round((e.loaded / e.total) * 100)
          setUploadProgress(percentComplete)
        }
      })

      // Handle response
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText)
            setResultPath(data.path || '')
            setSuccess(true)
            setUploadProgress(100)
            
            // Automatically parse the uploaded resume
            parseResume()
          } catch (parseError) {
            setError('Invalid response from server')
          }
        } else {
          setError(`Upload failed: ${xhr.status} ${xhr.statusText}`)
        }
        setUploading(false)
      })

      // Handle network errors
      xhr.addEventListener('error', () => {
        setError('Network error - please check if backend is running')
        setUploading(false)
      })

      // Handle timeout
      xhr.addEventListener('timeout', () => {
        setError('Upload timeout - file may be too large')
        setUploading(false)
      })

      // Configure and send request
      xhr.open('POST', 'http://127.0.0.1:8001/upload-resume')
      xhr.timeout = 30000 // 30 second timeout
      xhr.send(form)

    } catch (e: any) {
      setError(e?.message || 'Upload failed')
      setUploading(false)
    }
  }

  // Parse the uploaded resume to extract text and structured data
  async function parseResume() {
    if (!fileObj) return

    try {
      setParsing(true)
      setError("")

      const form = new FormData()
      form.append('file', fileObj)

      const response = await fetch('http://127.0.0.1:8001/parse-resume', {
        method: 'POST',
        body: form,
      })

      if (!response.ok) {
        throw new Error(`Parse failed: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      
      if (data.error) {
        setError(data.error)
        return
      }

      // Store parsed data
      setResumeText(data.text || '')
      setParsedData(data.parsed || null)
      
      // Automatically find job matches after parsing
      if (data.text) {
        findJobMatches(data.text)
      }

    } catch (e: any) {
      setError(e?.message || 'Failed to parse resume')
    } finally {
      setParsing(false)
    }
  }

  // Find job matches using the parsed resume text
  async function findJobMatches(text: string) {
    try {
      setMatching(true)
      setError("")

      // Let the backend compute embeddings using sentence-transformers
      // This will give us real semantic similarity instead of random dummy embeddings
      const response = await fetch('http://127.0.0.1:8001/match-jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'frontend-user',
          text: text,
          top_n: 5
          // No embedding field - let backend compute it
        }),
      })

      if (!response.ok) {
        throw new Error(`Job matching failed: ${response.status} ${response.statusText}`)
      }

      const data: JobMatchResponse = await response.json()
      
      setJobMatches(data.matches || [])
      setUserSkills(data.user_skills || [])

    } catch (e: any) {
      setError(e?.message || 'Failed to find job matches')
    } finally {
      setMatching(false)
    }
  }

  // Propose resume edits for a specific job
  async function proposeResumeEdits(jobId: string) {
    try {
      // Add job to the set of jobs being processed
      setProposingEdits(prev => new Set(prev).add(jobId))
      setError("")

      const response = await fetch('http://127.0.0.1:8001/propose-resume', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_id: jobId,
          resume_text: resumeText
        }),
      })

      if (!response.ok) {
        throw new Error(`Resume edit proposal failed: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      
      // Store the suggestions for display
      setEditSuggestions(prev => ({
        ...prev,
        [jobId]: data.suggestions || []
      }))

    } catch (e: any) {
      setError(e?.message || 'Failed to propose resume edits')
    } finally {
      // Remove job from the set of jobs being processed
      setProposingEdits(prev => {
        const newSet = new Set(prev)
        newSet.delete(jobId)
        return newSet
      })
    }
  }

  // Open the resume diff modal
  function openResumeDiffModal(job: JobMatch) {
    setSelectedJob({
      title: job.title,
      company: job.company
    })
    setIsModalOpen(true)
  }

  // Close the modal
  function closeModal() {
    setIsModalOpen(false)
    setSelectedJob(null)
  }

  return (
    <main className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-6">
        {/* Header Section */}
        <div className="text-center mb-8">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">
            CareerPilot Agent
          </h1>
          <p className="text-lg text-gray-600">
            Upload your resume to find matching jobs and get personalized suggestions
          </p>
        </div>

        {/* Upload Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload Resume</h2>
          
          {/* File input with accessibility features */}
          <label className="block">
            <span className="sr-only">Choose resume file</span>
            <input
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={handleFileChange}
              disabled={uploading || parsing || matching}
              className="block w-full text-sm text-gray-700 file:mr-4 file:rounded-md file:border-0 file:bg-blue-600 file:px-4 file:py-2 file:text-white hover:file:bg-blue-700 disabled:opacity-50"
              aria-describedby="file-help"
            />
          </label>
          <p id="file-help" className="mt-2 text-sm text-gray-500">
            Supported formats: PDF, DOC, DOCX (max 10MB)
          </p>

          {/* Selected file info */}
          {fileName && (
            <div className="mt-4 p-3 bg-gray-50 rounded-md">
              <p className="text-sm text-gray-700">
                <span className="font-medium">Selected:</span> {fileName}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Size: {fileObj ? `${(fileObj.size / 1024 / 1024).toFixed(2)} MB` : 'Unknown'}
              </p>
            </div>
          )}

          {/* Upload progress bar */}
          {uploading && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                  role="progressbar"
                  aria-valuenow={uploadProgress}
                  aria-valuemin={0}
                  aria-valuemax={100}
                ></div>
              </div>
            </div>
          )}

          {/* Upload button */}
          <button
            type="button"
            className="mt-4 w-full rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            disabled={!fileName || uploading || parsing || matching}
            onClick={handleSubmit}
            aria-describedby="upload-status"
          >
            {uploading ? 'Uploading...' : parsing ? 'Parsing...' : matching ? 'Finding matches...' : 'Upload & Analyze Resume'}
          </button>

          {/* Status messages */}
          {success && resultPath && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
              <p className="text-sm text-green-800 font-medium">✅ Upload successful!</p>
              <p className="text-xs text-green-700 mt-1 break-all">
                Saved to: {resultPath}
              </p>
            </div>
          )}

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-800 font-medium">❌ Error</p>
              <p className="text-xs text-red-700 mt-1">{error}</p>
            </div>
          )}
        </div>

        {/* Parsed Resume Data Section */}
        {parsedData && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Resume Analysis</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Personal Information */}
              <div className="space-y-3">
                <h3 className="font-medium text-gray-900">Personal Information</h3>
                {parsedData.name && (
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">Name:</span>
                    <span className="text-sm font-medium">{parsedData.name}</span>
                  </div>
                )}
                {parsedData.email && (
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">Email:</span>
                    <span className="text-sm font-medium">{parsedData.email}</span>
                  </div>
                )}
                {parsedData.phone && (
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">Phone:</span>
                    <span className="text-sm font-medium">{parsedData.phone}</span>
                  </div>
                )}
              </div>

              {/* Skills */}
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Skills ({parsedData.skills.length})</h3>
                <div className="flex flex-wrap gap-2">
                  {parsedData.skills.map((skill, index) => (
                    <span
                      key={index}
                      className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Job Matches Section */}
        {jobMatches.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                Job Matches ({jobMatches.length})
              </h2>
              {matching && (
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span>Finding matches...</span>
                </div>
              )}
            </div>

            {/* Job Cards Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {jobMatches.map((job) => (
                <div
                  key={job.job_id}
                  className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow"
                >
                  {/* Job Header */}
                  <div className="mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {job.title}
                    </h3>
                    <p className="text-sm text-gray-600">{job.company}</p>
                  </div>

                  {/* Match Score with Progress Bar */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">Match Score</span>
                      <span className="text-sm font-bold text-blue-600">
                        {(job.score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${job.score * 100}%` }}
                        role="progressbar"
                        aria-valuenow={job.score * 100}
                        aria-valuemin={0}
                        aria-valuemax={100}
                      ></div>
                    </div>
                  </div>

                  {/* Matching Skills */}
                  {job.top_keywords.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Matching Skills</h4>
                      <div className="flex flex-wrap gap-1">
                        {job.top_keywords.map((skill, index) => (
                          <span
                            key={index}
                            className="inline-block px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Missing Skills */}
                  {job.missing_skills.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Missing Skills</h4>
                      <div className="flex flex-wrap gap-1">
                        {job.missing_skills.slice(0, 5).map((skill, index) => (
                          <span
                            key={index}
                            className="inline-block px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded-full"
                          >
                            {skill}
                          </span>
                        ))}
                        {job.missing_skills.length > 5 && (
                          <span className="inline-block px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                            +{job.missing_skills.length - 5} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="mt-4 space-y-2">
                    <button
                      onClick={() => proposeResumeEdits(job.job_id)}
                      disabled={proposingEdits.has(job.job_id)}
                      className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
                      aria-describedby={`propose-${job.job_id}`}
                    >
                      {proposingEdits.has(job.job_id) ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          <span>Generating Suggestions...</span>
                        </>
                      ) : (
                        <span>Generate Suggestions</span>
                      )}
                    </button>
                    
                    {editSuggestions[job.job_id] && editSuggestions[job.job_id].length > 0 && (
                      <button
                        onClick={() => openResumeDiffModal(job)}
                        className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                        <span>Review & Apply Suggestions</span>
                      </button>
                    )}
                  </div>
                  <p id={`propose-${job.job_id}`} className="sr-only">
                    Get personalized suggestions to improve your resume for this job
                  </p>

                  {/* Edit Suggestions Display */}
                  {editSuggestions[job.job_id] && (
                    <div className="mt-4 p-4 bg-purple-50 border border-purple-200 rounded-md">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-medium text-purple-900">
                          💡 Resume Improvement Suggestions
                        </h4>
                        <div className="text-xs text-purple-600 bg-purple-100 px-2 py-1 rounded">
                          {editSuggestions[job.job_id].length} suggestions
                        </div>
                      </div>
                      
                      {/* Important Notice */}
                      <div className="mb-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
                        ⚠️ <strong>Important:</strong> These are suggestions only. Please review and approve any changes before updating your resume.
                      </div>
                      
                      <ul className="space-y-3">
                        {editSuggestions[job.job_id].map((suggestion, index) => {
                          // Determine confidence styling
                          const confidenceColors = {
                            high: { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-200', dot: 'bg-green-500' },
                            med: { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-200', dot: 'bg-yellow-500' },
                            low: { bg: 'bg-gray-100', text: 'text-gray-700', border: 'border-gray-200', dot: 'bg-gray-400' }
                          }
                          
                          const colors = confidenceColors[suggestion.confidence] || confidenceColors.med
                          
                          return (
                            <li key={index} className={`p-3 rounded-md border ${colors.bg} ${colors.border}`}>
                              <div className="flex items-start space-x-2">
                                <span className={`inline-block w-2 h-2 ${colors.dot} rounded-full mt-2 flex-shrink-0`}></span>
                                <div className="flex-1">
                                  <p className={`text-sm ${colors.text} font-medium`}>
                                    {suggestion.text}
                                  </p>
                                  <div className="mt-1 flex items-center space-x-2">
                                    <span className={`text-xs px-2 py-1 rounded-full ${colors.bg} ${colors.text} border ${colors.border}`}>
                                      {suggestion.confidence} confidence
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </li>
                          )
                        })}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Loading States */}
        {(parsing || matching) && jobMatches.length === 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-center">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              <span className="text-gray-600">
                {parsing ? 'Parsing resume...' : 'Finding job matches...'}
              </span>
            </div>
            <p className="text-sm text-gray-500">
              This may take a few moments depending on your resume size
            </p>
          </div>
        )}

        {/* Resume Diff Modal */}
        {isModalOpen && selectedJob && (
          <ResumeDiffModal
            isOpen={isModalOpen}
            onClose={closeModal}
            originalResume={resumeText}
            suggestions={jobMatches
              .filter(job => job.title === selectedJob.title && job.company === selectedJob.company)
              .flatMap(job => editSuggestions[job.job_id] || [])
            }
            jobTitle={selectedJob.title}
            company={selectedJob.company}
          />
        )}
      </div>
    </main>
  )
}


