import { useState, useEffect } from 'react'

// TypeScript interfaces for type safety
interface SuggestionItem {
  text: string
  confidence: 'low' | 'med' | 'high'
}

interface ResumeDiffModalProps {
  isOpen: boolean
  onClose: () => void
  originalResume: string
  suggestions: SuggestionItem[]
  jobTitle: string
  company: string
}

interface AppliedSuggestion {
  text: string
  confidence: string
  applied: boolean
  appliedText?: string
}

export default function ResumeDiffModal({
  isOpen,
  onClose,
  originalResume,
  suggestions,
  jobTitle,
  company
}: ResumeDiffModalProps) {
  // State for tracking which suggestions are applied
  const [appliedSuggestions, setAppliedSuggestions] = useState<AppliedSuggestion[]>([])
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [saveError, setSaveError] = useState<string>('')

  // Initialize applied suggestions when modal opens
  useEffect(() => {
    if (isOpen && suggestions.length > 0) {
      const initialSuggestions = suggestions.map(suggestion => ({
        text: suggestion.text,
        confidence: suggestion.confidence,
        applied: false,
        appliedText: generateAppliedText(suggestion.text)
      }))
      setAppliedSuggestions(initialSuggestions)
    }
  }, [isOpen, suggestions])

  // Generate a consistent user ID for this session
  function generateUserId(): string {
    // In a real app, this would come from authentication context
    // For demo purposes, we'll generate a consistent UUID based on localStorage
    const STORAGE_KEY = 'careerpilot_user_id'
    let userId = localStorage.getItem(STORAGE_KEY)
    
    if (!userId) {
      // Generate a new UUID (simplified version for demo)
      userId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0
        const v = c === 'x' ? r : (r & 0x3 | 0x8)
        return v.toString(16)
      })
      localStorage.setItem(STORAGE_KEY, userId)
    }
    
    return userId
  }

  // Generate the text that would be applied based on the suggestion
  function generateAppliedText(suggestionText: string): string {
    // Extract the actionable part from "Add or emphasize: [action]"
    const match = suggestionText.match(/Add or emphasize:\s*(.+)/i)
    if (match) {
      return match[1].trim()
    }
    return suggestionText.replace(/^Add or emphasize:\s*/i, '').trim()
  }

  // Toggle suggestion application
  function toggleSuggestion(index: number) {
    setAppliedSuggestions(prev => 
      prev.map((item, i) => 
        i === index 
          ? { ...item, applied: !item.applied }
          : item
      )
    )
  }

  // Generate the modified resume text with applied suggestions
  function generateModifiedResume(): string {
    let modifiedResume = originalResume
    
    // Apply suggestions in order of confidence (high first)
    const sortedSuggestions = [...appliedSuggestions]
      .filter(s => s.applied)
      .sort((a, b) => {
        const confidenceOrder = { high: 3, med: 2, low: 1 }
        return confidenceOrder[b.confidence as keyof typeof confidenceOrder] - 
               confidenceOrder[a.confidence as keyof typeof confidenceOrder]
      })

    // For demo purposes, we'll append applied suggestions to the resume
    // In a real implementation, you'd have more sophisticated text insertion logic
    if (sortedSuggestions.length > 0) {
      modifiedResume += '\n\n=== APPLIED SUGGESTIONS ===\n'
      sortedSuggestions.forEach((suggestion, index) => {
        modifiedResume += `${index + 1}. ${suggestion.appliedText}\n`
      })
    }

    return modifiedResume
  }

  // Save resume draft to backend
  async function saveResumeDraft() {
    setSaving(true)
    setSaveError('')
    setSaveSuccess(false)

    try {
      const modifiedResume = generateModifiedResume()
      const appliedSuggestionsData = appliedSuggestions
        .filter(s => s.applied)
        .map(s => ({
          text: s.text,
          confidence: s.confidence,
          applied_text: s.appliedText  // Match backend snake_case format
        }))

      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      const response = await fetch(`${API_BASE_URL}/save-resume-draft`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: generateUserId(), // Generate a consistent UUID for this session
          resume_text: modifiedResume,
          applied_suggestions: appliedSuggestionsData,
          job_context: {
            job_title: jobTitle,
            company: company
          }
        }),
      })

      if (!response.ok) {
        throw new Error(`Failed to save draft: ${response.status} ${response.statusText}`)
      }

      const result = await response.json()
      
      setSaveSuccess(true)
      
      // Auto-close modal after successful save (optional)
      setTimeout(() => {
        onClose()
        setSaveSuccess(false)
      }, 2000)

    } catch (error: any) {
      setSaveError(error.message || 'Failed to save resume draft')
    } finally {
      setSaving(false)
    }
  }

  // Get confidence color classes
  function getConfidenceColors(confidence: string) {
    switch (confidence) {
      case 'high':
        return {
          bg: 'bg-green-50',
          border: 'border-green-200',
          text: 'text-green-800',
          badge: 'bg-green-100 text-green-800',
          dot: 'bg-green-500'
        }
      case 'med':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200',
          text: 'text-yellow-800',
          badge: 'bg-yellow-100 text-yellow-800',
          dot: 'bg-yellow-500'
        }
      case 'low':
        return {
          bg: 'bg-gray-50',
          border: 'border-gray-200',
          text: 'text-gray-700',
          badge: 'bg-gray-100 text-gray-700',
          dot: 'bg-gray-400'
        }
      default:
        return {
          bg: 'bg-gray-50',
          border: 'border-gray-200',
          text: 'text-gray-700',
          badge: 'bg-gray-100 text-gray-700',
          dot: 'bg-gray-400'
        }
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity" onClick={onClose}></div>
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-7xl w-full max-h-[90vh] flex flex-col">
          
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Review Resume Suggestions
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                {jobTitle} at {company}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Close modal"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-hidden">
            <div className="grid grid-cols-1 lg:grid-cols-2 h-full">
              
              {/* Left Pane - Original Resume */}
              <div className="border-r border-gray-200 flex flex-col">
                <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                  <h3 className="text-sm font-medium text-gray-900">Original Resume</h3>
                  <p className="text-xs text-gray-600">Your current resume text</p>
                </div>
                <div className="flex-1 overflow-auto p-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono leading-relaxed">
                      {originalResume}
                    </pre>
                  </div>
                </div>
              </div>

              {/* Right Pane - Modified Resume */}
              <div className="flex flex-col">
                <div className="bg-blue-50 px-4 py-3 border-b border-gray-200">
                  <h3 className="text-sm font-medium text-gray-900">Suggested Resume</h3>
                  <p className="text-xs text-gray-600">
                    Preview with {appliedSuggestions.filter(s => s.applied).length} suggestions applied
                  </p>
                </div>
                <div className="flex-1 overflow-auto p-4">
                  <div className="bg-blue-50 rounded-lg p-4">
                    <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono leading-relaxed">
                      {generateModifiedResume()}
                    </pre>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Suggestions Panel */}
          <div className="border-t border-gray-200 bg-gray-50">
            <div className="p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Select Suggestions to Apply ({appliedSuggestions.filter(s => s.applied).length}/{suggestions.length})
              </h3>
              
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {appliedSuggestions.map((suggestion, index) => {
                  const colors = getConfidenceColors(suggestion.confidence)
                  
                  return (
                    <div
                      key={index}
                      className={`p-4 rounded-lg border ${colors.bg} ${colors.border} transition-all duration-200 ${
                        suggestion.applied ? 'ring-2 ring-blue-500 ring-opacity-50' : ''
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        <input
                          type="checkbox"
                          id={`suggestion-${index}`}
                          checked={suggestion.applied}
                          onChange={() => toggleSuggestion(index)}
                          className="mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        
                        <div className="flex-1 min-w-0">
                          <label htmlFor={`suggestion-${index}`} className="block cursor-pointer">
                            <div className="flex items-center space-x-2 mb-2">
                              <span className={`inline-block w-2 h-2 ${colors.dot} rounded-full`}></span>
                              <span className={`text-xs px-2 py-1 rounded-full ${colors.badge}`}>
                                {suggestion.confidence} confidence
                              </span>
                            </div>
                            
                            <p className={`text-sm ${colors.text} font-medium`}>
                              {suggestion.text}
                            </p>
                            
                            {suggestion.applied && (
                              <p className="text-xs text-blue-600 mt-1">
                                Will add: "{suggestion.appliedText}"
                              </p>
                            )}
                          </label>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-white">
            <div className="flex items-center space-x-4">
              {appliedSuggestions.filter(s => s.applied).length > 0 && (
                <div className="text-sm text-gray-600">
                  <span className="font-medium text-blue-600">
                    {appliedSuggestions.filter(s => s.applied).length}
                  </span> suggestions selected
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                Cancel
              </button>
              
              <button
                onClick={saveResumeDraft}
                disabled={saving || appliedSuggestions.filter(s => s.applied).length === 0}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
              >
                {saving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Saving...</span>
                  </>
                ) : (
                  <span>Save as Draft</span>
                )}
              </button>
            </div>
          </div>

          {/* Success/Error Messages */}
          {saveSuccess && (
            <div className="absolute top-4 right-4 bg-green-50 border border-green-200 rounded-md p-4 shadow-lg">
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-sm font-medium text-green-800">
                  Resume draft saved successfully!
                </span>
              </div>
            </div>
          )}

          {saveError && (
            <div className="absolute top-4 right-4 bg-red-50 border border-red-200 rounded-md p-4 shadow-lg max-w-sm">
              <div className="flex items-start space-x-2">
                <svg className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p className="text-sm font-medium text-red-800">Failed to save draft</p>
                  <p className="text-xs text-red-600 mt-1">{saveError}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
