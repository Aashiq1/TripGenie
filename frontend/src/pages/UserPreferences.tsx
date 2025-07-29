import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  User,
  ArrowRight,
  ArrowLeft,
  Loader2,
  CheckCircle,
  AlertCircle,
  Coffee,
  Zap,
  Heart,
  MapPin,
  Plane,
  Clock,
  Edit3,
  Eye
} from 'lucide-react'
import { useAuthStore } from '../stores/authStore'

interface UserPreferences {
  phone: string
  vibe: string[]
  interests: string[]
  departure_airports: string[]
  budget_min: number
  budget_max: number
  trip_duration: number
  travel_style: 'budget' | 'balanced' | 'luxury'
  pace: 'chill' | 'balanced' | 'fast'
  accommodation_preference: 'budget' | 'standard' | 'luxury'
  room_sharing: 'private' | 'share' | 'any'
  availability_dates: string[]
  dietary_restrictions: string[]
  additional_info: string
}

export function UserPreferences() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const { groupCode } = useParams<{ groupCode: string }>()
  const [isLoading, setIsLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [hasExistingPreferences, setHasExistingPreferences] = useState(false)
  
  const [userPreferences, setUserPreferences] = useState<UserPreferences>({
    phone: '',
    vibe: [],
    interests: [],
    departure_airports: [],
    budget_min: 500,
    budget_max: 2000,
    trip_duration: 7,
    travel_style: 'balanced',
    pace: 'balanced',
    accommodation_preference: 'standard',
    room_sharing: 'any',
    availability_dates: [],
    dietary_restrictions: [],
    additional_info: ''
  })

  const vibeOptions = [
    { value: 'relaxing', label: 'Relaxing', icon: Coffee },
    { value: 'adventurous', label: 'Adventurous', icon: Zap },
    { value: 'party', label: 'Party', icon: Heart },
    { value: 'culture', label: 'Culture', icon: MapPin }
  ]

  const interestOptions = [
    'Food & Cuisine', 'Museums & Art', 'Nightlife', 'Adventure Sports',
    'Shopping', 'Nature & Hiking', 'History', 'Photography',
    'Local Markets', 'Architecture', 'Beaches', 'Music & Concerts'
  ]

  const airportOptions = [
    'LAX', 'JFK', 'ORD', 'DFW', 'ATL', 'SFO', 'LAS', 'SEA',
    'MIA', 'BOS', 'DEN', 'PHX', 'IAH', 'EWR', 'MSP', 'DTW'
  ]

  const dietaryOptions = [
    'Vegetarian', 'Vegan', 'Gluten-Free', 'Dairy-Free',
    'Nut Allergy', 'Halal', 'Kosher', 'Pescatarian'
  ]

  useEffect(() => {
    const fetchUserPreferences = async () => {
      if (!groupCode || !user) return

      setIsLoading(true)
      try {
        const { tripAPI } = await import('../services/api')
        const tripDetails = await tripAPI.getTripDetails(groupCode)
        
        if (tripDetails && tripDetails.groupData) {
          // Find current user's preferences in the group data
          const userInGroup = tripDetails.groupData.find((member: any) => member.email === user.email)
          
          if (userInGroup && userInGroup.preferences) {
            setHasExistingPreferences(true)
            const prefs = userInGroup.preferences
            setUserPreferences({
              phone: userInGroup.phone || '',
              vibe: prefs.vibe || [],
              interests: prefs.interests || [],
              departure_airports: prefs.departure_airports || [],
              budget_min: prefs.budget?.min || 500,
              budget_max: prefs.budget?.max || 2000,
              trip_duration: prefs.trip_duration || 7,
              travel_style: prefs.travel_style || 'balanced',
              pace: prefs.pace || 'balanced',
              accommodation_preference: prefs.accommodation_preference || 'standard',
              room_sharing: prefs.room_sharing || 'any',
              availability_dates: userInGroup.availability?.dates || [],
              dietary_restrictions: prefs.dietary_restrictions || [],
              additional_info: prefs.additional_info || ''
            })
          }
        }
      } catch (error: any) {
        console.error('Failed to fetch user preferences:', error)
        setError('Failed to load your preferences.')
      } finally {
        setIsLoading(false)
      }
    }

    fetchUserPreferences()
  }, [groupCode, user])

  const updatePreferences = (field: keyof UserPreferences, value: any) => {
    setUserPreferences(prev => ({ ...prev, [field]: value }))
  }

  const toggleArrayValue = (field: keyof UserPreferences, value: string) => {
    setUserPreferences(prev => {
      const currentArray = prev[field] as string[]
      const newArray = currentArray.includes(value)
        ? currentArray.filter(item => item !== value)
        : [...currentArray, value]
      return { ...prev, [field]: newArray }
    })
  }

  const handleSubmit = async () => {
    if (!groupCode || !user) return

    // Validation
    if (!userPreferences.phone.trim()) {
      setError('Phone number is required')
      return
    }
    if (userPreferences.vibe.length === 0) {
      setError('Please select at least one vibe')
      return
    }
    if (userPreferences.interests.length === 0) {
      setError('Please select at least one interest')
      return
    }
    if (userPreferences.departure_airports.length === 0) {
      setError('Please select at least one departure airport')
      return
    }
    if (userPreferences.availability_dates.length === 0) {
      setError('Please select at least one available date')
      return
    }

    setIsSubmitting(true)
    setError(null)
    
    try {
      const { tripAPI } = await import('../services/api')
      
      // Create comprehensive user input data (without destinations)
      const userInput = {
        name: user.fullName,
        email: user.email,
        phone: userPreferences.phone,
        role: 'member', // Will be corrected on backend if user is actually creator
        preferences: {
          vibe: userPreferences.vibe,
          interests: userPreferences.interests,
          departure_airports: userPreferences.departure_airports,
          budget: {
            min: userPreferences.budget_min,
            max: userPreferences.budget_max
          },
          trip_duration: userPreferences.trip_duration,
          travel_style: userPreferences.travel_style,
          pace: userPreferences.pace,
          accommodation_preference: userPreferences.accommodation_preference,
          room_sharing: userPreferences.room_sharing,
          dietary_restrictions: userPreferences.dietary_restrictions.length > 0 ? userPreferences.dietary_restrictions : null,
          additional_info: userPreferences.additional_info || null
        },
        availability: {
          dates: userPreferences.availability_dates
        }
      }

      const result = await tripAPI.joinTrip(groupCode, userInput)
      
      if (result.success) {
        setSuccess(true)
        setError(null)
        setIsEditing(false)
        setHasExistingPreferences(true)
        
        // Only auto-redirect in production, not development
        const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        
        if (!isDevelopment) {
          // Show success message and redirect
          setTimeout(() => {
            navigate(`/trip/${groupCode}`)
          }, 2000)
        }
      } else {
        setError(result.message || 'Failed to update preferences')
      }
    } catch (error: any) {
      console.error('Failed to update preferences:', error)
      setError('Failed to update preferences. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Generate next 30 days for availability selection
  const generateAvailableDates = () => {
    const dates = []
    const today = new Date()
    for (let i = 0; i < 30; i++) {
      const date = new Date(today)
      date.setDate(today.getDate() + i)
      dates.push(date.toISOString().split('T')[0])
    }
    return dates
  }

  const availableDates = generateAvailableDates()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your preferences...</p>
        </div>
      </div>
    )
  }

  // Success state
  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="max-w-md w-full"
        >
          <div className="card text-center">
            <div className="bg-green-600 p-6 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="h-10 w-10 text-white" />
            </div>
            
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Preferences Updated! 🎉
            </h1>
            
            <div className="mb-6">
              <p className="text-gray-600 mb-2">
                Your trip preferences have been saved successfully.
              </p>
              
              {(window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') ? (
                <div className="space-y-3">
                  <div className="text-xs text-orange-600 bg-orange-50 border border-orange-200 rounded p-2">
                    💡 Auto-redirect disabled in development mode for console debugging
                  </div>
                  <button
                    onClick={() => navigate(`/trip/${groupCode}`)}
                    className="btn-primary w-full"
                  >
                    Go to Trip Details
                  </button>
                </div>
              ) : (
                <div className="flex items-center justify-center space-x-2 text-primary-600">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm font-medium">Redirecting you back to the trip...</span>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-8"
        >
          <div className="bg-primary-600 p-4 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
            <User className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {hasExistingPreferences ? 'Your Trip Preferences' : 'Add Your Preferences'}
          </h1>
          <p className="text-gray-600">
            {hasExistingPreferences 
              ? 'View and update your travel preferences for this trip'
              : 'Tell us about your travel preferences to help plan the perfect trip'
            }
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="card"
        >
          {/* Toggle View/Edit Mode */}
          {hasExistingPreferences && !isEditing && (
            <div className="flex items-center justify-between mb-6 pb-6 border-b border-gray-200">
              <div className="flex items-center space-x-2">
                <Eye className="h-5 w-5 text-gray-600" />
                <span className="text-lg font-semibold text-gray-900">Viewing Mode</span>
              </div>
              <button
                onClick={() => setIsEditing(true)}
                className="btn-primary flex items-center space-x-2"
              >
                <Edit3 className="h-4 w-4" />
                <span>Edit Preferences</span>
              </button>
            </div>
          )}

          {isEditing && (
            <div className="flex items-center justify-between mb-6 pb-6 border-b border-gray-200">
              <div className="flex items-center space-x-2">
                <Edit3 className="h-5 w-5 text-primary-600" />
                <span className="text-lg font-semibold text-gray-900">Editing Mode</span>
              </div>
              <button
                onClick={() => {
                  setIsEditing(false)
                  setError(null)
                }}
                className="btn-secondary flex items-center space-x-2"
              >
                <Eye className="h-4 w-4" />
                <span>View Only</span>
              </button>
            </div>
          )}

          <div className="space-y-8">
            {/* Destinations */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Trip Destinations
              </label>
              {isEditing ? (
                <div className="space-y-2">
                  {/* Destinations are now managed by the creator, so this section is removed */}
                </div>
              ) : (
                <div className="p-3 bg-gray-50 rounded-lg border">
                  Destinations are managed by the trip creator.
                </div>
              )}
            </div>

            {/* Phone Number */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Phone Number *
              </label>
              {isEditing ? (
                <input
                  type="tel"
                  value={userPreferences.phone}
                  onChange={(e) => updatePreferences('phone', e.target.value)}
                  placeholder="Your phone number"
                  className="input-field"
                  required
                />
              ) : (
                <div className="p-3 bg-gray-50 rounded-lg border">
                  {userPreferences.phone || 'Not set'}
                </div>
              )}
            </div>

            {/* Travel Vibe */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Travel Vibe * <span className="text-gray-500">(Select all that apply)</span>
              </label>
              <div className="grid grid-cols-2 gap-3">
                {vibeOptions.map((option) => (
                  <div
                    key={option.value}
                    className={`p-4 rounded-lg border-2 transition-all flex items-center space-x-3 ${
                      userPreferences.vibe.includes(option.value)
                        ? 'border-primary-600 bg-primary-50 text-primary-700'
                        : 'border-gray-200'
                    } ${isEditing ? 'cursor-pointer hover:border-gray-300' : ''}`}
                    onClick={isEditing ? () => toggleArrayValue('vibe', option.value) : undefined}
                  >
                    <option.icon className="h-5 w-5" />
                    <span className="font-medium">{option.label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Interests */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Interests * <span className="text-gray-500">(Select all that apply)</span>
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {interestOptions.map((interest) => (
                  <div
                    key={interest}
                    className={`p-3 rounded-lg border text-sm transition-all ${
                      userPreferences.interests.includes(interest)
                        ? 'border-primary-600 bg-primary-50 text-primary-700'
                        : 'border-gray-200'
                    } ${isEditing ? 'cursor-pointer hover:border-gray-300' : ''}`}
                    onClick={isEditing ? () => toggleArrayValue('interests', interest) : undefined}
                  >
                    {interest}
                  </div>
                ))}
              </div>
            </div>

            {/* Departure Airports */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Departure Airports * <span className="text-gray-500">(Your preferred airports)</span>
              </label>
              <div className="grid grid-cols-4 md:grid-cols-8 gap-2">
                {airportOptions.map((airport) => (
                  <div
                    key={airport}
                    className={`p-3 rounded-lg border text-sm font-mono transition-all text-center ${
                      userPreferences.departure_airports.includes(airport)
                        ? 'border-primary-600 bg-primary-50 text-primary-700'
                        : 'border-gray-200'
                    } ${isEditing ? 'cursor-pointer hover:border-gray-300' : ''}`}
                    onClick={isEditing ? () => toggleArrayValue('departure_airports', airport) : undefined}
                  >
                    {airport}
                  </div>
                ))}
              </div>
            </div>

            {/* Budget Range */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Minimum Budget (USD)
                </label>
                {isEditing ? (
                  <input
                    type="number"
                    value={userPreferences.budget_min}
                    onChange={(e) => updatePreferences('budget_min', parseInt(e.target.value) || 0)}
                    min="0"
                    step="100"
                    className="input-field"
                  />
                ) : (
                  <div className="p-3 bg-gray-50 rounded-lg border">
                    ${userPreferences.budget_min.toLocaleString()}
                  </div>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Maximum Budget (USD)
                </label>
                {isEditing ? (
                  <input
                    type="number"
                    value={userPreferences.budget_max}
                    onChange={(e) => updatePreferences('budget_max', parseInt(e.target.value) || 0)}
                    min="0"
                    step="100"
                    className="input-field"
                  />
                ) : (
                  <div className="p-3 bg-gray-50 rounded-lg border">
                    ${userPreferences.budget_max.toLocaleString()}
                  </div>
                )}
              </div>
            </div>

            {/* Trip Duration */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Preferred Trip Duration (days)
              </label>
              {isEditing ? (
                <input
                  type="number"
                  value={userPreferences.trip_duration}
                  onChange={(e) => updatePreferences('trip_duration', parseInt(e.target.value) || 1)}
                  min="1"
                  max="30"
                  className="input-field"
                />
              ) : (
                <div className="p-3 bg-gray-50 rounded-lg border">
                  {userPreferences.trip_duration} days
                </div>
              )}
            </div>

            {/* Travel Style and Pace */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Travel Style
                </label>
                {isEditing ? (
                  <select
                    value={userPreferences.travel_style}
                    onChange={(e) => updatePreferences('travel_style', e.target.value)}
                    className="input-field"
                  >
                    <option value="budget">Budget</option>
                    <option value="balanced">Balanced</option>
                    <option value="luxury">Luxury</option>
                  </select>
                ) : (
                  <div className="p-3 bg-gray-50 rounded-lg border capitalize">
                    {userPreferences.travel_style}
                  </div>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Trip Pace
                </label>
                {isEditing ? (
                  <select
                    value={userPreferences.pace}
                    onChange={(e) => updatePreferences('pace', e.target.value)}
                    className="input-field"
                  >
                    <option value="chill">Chill</option>
                    <option value="balanced">Balanced</option>
                    <option value="fast">Fast-paced</option>
                  </select>
                ) : (
                  <div className="p-3 bg-gray-50 rounded-lg border capitalize">
                    {userPreferences.pace === 'fast' ? 'Fast-paced' : userPreferences.pace}
                  </div>
                )}
              </div>
            </div>

            {/* Accommodation and Room Sharing */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Accommodation Preference
                </label>
                {isEditing ? (
                  <select
                    value={userPreferences.accommodation_preference}
                    onChange={(e) => updatePreferences('accommodation_preference', e.target.value)}
                    className="input-field"
                  >
                    <option value="budget">Budget</option>
                    <option value="standard">Standard</option>
                    <option value="luxury">Luxury</option>
                  </select>
                ) : (
                  <div className="p-3 bg-gray-50 rounded-lg border capitalize">
                    {userPreferences.accommodation_preference}
                  </div>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Room Sharing Preference
                </label>
                {isEditing ? (
                  <select
                    value={userPreferences.room_sharing}
                    onChange={(e) => updatePreferences('room_sharing', e.target.value)}
                    className="input-field"
                  >
                    <option value="private">Private room</option>
                    <option value="share">Share room</option>
                    <option value="any">Any</option>
                  </select>
                ) : (
                  <div className="p-3 bg-gray-50 rounded-lg border">
                    {userPreferences.room_sharing === 'private' ? 'Private room' :
                     userPreferences.room_sharing === 'share' ? 'Share room' : 'Any'}
                  </div>
                )}
              </div>
            </div>

            {/* Availability Dates */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Available Dates * <span className="text-gray-500">({userPreferences.availability_dates.length} dates selected)</span>
              </label>
              {isEditing ? (
                <div className="max-h-48 overflow-y-auto border border-gray-200 rounded-lg p-4">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {availableDates.map((date) => (
                      <button
                        key={date}
                        onClick={() => toggleArrayValue('availability_dates', date)}
                        className={`p-2 rounded border text-sm transition-all ${
                          userPreferences.availability_dates.includes(date)
                            ? 'border-primary-600 bg-primary-50 text-primary-700'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        {new Date(date).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric'
                        })}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="p-3 bg-gray-50 rounded-lg border">
                  {userPreferences.availability_dates.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {userPreferences.availability_dates.slice(0, 5).map((date) => (
                        <span key={date} className="px-2 py-1 bg-primary-100 text-primary-700 rounded text-sm">
                          {new Date(date).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric'
                          })}
                        </span>
                      ))}
                      {userPreferences.availability_dates.length > 5 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-sm">
                          +{userPreferences.availability_dates.length - 5} more
                        </span>
                      )}
                    </div>
                  ) : (
                    'No dates selected'
                  )}
                </div>
              )}
            </div>

            {/* Dietary Restrictions */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Dietary Restrictions <span className="text-gray-500">(Optional)</span>
              </label>
              {isEditing ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {dietaryOptions.map((restriction) => (
                    <button
                      key={restriction}
                      onClick={() => toggleArrayValue('dietary_restrictions', restriction)}
                      className={`p-3 rounded-lg border text-sm transition-all ${
                        userPreferences.dietary_restrictions.includes(restriction)
                          ? 'border-primary-600 bg-primary-50 text-primary-700'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      {restriction}
                    </button>
                  ))}
                </div>
              ) : (
                <div className="p-3 bg-gray-50 rounded-lg border">
                  {userPreferences.dietary_restrictions.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {userPreferences.dietary_restrictions.map((restriction) => (
                        <span key={restriction} className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-sm">
                          {restriction}
                        </span>
                      ))}
                    </div>
                  ) : (
                    'None specified'
                  )}
                </div>
              )}
            </div>

            {/* Additional Info */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Additional Information <span className="text-gray-500">(Optional)</span>
              </label>
              {isEditing ? (
                <textarea
                  value={userPreferences.additional_info}
                  onChange={(e) => updatePreferences('additional_info', e.target.value)}
                  placeholder="Any other preferences or requirements..."
                  rows={3}
                  className="input-field"
                />
              ) : (
                <div className="p-3 bg-gray-50 rounded-lg border min-h-[80px]">
                  {userPreferences.additional_info || 'No additional information provided'}
                </div>
              )}
            </div>

            {/* Error Message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center space-x-2 p-4 bg-red-50 border border-red-200 rounded-lg"
              >
                <AlertCircle className="h-5 w-5 text-red-600" />
                <span className="text-red-700 text-sm">{error}</span>
              </motion.div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center justify-between pt-6 border-t border-gray-200">
              <button
                onClick={() => navigate(`/trip/${groupCode}`)}
                className="btn-secondary flex items-center space-x-2"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Back to Trip</span>
              </button>

              {isEditing && (
                <button
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Saving...</span>
                    </>
                  ) : (
                    <>
                      <span>Save Preferences</span>
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
} 