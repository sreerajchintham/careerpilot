import React, { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { useRouter } from 'next/router'
import DashboardLayout from '../../components/DashboardLayout'
import { 
  User, 
  Mail,
  MapPin,
  Briefcase,
  Award,
  Github,
  Linkedin,
  Globe,
  Camera,
  Save,
  Bell,
  Lock,
  Settings as SettingsIcon,
  Trash2
} from 'lucide-react'
import toast from 'react-hot-toast'
import apiClient from '../../lib/api'

interface UserProfile {
  name?: string
  bio?: string
  location?: string
  current_role?: string
  experience_level?: string
  skills?: string[]
  linkedin_url?: string
  github_url?: string
  portfolio_url?: string
  avatar_url?: string
}

interface UserSettings {
  notifications: {
    email_on_application: boolean
    email_on_match: boolean
    email_weekly_summary: boolean
    push_notifications: boolean
  }
  privacy: {
    profile_visible: boolean
    show_resume: boolean
    anonymous_applications: boolean
  }
  application_preferences: {
    auto_apply_threshold: number
    preferred_job_types: string[]
    salary_min: number
    salary_max: number
    willing_to_relocate: boolean
  }
  email?: string
}

export default function Profile() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<'profile' | 'settings'>('profile')
  const [profile, setProfile] = useState<UserProfile>({})
  const [settings, setSettings] = useState<UserSettings | null>(null)
  const [loadingProfile, setLoadingProfile] = useState(true)
  const [saving, setSaving] = useState(false)
  const [avatarFile, setAvatarFile] = useState<File | null>(null)
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null)

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      fetchProfile()
      fetchSettings()
    }
  }, [user])

  const fetchProfile = async () => {
    if (!user?.id) return
    
    setLoadingProfile(true)
    try {
      const response = await apiClient.getUserProfile(user.id)
      setProfile(response.profile || {})
    } catch (error: any) {
      console.error('Error fetching profile:', error)
      toast.error('Failed to load profile')
    } finally {
      setLoadingProfile(false)
    }
  }

  const fetchSettings = async () => {
    if (!user?.id) return
    
    try {
      const response = await apiClient.getUserSettings(user.id)
      setSettings(response)
    } catch (error: any) {
      console.error('Error fetching settings:', error)
    }
  }

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        toast.error('Please select an image file')
        return
      }
      
      // Validate file size (5MB)
      if (file.size > 5 * 1024 * 1024) {
        toast.error('File size must be less than 5MB')
        return
      }
      
      setAvatarFile(file)
      
      // Create preview
      const reader = new FileReader()
      reader.onloadend = () => {
        setAvatarPreview(reader.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const uploadAvatar = async () => {
    if (!avatarFile || !user?.id) return
    
    const loadingToast = toast.loading('Uploading avatar...')
    try {
      const response = await apiClient.uploadAvatar(user.id, avatarFile)
      setProfile({ ...profile, avatar_url: response.avatar_url })
      setAvatarFile(null)
      setAvatarPreview(null)
      toast.success('Avatar uploaded successfully!')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to upload avatar')
    } finally {
      toast.dismiss(loadingToast)
    }
  }

  const deleteAvatar = async () => {
    if (!user?.id) return
    
    if (!confirm('Are you sure you want to delete your profile picture?')) return
    
    const loadingToast = toast.loading('Deleting avatar...')
    try {
      await apiClient.deleteAvatar(user.id)
      setProfile({ ...profile, avatar_url: undefined })
      toast.success('Avatar deleted successfully!')
    } catch (error: any) {
      toast.error('Failed to delete avatar')
    } finally {
      toast.dismiss(loadingToast)
    }
  }

  const saveProfile = async () => {
    if (!user?.id) return
    
    setSaving(true)
    try {
      // Upload avatar first if selected
      if (avatarFile) {
        await uploadAvatar()
      }
      
      await apiClient.updateUserProfile(user.id, profile)
      toast.success('Profile updated successfully!')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to update profile')
    } finally {
      setSaving(false)
    }
  }

  const saveSettings = async () => {
    if (!user?.id || !settings) return
    
    setSaving(true)
    try {
      await apiClient.updateUserSettings(user.id, settings)
      toast.success('Settings updated successfully!')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to update settings')
    } finally {
      setSaving(false)
    }
  }

  if (loading || loadingProfile) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">
            PROFILE & SETTINGS
          </h1>
          <p className="mt-2 text-lg text-gray-300">
            Manage your account information and preferences
          </p>
        </div>

        {/* Tabs */}
        <div className="flex space-x-4 border-b border-gray-700">
          <button
            onClick={() => setActiveTab('profile')}
            className={`px-6 py-3 font-bold transition-all ${
              activeTab === 'profile'
                ? 'text-cyan-400 border-b-2 border-cyan-400'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <User className="h-5 w-5 inline mr-2" />
            PROFILE
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`px-6 py-3 font-bold transition-all ${
              activeTab === 'settings'
                ? 'text-cyan-400 border-b-2 border-cyan-400'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <SettingsIcon className="h-5 w-5 inline mr-2" />
            SETTINGS
          </button>
        </div>

        {/* Profile Tab */}
        {activeTab === 'profile' && (
          <div className="space-y-6">
            {/* Avatar Section */}
            <div className="card-futuristic rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-gray-200 mb-6">
                <Camera className="h-6 w-6 inline mr-2 text-cyan-400" />
                PROFILE PICTURE
              </h2>

              <div className="flex items-center space-x-6">
                {/* Avatar Display */}
                <div className="relative">
                  <div className="w-32 h-32 rounded-full overflow-hidden bg-gradient-to-br from-cyan-500 to-green-500 p-1">
                    <div className="w-full h-full rounded-full overflow-hidden bg-gray-900">
                      {(avatarPreview || profile.avatar_url) ? (
                        <img 
                          src={avatarPreview || profile.avatar_url} 
                          alt="Avatar" 
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <User className="h-16 w-16 text-gray-600" />
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Avatar Controls */}
                <div className="flex-1 space-y-4">
                  <div>
                    <label className="btn-futuristic px-6 py-3 rounded-lg font-bold cursor-pointer inline-flex items-center">
                      <Camera className="h-5 w-5 mr-2" />
                      CHOOSE IMAGE
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleAvatarChange}
                        className="hidden"
                      />
                    </label>
                  </div>

                  {avatarPreview && (
                    <button
                      onClick={uploadAvatar}
                      disabled={saving}
                      className="bg-gradient-to-r from-green-500 to-emerald-500 text-white px-6 py-3 rounded-lg font-bold hover:from-green-600 hover:to-emerald-600 disabled:opacity-50 glow-green transition-all"
                    >
                      <Save className="h-5 w-5 inline mr-2" />
                      UPLOAD NEW AVATAR
                    </button>
                  )}

                  {profile.avatar_url && !avatarPreview && (
                    <button
                      onClick={deleteAvatar}
                      className="bg-gradient-to-r from-red-500 to-pink-500 text-white px-6 py-3 rounded-lg font-bold hover:from-red-600 hover:to-pink-600 transition-all"
                    >
                      <Trash2 className="h-5 w-5 inline mr-2" />
                      DELETE AVATAR
                    </button>
                  )}

                  <p className="text-sm text-gray-400">
                    JPG, PNG or GIF. Max 5MB.
                  </p>
                </div>
              </div>
            </div>

            {/* Basic Info */}
            <div className="card-futuristic rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-gray-200 mb-6">
                <User className="h-6 w-6 inline mr-2 text-cyan-400" />
                BASIC INFORMATION
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={profile.name || ''}
                    onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-200 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                    placeholder="John Doe"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    <Mail className="h-4 w-4 inline mr-1" />
                    Email (read-only)
                  </label>
                  <input
                    type="email"
                    value={user?.email || ''}
                    disabled
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-gray-400 cursor-not-allowed"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    <MapPin className="h-4 w-4 inline mr-1" />
                    Location
                  </label>
                  <input
                    type="text"
                    value={profile.location || ''}
                    onChange={(e) => setProfile({ ...profile, location: e.target.value })}
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-200 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                    placeholder="San Francisco, CA"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    <Briefcase className="h-4 w-4 inline mr-1" />
                    Current Role
                  </label>
                  <input
                    type="text"
                    value={profile.current_role || ''}
                    onChange={(e) => setProfile({ ...profile, current_role: e.target.value })}
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-200 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                    placeholder="Senior Software Engineer"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Bio
                  </label>
                  <textarea
                    value={profile.bio || ''}
                    onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                    rows={4}
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-200 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                    placeholder="Tell us about yourself..."
                  />
                </div>
              </div>
            </div>

            {/* Social Links */}
            <div className="card-futuristic rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-gray-200 mb-6">
                <Globe className="h-6 w-6 inline mr-2 text-cyan-400" />
                SOCIAL LINKS
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    <Linkedin className="h-4 w-4 inline mr-1" />
                    LinkedIn URL
                  </label>
                  <input
                    type="url"
                    value={profile.linkedin_url || ''}
                    onChange={(e) => setProfile({ ...profile, linkedin_url: e.target.value })}
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-200 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                    placeholder="https://linkedin.com/in/yourprofile"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    <Github className="h-4 w-4 inline mr-1" />
                    GitHub URL
                  </label>
                  <input
                    type="url"
                    value={profile.github_url || ''}
                    onChange={(e) => setProfile({ ...profile, github_url: e.target.value })}
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-200 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                    placeholder="https://github.com/yourusername"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    <Globe className="h-4 w-4 inline mr-1" />
                    Portfolio URL
                  </label>
                  <input
                    type="url"
                    value={profile.portfolio_url || ''}
                    onChange={(e) => setProfile({ ...profile, portfolio_url: e.target.value })}
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-200 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                    placeholder="https://yourportfolio.com"
                  />
                </div>
              </div>
            </div>

            {/* Save Button */}
            <div className="flex justify-end">
              <button
                onClick={saveProfile}
                disabled={saving}
                className="bg-gradient-to-r from-cyan-500 to-green-500 text-white px-8 py-4 rounded-xl font-bold text-lg hover:from-cyan-600 hover:to-green-600 disabled:opacity-50 glow-cyan transition-all"
              >
                <Save className="h-6 w-6 inline mr-2" />
                {saving ? 'SAVING...' : 'SAVE PROFILE'}
              </button>
            </div>
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === 'settings' && settings && (
          <div className="space-y-6">
            {/* Notifications */}
            <div className="card-futuristic rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-gray-200 mb-6">
                <Bell className="h-6 w-6 inline mr-2 text-cyan-400" />
                NOTIFICATIONS
              </h2>

              <div className="space-y-4">
                {Object.entries(settings.notifications).map(([key, value]) => (
                  <label key={key} className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg cursor-pointer hover:bg-gray-900 transition-all">
                    <span className="text-gray-200">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                    </span>
                    <input
                      type="checkbox"
                      checked={value}
                      onChange={(e) => setSettings({
                        ...settings,
                        notifications: {
                          ...settings.notifications,
                          [key]: e.target.checked
                        }
                      })}
                      className="w-5 h-5 text-cyan-500 bg-gray-700 border-gray-600 rounded focus:ring-cyan-500"
                    />
                  </label>
                ))}
              </div>
            </div>

            {/* Privacy */}
            <div className="card-futuristic rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-gray-200 mb-6">
                <Lock className="h-6 w-6 inline mr-2 text-cyan-400" />
                PRIVACY
              </h2>

              <div className="space-y-4">
                {Object.entries(settings.privacy).map(([key, value]) => (
                  <label key={key} className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg cursor-pointer hover:bg-gray-900 transition-all">
                    <span className="text-gray-200">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                    </span>
                    <input
                      type="checkbox"
                      checked={value}
                      onChange={(e) => setSettings({
                        ...settings,
                        privacy: {
                          ...settings.privacy,
                          [key]: e.target.checked
                        }
                      })}
                      className="w-5 h-5 text-cyan-500 bg-gray-700 border-gray-600 rounded focus:ring-cyan-500"
                    />
                  </label>
                ))}
              </div>
            </div>

            {/* Application Preferences */}
            <div className="card-futuristic rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-gray-200 mb-6">
                <Briefcase className="h-6 w-6 inline mr-2 text-cyan-400" />
                APPLICATION PREFERENCES
              </h2>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Auto-Apply Threshold (Match Score %)
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={settings.application_preferences.auto_apply_threshold}
                    onChange={(e) => setSettings({
                      ...settings,
                      application_preferences: {
                        ...settings.application_preferences,
                        auto_apply_threshold: parseInt(e.target.value)
                      }
                    })}
                    className="w-full"
                  />
                  <div className="flex justify-between text-sm text-gray-400 mt-2">
                    <span>0%</span>
                    <span className="text-cyan-400 font-bold">{settings.application_preferences.auto_apply_threshold}%</span>
                    <span>100%</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">
                      Minimum Salary ($)
                    </label>
                    <input
                      type="number"
                      value={settings.application_preferences.salary_min}
                      onChange={(e) => setSettings({
                        ...settings,
                        application_preferences: {
                          ...settings.application_preferences,
                          salary_min: parseInt(e.target.value) || 0
                        }
                      })}
                      className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-200 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                      placeholder="0"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">
                      Maximum Salary ($)
                    </label>
                    <input
                      type="number"
                      value={settings.application_preferences.salary_max}
                      onChange={(e) => setSettings({
                        ...settings,
                        application_preferences: {
                          ...settings.application_preferences,
                          salary_max: parseInt(e.target.value) || 0
                        }
                      })}
                      className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-gray-200 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                      placeholder="0"
                    />
                  </div>
                </div>

                <label className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg cursor-pointer hover:bg-gray-900 transition-all">
                  <span className="text-gray-200">Willing to Relocate</span>
                  <input
                    type="checkbox"
                    checked={settings.application_preferences.willing_to_relocate}
                    onChange={(e) => setSettings({
                      ...settings,
                      application_preferences: {
                        ...settings.application_preferences,
                        willing_to_relocate: e.target.checked
                      }
                    })}
                    className="w-5 h-5 text-cyan-500 bg-gray-700 border-gray-600 rounded focus:ring-cyan-500"
                  />
                </label>
              </div>
            </div>

            {/* Save Button */}
            <div className="flex justify-end">
              <button
                onClick={saveSettings}
                disabled={saving}
                className="bg-gradient-to-r from-cyan-500 to-green-500 text-white px-8 py-4 rounded-xl font-bold text-lg hover:from-cyan-600 hover:to-green-600 disabled:opacity-50 glow-cyan transition-all"
              >
                <Save className="h-6 w-6 inline mr-2" />
                {saving ? 'SAVING...' : 'SAVE SETTINGS'}
              </button>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}

