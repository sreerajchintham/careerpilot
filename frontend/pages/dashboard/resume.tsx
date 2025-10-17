import React, { useState, useCallback } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { useRouter } from 'next/router'
import DashboardLayout from '../../components/DashboardLayout'
import { useDropzone } from 'react-dropzone'
import { 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertCircle,
  Download,
  Eye,
  Edit
} from 'lucide-react'
import toast from 'react-hot-toast'
import apiClient from '../../lib/api'

interface ParsedResume {
  text: string
  parsed: {
    name?: string
    email?: string
    phone?: string
    skills?: string[]
    experience_years?: number
    current_title?: string
    education?: string
    location?: string
    summary?: string
  }
}

export default function ResumeUpload() {
  const { user, appUser, updateProfile } = useAuth()
  const router = useRouter()
  const [uploading, setUploading] = useState(false)
  const [parsedResume, setParsedResume] = useState<ParsedResume | null>(null)
  const [editingProfile, setEditingProfile] = useState(false)
  const [profileData, setProfileData] = useState({
    name: appUser?.profile?.name || '',
    title: appUser?.profile?.title || '',
    location: appUser?.profile?.location || '',
    phone: appUser?.profile?.phone || '',
    summary: appUser?.profile?.summary || '',
    skills: appUser?.profile?.skills || [],
    experience: appUser?.profile?.experience || [],
    education: appUser?.profile?.education || [],
  })

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    if (file.type !== 'application/pdf') {
      toast.error('Please upload a PDF file')
      return
    }

    setUploading(true)
    try {
      // Upload and parse the resume in one go
      const parseResult = await apiClient.parseResumeFile(file)
      setParsedResume(parseResult)
      toast.success('Resume uploaded and parsed successfully!')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.message || 'Failed to upload or parse resume')
    } finally {
      setUploading(false)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: false
  })

  const handleSaveProfile = async () => {
    try {
      await updateProfile(profileData)
      toast.success('Profile updated successfully!')
      setEditingProfile(false)
    } catch (error: any) {
      toast.error('Failed to update profile')
    }
  }

  const addSkill = () => {
    setProfileData(prev => ({
      ...prev,
      skills: [...prev.skills, '']
    }))
  }

  const updateSkill = (index: number, value: string) => {
    setProfileData(prev => ({
      ...prev,
      skills: prev.skills.map((skill, i) => i === index ? value : skill)
    }))
  }

  const removeSkill = (index: number) => {
    setProfileData(prev => ({
      ...prev,
      skills: prev.skills.filter((_, i) => i !== index)
    }))
  }

  const addExperience = () => {
    setProfileData(prev => ({
      ...prev,
      experience: [...prev.experience, {
        title: '',
        company: '',
        location: '',
        start_date: '',
        end_date: '',
        description: ''
      }]
    }))
  }

  const updateExperience = (index: number, field: string, value: string) => {
    setProfileData(prev => ({
      ...prev,
      experience: prev.experience.map((exp, i) => 
        i === index ? { ...exp, [field]: value } : exp
      )
    }))
  }

  const removeExperience = (index: number) => {
    setProfileData(prev => ({
      ...prev,
      experience: prev.experience.filter((_, i) => i !== index)
    }))
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">RESUME MANAGEMENT</h1>
          <p className="mt-2 text-lg text-gray-300">
            Upload your resume and manage your profile information.
          </p>
        </div>

        {/* Resume Upload Section */}
        <div className="card-futuristic rounded-2xl p-8">
            <h2 className="text-2xl font-bold text-gray-200 mb-6">UPLOAD RESUME</h2>
            
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300 ${
                isDragActive
                  ? 'border-cyan-400 bg-cyan-500/10 glow-blue'
                  : 'border-gray-600 hover:border-cyan-400 hover:bg-gray-800/50'
              }`}
            >
              <input {...getInputProps()} />
              <Upload className="mx-auto h-16 w-16 text-cyan-400 mb-4" />
              <div className="mt-4">
                <p className="text-lg text-gray-300 mb-2">
                  {isDragActive
                    ? 'DROP THE PDF FILE HERE...'
                    : 'DRAG & DROP A PDF FILE HERE, OR CLICK TO SELECT'}
                </p>
                <p className="text-sm text-gray-500">
                  PDF files only, max 10MB
                </p>
              </div>
            </div>

            {uploading && (
              <div className="mt-6 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
                <span className="ml-3 text-lg text-gray-300">Processing with AI...</span>
              </div>
            )}
        </div>

        {/* Parsed Resume Results */}
        {parsedResume && (
          <div className="space-y-6">
            {/* Success Message */}
            <div className="p-6 bg-gradient-to-r from-green-500/20 to-emerald-500/20 rounded-2xl border border-green-500/30">
              <div className="flex items-center">
                <CheckCircle className="h-8 w-8 text-green-400" />
                <span className="ml-3 text-lg font-bold text-green-400">
                  Resume parsed successfully with AI!
                </span>
              </div>
            </div>

            {/* Parsed Data Display */}
            <div className="card-futuristic rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-gray-200 mb-6">EXTRACTED INFORMATION</h2>
              
              <div className="space-y-6">
                  {/* Basic Info Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                    {parsedResume.parsed.name && (
                      <div className="p-4 bg-gray-800/50 rounded-xl">
                        <p className="text-sm text-gray-400 mb-1">Name</p>
                        <p className="text-cyan-400 font-semibold">{parsedResume.parsed.name}</p>
                      </div>
                    )}
                    <div className="p-4 bg-gray-800/50 rounded-xl">
                      <p className="text-sm text-gray-400 mb-1">Email</p>
                      <p className="text-cyan-400 font-semibold">{parsedResume.parsed.email || 'Not found'}</p>
                    </div>
                    <div className="p-4 bg-gray-800/50 rounded-xl">
                      <p className="text-sm text-gray-400 mb-1">Phone</p>
                      <p className="text-cyan-400 font-semibold">{parsedResume.parsed.phone || 'Not found'}</p>
                    </div>
                    <div className="p-4 bg-gray-800/50 rounded-xl">
                      <p className="text-sm text-gray-400 mb-1">Skills Found</p>
                      <p className="text-cyan-400 font-semibold text-2xl">{parsedResume.parsed.skills?.length || 0}</p>
                    </div>
                  </div>

                  {/* Professional Info Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    {parsedResume.parsed.current_title && (
                      <div className="p-4 bg-gray-800/50 rounded-xl">
                        <p className="text-sm text-gray-400 mb-1">Current Title</p>
                        <p className="text-green-400 font-semibold">{parsedResume.parsed.current_title}</p>
                      </div>
                    )}
                    {parsedResume.parsed.experience_years && parsedResume.parsed.experience_years > 0 && (
                      <div className="p-4 bg-gray-800/50 rounded-xl">
                        <p className="text-sm text-gray-400 mb-1">Experience</p>
                        <p className="text-green-400 font-semibold">{parsedResume.parsed.experience_years} years</p>
                      </div>
                    )}
                    {parsedResume.parsed.location && (
                      <div className="p-4 bg-gray-800/50 rounded-xl">
                        <p className="text-sm text-gray-400 mb-1">Location</p>
                        <p className="text-green-400 font-semibold">{parsedResume.parsed.location}</p>
                      </div>
                    )}
                  </div>

                  {/* Education */}
                  {parsedResume.parsed.education && (
                    <div className="p-4 bg-gray-800/50 rounded-xl mb-4">
                      <p className="text-sm text-gray-400 mb-1">Education</p>
                      <p className="text-purple-400 font-semibold">{parsedResume.parsed.education}</p>
                    </div>
                  )}

                  {/* Summary */}
                  {parsedResume.parsed.summary && (
                    <div className="p-4 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-xl border border-purple-500/30 mb-4">
                      <p className="text-sm text-purple-400 font-bold mb-2">Professional Summary</p>
                      <p className="text-gray-300">{parsedResume.parsed.summary}</p>
                    </div>
                  )}

                  {/* Skills */}
                  {parsedResume.parsed.skills && parsedResume.parsed.skills.length > 0 && (
                    <div className="mt-4">
                      <p className="text-sm text-gray-400 mb-3 font-bold">Technical & Professional Skills:</p>
                      <div className="flex flex-wrap gap-2">
                        {parsedResume.parsed.skills.map((skill, idx) => (
                          <span
                            key={idx}
                            className="px-3 py-2 bg-cyan-500/20 text-cyan-400 rounded-lg text-sm border border-cyan-500/30 hover:bg-cyan-500/30 transition-all duration-300"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
              </div>
            </div>

            {/* Resume Text Viewer */}
            <div className="card-futuristic rounded-2xl p-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-200 flex items-center">
                  <FileText className="h-6 w-6 text-cyan-400 mr-3" />
                  EXTRACTED RESUME TEXT
                </h2>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(parsedResume.text)
                    toast.success('Resume text copied to clipboard!')
                  }}
                  className="btn-futuristic px-6 py-3 text-sm font-bold rounded-xl"
                >
                  COPY TEXT
                </button>
              </div>
              <div className="max-h-96 overflow-y-auto bg-black/30 rounded-xl p-4 border border-gray-700">
                <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
                  {parsedResume.text}
                </pre>
              </div>
            </div>
          </div>
        )}

        {/* Profile Information */}
        <div className="card-futuristic rounded-2xl p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-200">PROFILE INFORMATION</h2>
              <button
                onClick={() => setEditingProfile(!editingProfile)}
                className="btn-futuristic px-6 py-3 text-sm font-bold rounded-xl"
              >
                {editingProfile ? 'CANCEL' : 'EDIT'}
              </button>
            </div>

            {editingProfile ? (
              <div className="space-y-6">
                <div>
                  <label className="block text-lg font-semibold text-gray-200 mb-3">NAME</label>
                  <input
                    type="text"
                    value={profileData.name}
                    onChange={(e) => setProfileData(prev => ({ ...prev, name: e.target.value }))}
                    className="input-futuristic block w-full py-4 text-lg rounded-xl"
                  />
                </div>

                <div>
                  <label className="block text-lg font-semibold text-gray-200 mb-3">TITLE</label>
                  <input
                    type="text"
                    value={profileData.title}
                    onChange={(e) => setProfileData(prev => ({ ...prev, title: e.target.value }))}
                    className="input-futuristic block w-full py-4 text-lg rounded-xl"
                  />
                </div>

                <div>
                  <label className="block text-lg font-semibold text-gray-200 mb-3">LOCATION</label>
                  <input
                    type="text"
                    value={profileData.location}
                    onChange={(e) => setProfileData(prev => ({ ...prev, location: e.target.value }))}
                    className="input-futuristic block w-full py-4 text-lg rounded-xl"
                  />
                </div>

                <div>
                  <label className="block text-lg font-semibold text-gray-200 mb-3">PHONE</label>
                  <input
                    type="text"
                    value={profileData.phone}
                    onChange={(e) => setProfileData(prev => ({ ...prev, phone: e.target.value }))}
                    className="input-futuristic block w-full py-4 text-lg rounded-xl"
                  />
                </div>

                <div>
                  <label className="block text-lg font-semibold text-gray-200 mb-3">SUMMARY</label>
                  <textarea
                    rows={4}
                    value={profileData.summary}
                    onChange={(e) => setProfileData(prev => ({ ...prev, summary: e.target.value }))}
                    className="input-futuristic block w-full py-4 text-lg rounded-xl"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-3">
                    <label className="block text-lg font-semibold text-gray-200">SKILLS</label>
                    <button
                      onClick={addSkill}
                      className="text-cyan-400 hover:text-green-400 text-lg font-semibold transition-colors"
                    >
                      + ADD SKILL
                    </button>
                  </div>
                  <div className="space-y-3">
                    {profileData.skills.map((skill, index) => (
                      <div key={index} className="flex items-center space-x-3">
                        <input
                          type="text"
                          value={skill}
                          onChange={(e) => updateSkill(index, e.target.value)}
                          className="input-futuristic flex-1 py-3 text-lg rounded-xl"
                        />
                        <button
                          onClick={() => removeSkill(index)}
                          className="text-red-400 hover:text-red-300 text-2xl font-bold transition-colors"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex space-x-4">
                  <button
                    onClick={handleSaveProfile}
                    className="btn-futuristic px-8 py-4 text-lg font-bold rounded-xl"
                  >
                    SAVE PROFILE
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <div>
                  <span className="text-lg font-semibold text-gray-400">NAME:</span>
                  <p className="text-xl text-gray-200 mt-1">{profileData.name || 'Not set'}</p>
                </div>
                <div>
                  <span className="text-lg font-semibold text-gray-400">TITLE:</span>
                  <p className="text-xl text-gray-200 mt-1">{profileData.title || 'Not set'}</p>
                </div>
                <div>
                  <span className="text-lg font-semibold text-gray-400">LOCATION:</span>
                  <p className="text-xl text-gray-200 mt-1">{profileData.location || 'Not set'}</p>
                </div>
                <div>
                  <span className="text-lg font-semibold text-gray-400">PHONE:</span>
                  <p className="text-xl text-gray-200 mt-1">{profileData.phone || 'Not set'}</p>
                </div>
                <div>
                  <span className="text-lg font-semibold text-gray-400">SKILLS:</span>
                  <p className="text-xl text-gray-200 mt-1">
                    {profileData.skills.length > 0 
                      ? profileData.skills.join(', ')
                      : 'No skills added'
                    }
                  </p>
                </div>
              </div>
            )}
        </div>

        {/* Experience Section */}
        {editingProfile && (
          <div className="card-futuristic rounded-2xl p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-200">EXPERIENCE</h2>
              <button
                onClick={addExperience}
                className="btn-futuristic px-6 py-3 text-sm font-bold rounded-xl"
              >
                + ADD EXPERIENCE
              </button>
            </div>

            <div className="space-y-6">
              {profileData.experience.map((exp, index) => (
                <div key={index} className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Job Title</label>
                      <input
                        type="text"
                        value={exp.title}
                        onChange={(e) => updateExperience(index, 'title', e.target.value)}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Company</label>
                      <input
                        type="text"
                        value={exp.company}
                        onChange={(e) => updateExperience(index, 'company', e.target.value)}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Location</label>
                      <input
                        type="text"
                        value={exp.location}
                        onChange={(e) => updateExperience(index, 'location', e.target.value)}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Duration</label>
                      <div className="flex space-x-2">
                        <input
                          type="text"
                          placeholder="Start date"
                          value={exp.start_date}
                          onChange={(e) => updateExperience(index, 'start_date', e.target.value)}
                          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                        />
                        <input
                          type="text"
                          placeholder="End date"
                          value={exp.end_date}
                          onChange={(e) => updateExperience(index, 'end_date', e.target.value)}
                          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                        />
                      </div>
                    </div>
                  </div>
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700">Description</label>
                    <textarea
                      rows={3}
                      value={exp.description}
                      onChange={(e) => updateExperience(index, 'description', e.target.value)}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>
                  <div className="mt-4 flex justify-end">
                    <button
                      onClick={() => removeExperience(index)}
                      className="text-red-600 hover:text-red-500 text-sm"
                    >
                      Remove Experience
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
