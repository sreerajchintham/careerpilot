import React, { useState } from 'react'
import { 
  X, 
  Copy, 
  ExternalLink, 
  CheckCircle,
  FileText,
  Award,
  AlertCircle,
  TrendingUp,
  Target
} from 'lucide-react'
import toast from 'react-hot-toast'

interface ApplicationMaterialsModalProps {
  isOpen: boolean
  onClose: () => void
  application: {
    id: string
    job_id: string
    status: string
    artifacts?: {
      cover_letter?: string
      match_analysis?: {
        match_score?: number
        key_strengths?: string[]
        gaps?: string[]
        recommendations?: string[]
        should_apply?: boolean
        reasoning?: string
      }
    }
    attempt_meta?: {
      match_score?: number
      note?: string
    }
    jobs?: {
      id: string
      title: string
      company: string
      location?: string
      raw?: {
        url?: string
        description?: string
        salary?: string
      }
    }
  }
  onMarkAsManuallySubmitted?: () => void
}

export default function ApplicationMaterialsModal({
  isOpen,
  onClose,
  application,
  onMarkAsManuallySubmitted
}: ApplicationMaterialsModalProps) {
  const [copied, setCopied] = useState<string | null>(null)

  if (!isOpen) return null

  const job = application.jobs
  const coverLetter = application.artifacts?.cover_letter
  const matchAnalysis = application.artifacts?.match_analysis
  const matchScore = matchAnalysis?.match_score || application.attempt_meta?.match_score || 0
  const jobUrl = job?.raw?.url

  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(label)
      toast.success(`${label} copied to clipboard!`)
      setTimeout(() => setCopied(null), 2000)
    } catch (error) {
      toast.error('Failed to copy to clipboard')
    }
  }

  const openJobUrl = () => {
    if (jobUrl) {
      window.open(jobUrl, '_blank', 'noopener,noreferrer')
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/80 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl shadow-2xl border border-cyan-500/30 max-w-6xl w-full max-h-[90vh] flex flex-col">
          
          {/* Header */}
          <div className="flex items-start justify-between p-6 border-b border-gray-700">
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                <FileText className="h-7 w-7 text-cyan-400" />
                AI-Generated Application Materials
              </h2>
              <div className="mt-2 space-y-1">
                <p className="text-lg text-gray-300 font-semibold">
                  {job?.title || 'Unknown Position'}
                </p>
                <p className="text-sm text-gray-400">
                  {job?.company || 'Unknown Company'} {job?.location && `• ${job.location}`}
                </p>
              </div>
            </div>
            
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors p-2 rounded-lg hover:bg-gray-700"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            
            {/* Match Score Card */}
            <div className="bg-gradient-to-r from-cyan-500/10 to-purple-500/10 rounded-xl p-6 border border-cyan-500/30">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Target className="h-8 w-8 text-cyan-400" />
                  <div>
                    <p className="text-sm text-gray-400 font-medium">AI Match Score</p>
                    <p className="text-3xl font-bold text-white">{matchScore}/100</p>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className={`inline-flex items-center px-4 py-2 rounded-xl text-sm font-bold ${
                    matchScore >= 80 ? 'bg-green-500/20 text-green-400 border border-green-500/30' :
                    matchScore >= 60 ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                    'bg-red-500/20 text-red-400 border border-red-500/30'
                  }`}>
                    {matchScore >= 80 ? 'Excellent Match' : matchScore >= 60 ? 'Good Match' : 'Fair Match'}
                  </div>
                </div>
              </div>
            </div>

            {/* Key Strengths */}
            {matchAnalysis?.key_strengths && matchAnalysis.key_strengths.length > 0 && (
              <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center gap-2 mb-4">
                  <TrendingUp className="h-5 w-5 text-green-400" />
                  <h3 className="text-lg font-bold text-white">Your Key Strengths</h3>
                </div>
                <ul className="space-y-2">
                  {matchAnalysis.key_strengths.map((strength, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-gray-300">
                      <CheckCircle className="h-5 w-5 text-green-400 mt-0.5 flex-shrink-0" />
                      <span>{strength}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Gaps & Recommendations */}
            {matchAnalysis?.gaps && matchAnalysis.gaps.length > 0 && (
              <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center gap-2 mb-4">
                  <AlertCircle className="h-5 w-5 text-yellow-400" />
                  <h3 className="text-lg font-bold text-white">Areas to Address</h3>
                </div>
                <ul className="space-y-2">
                  {matchAnalysis.gaps.map((gap, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-gray-300">
                      <span className="text-yellow-400">•</span>
                      <span>{gap}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* AI Recommendations */}
            {matchAnalysis?.recommendations && matchAnalysis.recommendations.length > 0 && (
              <div className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-xl p-6 border border-purple-500/30">
                <div className="flex items-center gap-2 mb-4">
                  <Award className="h-5 w-5 text-purple-400" />
                  <h3 className="text-lg font-bold text-white">AI Recommendations</h3>
                </div>
                <ul className="space-y-2">
                  {matchAnalysis.recommendations.map((rec, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-gray-300">
                      <span className="text-purple-400">→</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Cover Letter */}
            {coverLetter && (
              <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <FileText className="h-5 w-5 text-cyan-400" />
                    AI-Generated Cover Letter
                  </h3>
                  <button
                    onClick={() => copyToClipboard(coverLetter, 'Cover Letter')}
                    className="flex items-center gap-2 px-4 py-2 bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 rounded-lg text-sm font-medium transition-colors border border-cyan-500/30"
                  >
                    {copied === 'Cover Letter' ? (
                      <>
                        <CheckCircle className="h-4 w-4" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4" />
                        Copy
                      </>
                    )}
                  </button>
                </div>
                <div className="bg-gray-900/50 rounded-lg p-4 max-h-96 overflow-y-auto">
                  <p className="text-gray-300 whitespace-pre-wrap font-mono text-sm leading-relaxed">
                    {coverLetter}
                  </p>
                </div>
              </div>
            )}

            {/* AI Note */}
            {application.attempt_meta?.note && (
              <div className="bg-blue-500/10 rounded-xl p-4 border border-blue-500/30">
                <p className="text-sm text-blue-300">
                  <span className="font-semibold">Note:</span> {application.attempt_meta.note}
                </p>
              </div>
            )}

          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-6 border-t border-gray-700 bg-gray-900/50">
            <div className="text-sm text-gray-400">
              <p>💡 <span className="font-semibold text-gray-300">Tip:</span> Review and customize these materials before applying</p>
            </div>
            
            <div className="flex items-center gap-3">
              <button
                onClick={onClose}
                className="px-6 py-2.5 text-sm font-bold text-gray-300 bg-gray-700 hover:bg-gray-600 rounded-xl transition-colors"
              >
                Close
              </button>
              
              {jobUrl && (
                <button
                  onClick={openJobUrl}
                  className="px-6 py-2.5 text-sm font-bold text-white bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 rounded-xl transition-all flex items-center gap-2 shadow-lg shadow-cyan-500/20"
                >
                  <ExternalLink className="h-4 w-4" />
                  Open Job Application
                </button>
              )}
              
              {onMarkAsManuallySubmitted && application.status === 'materials_ready' && (
                <button
                  onClick={onMarkAsManuallySubmitted}
                  className="px-6 py-2.5 text-sm font-bold text-white bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 rounded-xl transition-all flex items-center gap-2 shadow-lg shadow-green-500/20"
                >
                  <CheckCircle className="h-4 w-4" />
                  Mark as Manually Submitted
                </button>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}

