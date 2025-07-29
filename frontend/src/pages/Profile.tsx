import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  User, 
  Settings, 
  MapPin, 
  Plane, 
  Bell, 
  Shield, 
  CreditCard,
  Globe,
  Save,
  Edit3,
  Camera,
  Mail,
  Calendar,
  Award,
  TrendingUp
} from 'lucide-react'
import { useAuthStore } from '../stores/authStore'

interface UserStats {
  tripsCompleted: number
  tripsPlanned: number
  countriesVisited: number
  totalDistance: number
}

interface TravelPreferences {
  preferredAccommodation: 'budget' | 'standard' | 'luxury'
  preferredTransport: 'flights' | 'trains' | 'cars' | 'mixed'
  budgetRange: string
  travelStyle: 'adventure' | 'relaxed' | 'cultural' | 'party'
  groupSize: 'small' | 'medium' | 'large'
}

interface NotificationSettings {
  emailNotifications: boolean
  tripUpdates: boolean
  newMembers: boolean
  bookingReminders: boolean
  marketingEmails: boolean
}

export function Profile() {
  const { user, logout } = useAuthStore()
  const [activeTab, setActiveTab] = useState<'profile' | 'preferences' | 'notifications' | 'security'>('profile')
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  // Mock user stats
  const [userStats] = useState<UserStats>({
    tripsCompleted: 3,
    tripsPlanned: 2,
    countriesVisited: 8,
    totalDistance: 15420
  })

  // User profile form data
  const [profileData, setProfileData] = useState({
    fullName: user?.fullName || '',
    email: user?.email || '',
    bio: 'Love exploring new places and making memories with friends!',
    location: 'San Francisco, CA',
    phone: '+1 (555) 123-4567',
    dateOfBirth: '1990-05-15'
  })

  // Travel preferences
  const [preferences, setPreferences] = useState<TravelPreferences>({
    preferredAccommodation: 'standard',
    preferredTransport: 'mixed',
    budgetRange: '1000-2000',
    travelStyle: 'cultural',
    groupSize: 'medium'
  })

  // Notification settings
  const [notifications, setNotifications] = useState<NotificationSettings>({
    emailNotifications: true,
    tripUpdates: true,
    newMembers: true,
    bookingReminders: true,
    marketingEmails: false
  })

  const handleSaveProfile = async () => {
    setIsSaving(true)
    // TODO: API call to save profile data
    await new Promise(resolve => setTimeout(resolve, 1000)) // Mock delay
    setIsSaving(false)
    setIsEditing(false)
  }

  const handleSavePreferences = async () => {
    setIsSaving(true)
    // TODO: API call to save preferences
    await new Promise(resolve => setTimeout(resolve, 1000)) // Mock delay
    setIsSaving(false)
  }

  const handleSaveNotifications = async () => {
    setIsSaving(true)
    // TODO: API call to save notification settings
    await new Promise(resolve => setTimeout(resolve, 1000)) // Mock delay
    setIsSaving(false)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Profile Settings
              </h1>
              <p className="text-gray-600">
                Manage your account, preferences, and travel settings
              </p>
            </div>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar Navigation */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="lg:col-span-1"
          >
            <div className="card">
              {/* Profile Header */}
              <div className="text-center mb-6 pb-6 border-b border-gray-200">
                <div className="relative inline-block">
                  <div className="h-20 w-20 rounded-full bg-primary-600 flex items-center justify-center mx-auto mb-3">
                    <span className="text-2xl font-bold text-white">
                      {user?.fullName?.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <button className="absolute bottom-0 right-0 p-1.5 bg-white rounded-full shadow-md border-2 border-gray-100 hover:bg-gray-50 transition-colors">
                    <Camera className="h-3 w-3 text-gray-600" />
                  </button>
                </div>
                <h3 className="font-semibold text-gray-900">{user?.fullName}</h3>
                <p className="text-sm text-gray-600">{user?.email}</p>
              </div>

              {/* Navigation Menu */}
              <nav className="space-y-1">
                {[
                  { id: 'profile', name: 'Profile', icon: User },
                  { id: 'preferences', name: 'Travel Preferences', icon: MapPin },
                  { id: 'notifications', name: 'Notifications', icon: Bell },
                  { id: 'security', name: 'Security', icon: Shield }
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id as any)}
                    className={`w-full flex items-center space-x-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                      activeTab === item.id
                        ? 'bg-primary-100 text-primary-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <item.icon className="h-4 w-4" />
                    <span>{item.name}</span>
                  </button>
                ))}
              </nav>
            </div>

            {/* User Stats */}
            <div className="card mt-6">
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                <Award className="h-4 w-4 mr-2" />
                Travel Stats
              </h4>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Trips Completed</span>
                  <span className="font-semibold text-green-600">{userStats.tripsCompleted}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Trips Planned</span>
                  <span className="font-semibold text-blue-600">{userStats.tripsPlanned}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Countries Visited</span>
                  <span className="font-semibold text-purple-600">{userStats.countriesVisited}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Distance Traveled</span>
                  <span className="font-semibold text-orange-600">{userStats.totalDistance.toLocaleString()} km</span>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Main Content */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="lg:col-span-3"
          >
            {activeTab === 'profile' && (
              <div className="card">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">Personal Information</h2>
                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    className="btn-secondary flex items-center space-x-2"
                  >
                    <Edit3 className="h-4 w-4" />
                    <span>{isEditing ? 'Cancel' : 'Edit'}</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={profileData.fullName}
                      onChange={(e) => setProfileData(prev => ({ ...prev, fullName: e.target.value }))}
                      disabled={!isEditing}
                      className="input-field disabled:bg-gray-50 disabled:text-gray-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Address
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <input
                        type="email"
                        value={profileData.email}
                        onChange={(e) => setProfileData(prev => ({ ...prev, email: e.target.value }))}
                        disabled={!isEditing}
                        className="input-field pl-10 disabled:bg-gray-50 disabled:text-gray-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Phone Number
                    </label>
                    <input
                      type="tel"
                      value={profileData.phone}
                      onChange={(e) => setProfileData(prev => ({ ...prev, phone: e.target.value }))}
                      disabled={!isEditing}
                      className="input-field disabled:bg-gray-50 disabled:text-gray-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Date of Birth
                    </label>
                    <div className="relative">
                      <Calendar className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <input
                        type="date"
                        value={profileData.dateOfBirth}
                        onChange={(e) => setProfileData(prev => ({ ...prev, dateOfBirth: e.target.value }))}
                        disabled={!isEditing}
                        className="input-field pl-10 disabled:bg-gray-50 disabled:text-gray-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Location
                    </label>
                    <div className="relative">
                      <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <input
                        type="text"
                        value={profileData.location}
                        onChange={(e) => setProfileData(prev => ({ ...prev, location: e.target.value }))}
                        disabled={!isEditing}
                        className="input-field pl-10 disabled:bg-gray-50 disabled:text-gray-500"
                      />
                    </div>
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Bio
                    </label>
                    <textarea
                      value={profileData.bio}
                      onChange={(e) => setProfileData(prev => ({ ...prev, bio: e.target.value }))}
                      disabled={!isEditing}
                      rows={3}
                      className="input-field disabled:bg-gray-50 disabled:text-gray-500"
                    />
                  </div>
                </div>

                {isEditing && (
                  <div className="flex items-center justify-end space-x-3 mt-6 pt-6 border-t border-gray-200">
                    <button
                      onClick={() => setIsEditing(false)}
                      className="btn-secondary"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveProfile}
                      disabled={isSaving}
                      className="btn-primary flex items-center space-x-2 disabled:opacity-50"
                    >
                      {isSaving ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                          <span>Saving...</span>
                        </>
                      ) : (
                        <>
                          <Save className="h-4 w-4" />
                          <span>Save Changes</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'preferences' && (
              <div className="space-y-6">
                <div className="card">
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">Travel Preferences</h2>

                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-3">
                        Preferred Accommodation
                      </label>
                      <div className="grid grid-cols-3 gap-4">
                        {[
                          { value: 'budget', label: 'Budget', desc: 'Hostels, basic hotels' },
                          { value: 'standard', label: 'Standard', desc: '3-4 star hotels' },
                          { value: 'luxury', label: 'Luxury', desc: '5 star hotels, resorts' }
                        ].map((option) => (
                          <button
                            key={option.value}
                            onClick={() => setPreferences(prev => ({ ...prev, preferredAccommodation: option.value as any }))}
                            className={`p-4 border-2 rounded-lg transition-all text-left ${
                              preferences.preferredAccommodation === option.value
                                ? 'border-primary-600 bg-primary-50'
                                : 'border-gray-300 hover:border-gray-400'
                            }`}
                          >
                            <div className="font-medium">{option.label}</div>
                            <div className="text-sm text-gray-500">{option.desc}</div>
                          </button>
                        ))}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-3">
                        Travel Style
                      </label>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {[
                          { value: 'adventure', label: 'Adventure', icon: '🏔️' },
                          { value: 'relaxed', label: 'Relaxed', icon: '🏖️' },
                          { value: 'cultural', label: 'Cultural', icon: '🏛️' },
                          { value: 'party', label: 'Nightlife', icon: '🎉' }
                        ].map((style) => (
                          <button
                            key={style.value}
                            onClick={() => setPreferences(prev => ({ ...prev, travelStyle: style.value as any }))}
                            className={`p-4 border-2 rounded-lg transition-all text-center ${
                              preferences.travelStyle === style.value
                                ? 'border-primary-600 bg-primary-50'
                                : 'border-gray-300 hover:border-gray-400'
                            }`}
                          >
                            <div className="text-2xl mb-2">{style.icon}</div>
                            <div className="font-medium">{style.label}</div>
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Budget Range (USD)
                        </label>
                        <select
                          value={preferences.budgetRange}
                          onChange={(e) => setPreferences(prev => ({ ...prev, budgetRange: e.target.value }))}
                          className="input-field"
                        >
                          <option value="500-1000">$500 - $1,000</option>
                          <option value="1000-2000">$1,000 - $2,000</option>
                          <option value="2000-5000">$2,000 - $5,000</option>
                          <option value="5000+">$5,000+</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Preferred Group Size
                        </label>
                        <select
                          value={preferences.groupSize}
                          onChange={(e) => setPreferences(prev => ({ ...prev, groupSize: e.target.value as any }))}
                          className="input-field"
                        >
                          <option value="small">Small (2-4 people)</option>
                          <option value="medium">Medium (5-8 people)</option>
                          <option value="large">Large (9+ people)</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end mt-6 pt-6 border-t border-gray-200">
                    <button
                      onClick={handleSavePreferences}
                      disabled={isSaving}
                      className="btn-primary flex items-center space-x-2 disabled:opacity-50"
                    >
                      {isSaving ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                          <span>Saving...</span>
                        </>
                      ) : (
                        <>
                          <Save className="h-4 w-4" />
                          <span>Save Preferences</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'notifications' && (
              <div className="card">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Notification Settings</h2>

                <div className="space-y-6">
                  {[
                    {
                      key: 'emailNotifications' as keyof NotificationSettings,
                      title: 'Email Notifications',
                      description: 'Receive notifications via email'
                    },
                    {
                      key: 'tripUpdates' as keyof NotificationSettings,
                      title: 'Trip Updates',
                      description: 'Get notified when trip details change'
                    },
                    {
                      key: 'newMembers' as keyof NotificationSettings,
                      title: 'New Members',
                      description: 'Alert when someone joins your trips'
                    },
                    {
                      key: 'bookingReminders' as keyof NotificationSettings,
                      title: 'Booking Reminders',
                      description: 'Reminders for important booking deadlines'
                    },
                    {
                      key: 'marketingEmails' as keyof NotificationSettings,
                      title: 'Marketing Emails',
                      description: 'Receive travel deals and promotions'
                    }
                  ].map((setting) => (
                    <div key={setting.key} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div>
                        <h4 className="font-medium text-gray-900">{setting.title}</h4>
                        <p className="text-sm text-gray-600">{setting.description}</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={notifications[setting.key]}
                          onChange={(e) => setNotifications(prev => ({ ...prev, [setting.key]: e.target.checked }))}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                      </label>
                    </div>
                  ))}
                </div>

                <div className="flex justify-end mt-6 pt-6 border-t border-gray-200">
                  <button
                    onClick={handleSaveNotifications}
                    disabled={isSaving}
                    className="btn-primary flex items-center space-x-2 disabled:opacity-50"
                  >
                    {isSaving ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                        <span>Saving...</span>
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4" />
                        <span>Save Settings</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'security' && (
              <div className="space-y-6">
                <div className="card">
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">Security Settings</h2>

                  <div className="space-y-6">
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <h4 className="font-medium text-gray-900 mb-2">Password</h4>
                      <p className="text-sm text-gray-600 mb-4">
                        Keep your account secure with a strong password
                      </p>
                      <button className="btn-secondary">
                        Change Password
                      </button>
                    </div>

                    <div className="p-4 bg-gray-50 rounded-lg">
                      <h4 className="font-medium text-gray-900 mb-2">Two-Factor Authentication</h4>
                      <p className="text-sm text-gray-600 mb-4">
                        Add an extra layer of security to your account
                      </p>
                      <button className="btn-primary">
                        Enable 2FA
                      </button>
                    </div>

                    <div className="p-4 bg-gray-50 rounded-lg">
                      <h4 className="font-medium text-gray-900 mb-2">Active Sessions</h4>
                      <p className="text-sm text-gray-600 mb-4">
                        Manage devices that are currently logged into your account
                      </p>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between p-3 bg-white rounded border">
                          <div>
                            <div className="font-medium text-sm">Current Device</div>
                            <div className="text-xs text-gray-500">Chrome on macOS • Last active: Now</div>
                          </div>
                          <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Active</span>
                        </div>
                      </div>
                    </div>

                    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                      <h4 className="font-medium text-red-900 mb-2">Danger Zone</h4>
                      <p className="text-sm text-red-700 mb-4">
                        Permanently delete your account and all associated data
                      </p>
                      <button className="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors">
                        Delete Account
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  )
} 