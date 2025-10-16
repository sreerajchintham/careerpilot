import React, { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { useRouter } from 'next/router'
import DashboardLayout from '../../components/DashboardLayout'
import { 
  FileText, 
  Plus, 
  Edit, 
  Trash2, 
  Save,
  Eye,
  CheckCircle,
  AlertCircle,
  Download
} from 'lucide-react'
import toast from 'react-hot-toast'
import { supabase } from '../../lib/supabase'
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

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      fetchDrafts()
    }
  }, [user])

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
      resume_text: appUser?.profile?.summary || '',
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
        // Create new draft
        await apiClient.saveResumeDraft(user.id, draftText, selectedSuggestions)
        toast.success('Draft created successfully!')
      } else {
        // Update existing draft
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
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to get suggestions')
    } finally {
      setLoadingSuggestions(false)
    }
  }

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
      // Simple implementation - in reality, this would be more sophisticated
      newText += '\n\n' + suggestion
    })
    
    setDraftText(newText)
    setSelectedSuggestions([])
    toast.success('Suggestions applied to draft!')
  }

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return 'bg-green-100 text-green-800'
      case 'med':
        return 'bg-yellow-100 text-yellow-800'
      case 'low':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
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
          <h1 className="text-2xl font-bold text-gray-900">Resume Drafting</h1>
          <p className="mt-1 text-sm text-gray-500">
            Create and edit resume drafts with AI-powered suggestions.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Drafts List */}
          <div className="lg:col-span-1">
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-medium text-gray-900">Drafts</h2>
                  <button
                    onClick={createNewDraft}
                    className="bg-indigo-600 text-white px-3 py-1 rounded-md text-sm font-medium hover:bg-indigo-700 flex items-center"
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    New
                  </button>
                </div>
              </div>

              {loadingDrafts ? (
                <div className="p-6 text-center">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mx-auto"></div>
                </div>
              ) : drafts.length === 0 ? (
                <div className="p-6 text-center">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto" />
                  <p className="mt-2 text-sm text-gray-500">No drafts found</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {drafts.map((draft) => (
                    <div
                      key={draft.id}
                      className={`p-4 cursor-pointer hover:bg-gray-50 ${
                        selectedDraft?.id === draft.id ? 'bg-indigo-50' : ''
                      }`}
                      onClick={() => selectDraft(draft)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">
                            Draft {formatDate(draft.created_at)}
                          </p>
                          <p className="text-xs text-gray-500">
                            {draft.applied_suggestions.length} suggestions applied
                          </p>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteDraft(draft.id)
                          }}
                          className="text-red-600 hover:text-red-500"
                        >
                          <Trash2 className="h-4 w-4" />
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
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-medium text-gray-900">
                    {selectedDraft ? 'Edit Draft' : 'Select a Draft'}
                  </h2>
                  {selectedDraft && (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setEditingDraft(!editingDraft)}
                        className="text-indigo-600 hover:text-indigo-500 text-sm font-medium flex items-center"
                      >
                        <Edit className="h-4 w-4 mr-1" />
                        {editingDraft ? 'View' : 'Edit'}
                      </button>
                      {editingDraft && (
                        <button
                          onClick={saveDraft}
                          className="bg-indigo-600 text-white px-3 py-1 rounded-md text-sm font-medium hover:bg-indigo-700 flex items-center"
                        >
                          <Save className="h-4 w-4 mr-1" />
                          Save
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>

              <div className="p-6">
                {!selectedDraft ? (
                  <div className="text-center py-12">
                    <FileText className="h-12 w-12 text-gray-400 mx-auto" />
                    <p className="mt-2 text-sm text-gray-500">
                      Select a draft from the list or create a new one
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {editingDraft ? (
                      <textarea
                        value={draftText}
                        onChange={(e) => setDraftText(e.target.value)}
                        rows={20}
                        className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="Enter your resume text..."
                      />
                    ) : (
                      <div className="prose max-w-none">
                        <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 p-4 rounded-lg">
                          {draftText}
                        </pre>
                      </div>
                    )}

                    {/* AI Suggestions */}
                    {editingDraft && (
                      <div className="border-t pt-4">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-sm font-medium text-gray-900">AI Suggestions</h3>
                          <div className="flex items-center space-x-2">
                            <input
                              type="text"
                              placeholder="Job ID for suggestions"
                              value={selectedJobId}
                              onChange={(e) => setSelectedJobId(e.target.value)}
                              className="border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                            />
                            <button
                              onClick={getSuggestions}
                              disabled={loadingSuggestions}
                              className="bg-gray-600 text-white px-3 py-1 rounded-md text-sm font-medium hover:bg-gray-700 disabled:opacity-50"
                            >
                              {loadingSuggestions ? 'Loading...' : 'Get Suggestions'}
                            </button>
                          </div>
                        </div>

                        {suggestions.length > 0 && (
                          <div className="space-y-2">
                            {suggestions.map((suggestion, index) => (
                              <div
                                key={index}
                                className={`p-3 rounded-lg border cursor-pointer ${
                                  selectedSuggestions.includes(suggestion.text)
                                    ? 'border-indigo-500 bg-indigo-50'
                                    : 'border-gray-200 hover:border-gray-300'
                                }`}
                                onClick={() => toggleSuggestion(suggestion.text)}
                              >
                                <div className="flex items-start space-x-2">
                                  <input
                                    type="checkbox"
                                    checked={selectedSuggestions.includes(suggestion.text)}
                                    onChange={() => toggleSuggestion(suggestion.text)}
                                    className="mt-1"
                                  />
                                  <div className="flex-1">
                                    <p className="text-sm text-gray-700">{suggestion.text}</p>
                                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(suggestion.confidence)}`}>
                                      {suggestion.confidence} confidence
                                    </span>
                                  </div>
                                </div>
                              </div>
                            ))}
                            
                            {selectedSuggestions.length > 0 && (
                              <button
                                onClick={applySuggestions}
                                className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700"
                              >
                                Apply Selected Suggestions
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
    </DashboardLayout>
  )
}
