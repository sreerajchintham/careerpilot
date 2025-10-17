import React, { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { useRouter } from 'next/router'
import DashboardLayout from '../../components/DashboardLayout'
import ResumeDiffModal from '../../components/ResumeDiffModal'
import { 
  FileText, 
  Plus, 
  Edit, 
  Trash2, 
  Save,
  Eye,
  CheckCircle,
  AlertCircle,
  Download,
  Sparkles,
  Briefcase
} from 'lucide-react'
import toast from 'react-hot-toast'
import { supabase, Job } from '../../lib/supabase'
import apiClient from '../../lib/api'

interface Draft {
  id: string
  resume_text: string
  applied_suggestions: string[]
  created_at: string
  updated_at: string
}

interface ResumeSuggestion {
  text: string
  confidence: 'low' | 'med' | 'high'
}

interface Application {
  id: string
  status: string
  created_at: string
  artifacts: {
    match_analysis?: {
      match_score: number
      reasoning: string
      key_strengths: string[]
      areas_to_address: string[]
      recommendations: string[]
    }
    cover_letter?: string
  }
  jobs: {
    id: string
    title: string
    company: string
    location: string
  }
}

export default function ResumeDrafts() {
  const { user, appUser, loading } = useAuth()
  const router = useRouter()
  const [drafts, setDrafts] = useState<Draft[]>([])
  const [loadingDrafts, setLoadingDrafts] = useState(true)
  const [selectedDraft, setSelectedDraft] = useState<Draft | null>(null)
  const [editingDraft, setEditingDraft] = useState(false)
  const [draftText, setDraftText] = useState('')
  const [suggestions, setSuggestions] = useState<ResumeSuggestion[]>([])
  const [selectedSuggestions, setSelectedSuggestions] = useState<string[]>([])
  const [loadingSuggestions, setLoadingSuggestions] = useState(false)
  const [selectedJobId, setSelectedJobId] = useState('')
  const [jobs, setJobs] = useState<Job[]>([])
  const [loadingJobs, setLoadingJobs] = useState(false)
  const [showDiffModal, setShowDiffModal] = useState(false)
  const [originalResumeText, setOriginalResumeText] = useState('')
  
  // New state for tailored resume generation
  const [materialsReadyApps, setMaterialsReadyApps] = useState<Application[]>([])
  const [loadingApplications, setLoadingApplications] = useState(false)
  const [selectedApplicationId, setSelectedApplicationId] = useState('')
  const [generatingResume, setGeneratingResume] = useState(false)
  const [tailoredResume, setTailoredResume] = useState<string>('')
  const [changesMade, setChangesMade] = useState<string[]>([])
  const [showTailoredView, setShowTailoredView] = useState(false)

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      fetchDrafts()
      fetchJobs()
      fetchLatestResume()
      fetchMaterialsReadyApplications()
    }
  }, [user])

  const fetchMaterialsReadyApplications = async () => {
    if (!user) return
    
    setLoadingApplications(true)
    try {
      const { data, error } = await supabase
        .from('applications')
        .select(`
          id,
          status,
          created_at,
          artifacts,
          jobs!inner(
            id,
            title,
            company,
            location
          )
        `)
        .eq('user_id', user.id)
        .eq('status', 'materials_ready')
        .order('created_at', { ascending: false })

      if (error) throw error
      setMaterialsReadyApps((data as Application[]) || [])
      console.log(`Fetched ${data?.length || 0} materials_ready applications`)
    } catch (error) {
      console.error('Error fetching materials_ready applications:', error)
      toast.error('Failed to fetch AI-ready applications')
    } finally {
      setLoadingApplications(false)
    }
  }

  const fetchJobs = async () => {
    setLoadingJobs(true)
    try {
      const { data, error } = await supabase
        .from('jobs')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(50)

      if (error) throw error
      setJobs(data || [])
    } catch (error) {
      console.error('Error fetching jobs:', error)
    } finally {
      setLoadingJobs(false)
    }
  }

  const fetchLatestResume = async () => {
    if (!user) return
    
    try {
      const resumeData = await apiClient.getLatestResume(user.id)
      if (resumeData.resume) {
        setOriginalResumeText(resumeData.resume.text || '')
        if (!draftText) {
          setDraftText(resumeData.resume.text || '')
        }
      }
    } catch (error) {
      console.error('Error fetching latest resume:', error)
    }
  }

  const fetchDrafts = async () => {
    setLoadingDrafts(true)
    try {
      const response = await apiClient.getUserDrafts(user?.id || '')
      setDrafts(response.drafts || [])
    } catch (error) {
      console.error('Error fetching drafts:', error)
      toast.error('Failed to fetch drafts')
    } finally {
      setLoadingDrafts(false)
    }
  }

  const createNewDraft = () => {
    const newDraft: Draft = {
      id: 'new',
      resume_text: originalResumeText || appUser?.profile?.summary || '',
      applied_suggestions: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    setSelectedDraft(newDraft)
    setDraftText(newDraft.resume_text)
    setEditingDraft(true)
  }

  const selectDraft = (draft: Draft) => {
    setSelectedDraft(draft)
    setDraftText(draft.resume_text)
    setEditingDraft(false)
  }

  const saveDraft = async () => {
    if (!user) return

    try {
      if (selectedDraft?.id === 'new') {
        await apiClient.saveResumeDraft(user.id, draftText, selectedSuggestions)
        toast.success('Draft created successfully!')
      } else {
        await apiClient.saveResumeDraft(user.id, draftText, selectedSuggestions)
        toast.success('Draft updated successfully!')
      }
      
      setEditingDraft(false)
      fetchDrafts()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save draft')
    }
  }

  const deleteDraft = async (draftId: string) => {
    if (!user) return

    try {
      await apiClient.deleteDraft(user.id, draftId)
      toast.success('Draft deleted successfully!')
      fetchDrafts()
      
      if (selectedDraft?.id === draftId) {
        setSelectedDraft(null)
        setDraftText('')
      }
    } catch (error: any) {
      toast.error('Failed to delete draft')
    }
  }

  const getSuggestions = async () => {
    if (!selectedJobId || !draftText) {
      toast.error('Please select a job and enter resume text')
      return
    }

    setLoadingSuggestions(true)
    try {
      const response = await apiClient.proposeResume({
        job_id: selectedJobId,
        resume_text: draftText
      })
      setSuggestions(response.suggestions)
      toast.success(`Generated ${response.suggestions.length} suggestions!`)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to get suggestions')
    } finally {
      setLoadingSuggestions(false)
    }
  }

  const openDiffModal = async () => {
    if (!selectedJobId || !draftText) {
      toast.error('Please select a job and enter resume text')
      return
    }

    // Get suggestions first if not already loaded
    if (suggestions.length === 0) {
      await getSuggestions()
    }

    setShowDiffModal(true)
  }

  const selectedJob = jobs.find(j => j.id === selectedJobId)

  const toggleSuggestion = (suggestion: string) => {
    setSelectedSuggestions(prev => 
      prev.includes(suggestion)
        ? prev.filter(s => s !== suggestion)
        : [...prev, suggestion]
    )
  }

  const applySuggestions = () => {
    let newText = draftText
    
    selectedSuggestions.forEach(suggestion => {
      newText += '\n\n' + suggestion
    })
    
    setDraftText(newText)
    setSelectedSuggestions([])
    toast.success('Suggestions applied to draft!')
  }

  const generateTailoredResume = async () => {
    if (!selectedApplicationId || !user) {
      toast.error('Please select an application first')
      return
    }

    setGeneratingResume(true)
    try {
      const response = await apiClient.generateTailoredResume(selectedApplicationId, user.id)
      
      setTailoredResume(response.tailored_resume)
      setChangesMade(response.changes_made)
      setOriginalResumeText(response.original_resume)
      setShowTailoredView(true)
      
      toast.success('Tailored resume generated successfully!')
    } catch (error: any) {
      console.error('Error generating tailored resume:', error)
      toast.error(error.response?.data?.detail || 'Failed to generate tailored resume')
    } finally {
      setGeneratingResume(false)
    }
  }

  const downloadTailoredResume = () => {
    if (!tailoredResume) {
      toast.error('No tailored resume to download')
      return
    }

    const blob = new Blob([tailoredResume], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    
    const selectedApp = materialsReadyApps.find(app => app.id === selectedApplicationId)
    const filename = selectedApp 
      ? `resume_${selectedApp.jobs.company}_${selectedApp.jobs.title.replace(/\s+/g, '_')}.txt`
      : 'tailored_resume.txt'
    
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    toast.success('Resume downloaded!')
  }

  const copyTailoredResume = () => {
    if (!tailoredResume) return
    
    navigator.clipboard.writeText(tailoredResume)
      .then(() => toast.success('Resume copied to clipboard!'))
      .catch(() => toast.error('Failed to copy resume'))
  }

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return 'bg-green-900/30 text-green-300 border-green-500/30'
      case 'med':
        return 'bg-yellow-900/30 text-yellow-300 border-yellow-500/30'
      case 'low':
        return 'bg-orange-900/30 text-orange-300 border-orange-500/30'
      default:
        return 'bg-gray-900/30 text-gray-300 border-gray-500/30'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-cyan-600"></div>
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
          <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">
            RESUME DRAFTING
          </h1>
          <p className="mt-2 text-lg text-gray-300">
            Create AI-powered resume versions optimized for specific jobs.
          </p>
        </div>

        {/* AI Tailored Resume Generation Section */}
        <div className="card-futuristic rounded-2xl p-6 mb-6">
          <div className="flex items-center mb-6">
            <Sparkles className="h-8 w-8 text-cyan-400 mr-3" />
            <div>
              <h2 className="text-2xl font-bold text-gray-200">AI TAILORED RESUMES</h2>
              <p className="text-sm text-gray-400 mt-1">
                Generate custom resumes using AI materials from your applications
              </p>
            </div>
          </div>

          {!showTailoredView ? (
            <>
              {/* Application Selector */}
              <div className="mb-6">
                <label className="block text-sm font-bold text-gray-300 mb-3">
                  SELECT APPLICATION WITH AI MATERIALS
                </label>
                {loadingApplications ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-600"></div>
                  </div>
                ) : materialsReadyApps.length === 0 ? (
                  <div className="bg-gray-800/50 rounded-lg p-8 text-center border border-gray-700">
                    <Briefcase className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400 text-lg mb-2">No AI-Ready Applications</p>
                    <p className="text-gray-500 text-sm">
                      Queue some jobs and let the AI worker process them first.
                    </p>
                  </div>
                ) : (
                  <select
                    value={selectedApplicationId}
                    onChange={(e) => setSelectedApplicationId(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 text-gray-200 rounded-lg px-4 py-4 focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                  >
                    <option value="">-- Select an application --</option>
                    {materialsReadyApps.map((app) => (
                      <option key={app.id} value={app.id}>
                        {app.jobs.title} at {app.jobs.company} 
                        {app.artifacts.match_analysis?.match_score && 
                          ` (Match: ${app.artifacts.match_analysis.match_score}/100)`
                        }
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Generate Button */}
              <button
                onClick={generateTailoredResume}
                disabled={generatingResume || !selectedApplicationId}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white px-8 py-4 rounded-lg font-bold hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center glow-purple"
              >
                {generatingResume ? (
                  <>
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3"></div>
                    GENERATING TAILORED RESUME...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-6 w-6 mr-3" />
                    GENERATE TAILORED RESUME WITH AI
                  </>
                )}
              </button>
            </>
          ) : (
            <>
              {/* Tailored Resume View */}
              <div className="space-y-6">
                {/* Action Buttons */}
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-bold text-gray-200">
                    {materialsReadyApps.find(app => app.id === selectedApplicationId)?.jobs.title || 'Tailored Resume'}
                  </h3>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => {
                        setShowTailoredView(false)
                        setTailoredResume('')
                        setSelectedApplicationId('')
                      }}
                      className="text-gray-400 hover:text-gray-300 text-sm font-bold flex items-center transition-colors"
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      SELECT DIFFERENT JOB
                    </button>
                    <button
                      onClick={copyTailoredResume}
                      className="bg-gradient-to-r from-green-500 to-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-bold hover:from-green-600 hover:to-emerald-600 flex items-center glow-green transition-all"
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      COPY
                    </button>
                    <button
                      onClick={downloadTailoredResume}
                      className="bg-gradient-to-r from-cyan-500 to-blue-500 text-white px-4 py-2 rounded-lg text-sm font-bold hover:from-cyan-600 hover:to-blue-600 flex items-center glow-blue transition-all"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      DOWNLOAD
                    </button>
                  </div>
                </div>

                {/* Changes Made */}
                {changesMade.length > 0 && (
                  <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-lg p-4 border border-purple-500/30">
                    <h4 className="text-sm font-bold text-purple-400 mb-2">CHANGES MADE BY AI:</h4>
                    <ul className="space-y-1">
                      {changesMade.map((change, index) => (
                        <li key={index} className="text-sm text-gray-300 flex items-start">
                          <span className="text-purple-400 mr-2">•</span>
                          {change}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Side-by-Side Comparison */}
                <div className="grid grid-cols-2 gap-6">
                  {/* Original Resume */}
                  <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
                    <h4 className="text-sm font-bold text-gray-400 mb-4 uppercase">Original Resume</h4>
                    <pre className="whitespace-pre-wrap text-xs text-gray-400 font-mono leading-relaxed max-h-96 overflow-y-auto">
                      {originalResumeText}
                    </pre>
                  </div>

                  {/* Tailored Resume */}
                  <div className="bg-gradient-to-br from-cyan-900/20 to-green-900/20 rounded-lg p-6 border border-cyan-500/30">
                    <h4 className="text-sm font-bold text-cyan-400 mb-4 uppercase">✨ Tailored Resume</h4>
                    <pre className="whitespace-pre-wrap text-xs text-gray-200 font-mono leading-relaxed max-h-96 overflow-y-auto">
                      {tailoredResume}
                    </pre>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Drafts List */}
          <div className="lg:col-span-1">
            <div className="card-futuristic rounded-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-700">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold text-gray-200">DRAFTS</h2>
                  <button
                    onClick={createNewDraft}
                    className="bg-gradient-to-r from-cyan-500 to-green-500 text-white px-4 py-2 rounded-lg text-sm font-bold hover:from-cyan-600 hover:to-green-600 flex items-center glow-blue transition-all"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    NEW
                  </button>
                </div>
              </div>

              {loadingDrafts ? (
                <div className="p-6 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-600 mx-auto"></div>
                </div>
              ) : drafts.length === 0 ? (
                <div className="p-8 text-center">
                  <FileText className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400 text-lg">NO DRAFTS YET</p>
                  <p className="text-gray-500 text-sm mt-2">Create your first draft to get started</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-700">
                  {drafts.map((draft) => (
                    <div
                      key={draft.id}
                      className={`p-4 cursor-pointer hover:bg-gray-800/50 transition-colors ${
                        selectedDraft?.id === draft.id ? 'bg-cyan-900/20 border-l-4 border-cyan-500' : ''
                      }`}
                      onClick={() => selectDraft(draft)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="text-base font-bold text-gray-200">
                            {formatDate(draft.created_at)}
                          </p>
                          <p className="text-sm text-cyan-400">
                            {draft.applied_suggestions.length} suggestions applied
                          </p>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteDraft(draft.id)
                          }}
                          className="text-red-500 hover:text-red-400 transition-colors"
                        >
                          <Trash2 className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Draft Editor */}
          <div className="lg:col-span-2">
            <div className="card-futuristic rounded-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-700">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold text-gray-200">
                    {selectedDraft ? (selectedDraft.id === 'new' ? 'NEW DRAFT' : 'EDIT DRAFT') : 'SELECT A DRAFT'}
                  </h2>
                  {selectedDraft && (
                    <div className="flex items-center space-x-3">
                      <button
                        onClick={() => setEditingDraft(!editingDraft)}
                        className="text-cyan-400 hover:text-cyan-300 text-sm font-bold flex items-center transition-colors"
                      >
                        <Edit className="h-4 w-4 mr-2" />
                        {editingDraft ? 'VIEW' : 'EDIT'}
                      </button>
                      {editingDraft && (
                        <button
                          onClick={saveDraft}
                          className="bg-gradient-to-r from-cyan-500 to-green-500 text-white px-4 py-2 rounded-lg text-sm font-bold hover:from-cyan-600 hover:to-green-600 flex items-center glow-green transition-all"
                        >
                          <Save className="h-4 w-4 mr-2" />
                          SAVE
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>

              <div className="p-6">
                {!selectedDraft ? (
                  <div className="text-center py-16">
                    <FileText className="h-20 w-20 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400 text-xl">
                      Select a draft from the list or create a new one
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {editingDraft ? (
                      <textarea
                        value={draftText}
                        onChange={(e) => setDraftText(e.target.value)}
                        rows={20}
                        className="w-full bg-gray-900 border border-gray-700 text-gray-200 rounded-lg p-4 focus:ring-2 focus:ring-cyan-500 focus:border-transparent font-mono text-sm"
                        placeholder="Enter your resume text..."
                      />
                    ) : (
                      <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
                        <pre className="whitespace-pre-wrap text-sm text-gray-300 font-mono leading-relaxed">
                          {draftText}
                        </pre>
                      </div>
                    )}

                    {/* AI Suggestions Section */}
                    {editingDraft && (
                      <div className="border-t border-gray-700 pt-6">
                        <div className="flex items-center justify-between mb-6">
                          <div className="flex items-center space-x-2">
                            <Sparkles className="h-6 w-6 text-cyan-400" />
                            <h3 className="text-xl font-bold text-gray-200">AI SUGGESTIONS</h3>
                          </div>
                        </div>

                        {/* Job Selector */}
                        <div className="mb-6">
                          <label className="block text-sm font-bold text-gray-300 mb-2">
                            SELECT JOB FOR OPTIMIZATION
                          </label>
                          <div className="flex items-center space-x-3">
                            <select
                              value={selectedJobId}
                              onChange={(e) => setSelectedJobId(e.target.value)}
                              className="flex-1 bg-gray-900 border border-gray-700 text-gray-200 rounded-lg px-4 py-3 focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                              disabled={loadingJobs}
                            >
                              <option value="">-- Select a job --</option>
                              {jobs.map((job) => (
                                <option key={job.id} value={job.id}>
                                  {job.title} at {job.company}
                                </option>
                              ))}
                            </select>
                            <button
                              onClick={getSuggestions}
                              disabled={loadingSuggestions || !selectedJobId}
                              className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-3 rounded-lg font-bold hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center"
                            >
                              {loadingSuggestions ? (
                                <>
                                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                                  GENERATING...
                                </>
                              ) : (
                                <>
                                  <Sparkles className="h-5 w-5 mr-2" />
                                  GET SUGGESTIONS
                                </>
                              )}
                            </button>
                          </div>
                        </div>

                        {/* Suggestions List */}
                        {suggestions.length > 0 && (
                          <div className="space-y-4">
                            <div className="flex items-center justify-between">
                              <p className="text-sm text-gray-400">
                                {suggestions.length} suggestions generated
                              </p>
                              <button
                                onClick={openDiffModal}
                                className="bg-gradient-to-r from-cyan-500 to-green-500 text-white px-4 py-2 rounded-lg text-sm font-bold hover:from-cyan-600 hover:to-green-600 flex items-center glow-blue transition-all"
                              >
                                <Eye className="h-4 w-4 mr-2" />
                                PREVIEW CHANGES
                              </button>
                            </div>

                            {suggestions.map((suggestion, index) => (
                              <div
                                key={index}
                                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                                  selectedSuggestions.includes(suggestion.text)
                                    ? 'border-cyan-500 bg-cyan-900/20'
                                    : 'border-gray-700 hover:border-gray-600 bg-gray-900/50'
                                }`}
                                onClick={() => toggleSuggestion(suggestion.text)}
                              >
                                <div className="flex items-start space-x-3">
                                  <input
                                    type="checkbox"
                                    checked={selectedSuggestions.includes(suggestion.text)}
                                    onChange={() => toggleSuggestion(suggestion.text)}
                                    className="mt-1 h-4 w-4 text-cyan-600 border-gray-600 rounded focus:ring-cyan-500 bg-gray-800"
                                  />
                                  <div className="flex-1">
                                    <p className="text-sm text-gray-300 mb-2">{suggestion.text}</p>
                                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border ${getConfidenceColor(suggestion.confidence)}`}>
                                      {suggestion.confidence.toUpperCase()} CONFIDENCE
                                    </span>
                                  </div>
                                </div>
                              </div>
                            ))}
                            
                            {selectedSuggestions.length > 0 && (
                              <button
                                onClick={applySuggestions}
                                className="w-full bg-gradient-to-r from-green-500 to-emerald-500 text-white px-6 py-3 rounded-lg font-bold hover:from-green-600 hover:to-emerald-600 glow-green transition-all"
                              >
                                APPLY {selectedSuggestions.length} SELECTED SUGGESTIONS
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Resume Diff Modal */}
      {showDiffModal && selectedJob && (
        <ResumeDiffModal
          isOpen={showDiffModal}
          onClose={() => setShowDiffModal(false)}
          originalResume={originalResumeText || draftText}
          suggestions={suggestions}
          jobTitle={selectedJob.title}
          company={selectedJob.company}
        />
      )}
    </DashboardLayout>
  )
}
