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
  Clock
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

export function TripPreferences() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const { groupCode } = useParams<{ groupCode: string }>()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [redirectCountdown, setRedirectCountdown] = useState<number | null>(null)
  
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

  const addDateRange = (startDate: string, endDate: string) => {
    const start = new Date(startDate)
    const end = new Date(endDate)
    const newDates: string[] = []
    const currentDates = userPreferences.availability_dates

    // Generate all dates in range
    const current = new Date(start)
    while (current <= end) {
      const dateString = current.toISOString().split('T')[0]
      if (!currentDates.includes(dateString)) {
        newDates.push(dateString)
      }
      current.setDate(current.getDate() + 1)
    }

    // Add all new dates at once
    if (newDates.length > 0) {
      updatePreferences('availability_dates', [...currentDates, ...newDates])
    }
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
      
      // Create comprehensive user input data
      const userInput = {
        name: user.fullName,
        email: user.email,
        phone: userPreferences.phone,
        role: 'creator',
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
        
        // Only auto-redirect in production, not development
        const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        
        if (!isDevelopment) {
          // Start countdown
          setRedirectCountdown(3)
          
          // Countdown timer
          const countdownInterval = setInterval(() => {
            setRedirectCountdown(prev => {
              if (prev && prev > 1) {
                return prev - 1
              } else {
                clearInterval(countdownInterval)
                navigate(`/trip/${groupCode}`)
                return null
              }
            })
          }, 1000)
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
            
            <p className="text-gray-600 mb-2">
              Your trip preferences have been saved successfully.
            </p>
            
            {redirectCountdown !== null ? (
              <div className="mb-6">
                <p className="text-sm text-gray-500 mb-2">
                  Now your group can see your preferences and start planning!
                </p>
                <div className="flex items-center justify-center space-x-2 text-primary-600">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm font-medium">
                    Redirecting to trip details in {redirectCountdown}...
                  </span>
                </div>
              </div>
            ) : (
              <div className="mb-6">
                <p className="text-sm text-gray-500 mb-2">
                  Now your group can see your preferences and start planning!
                </p>
                {(window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && (
                  <div className="text-xs text-orange-600 bg-orange-50 border border-orange-200 rounded p-2">
                    💡 Auto-redirect disabled in development mode for console debugging
                  </div>
                )}
              </div>
            )}
            
            <div className="space-y-3">
              <button
                onClick={() => navigate(`/trip/${groupCode}`)}
                className="btn-primary w-full"
              >
                View Trip Details
              </button>
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
            Add Your Preferences
          </h1>
          <p className="text-gray-600">
            Tell us about your travel preferences to help plan the perfect trip
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="card space-y-8"
        >
          {/* Phone Number */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Phone Number *
            </label>
            <input
              type="tel"
              value={userPreferences.phone}
              onChange={(e) => updatePreferences('phone', e.target.value)}
              placeholder="Your phone number"
              className="input-field"
              required
            />
          </div>

          {/* Travel Vibe */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              What's your travel vibe? * <span className="text-gray-500">(Select all that apply)</span>
            </label>
            <div className="grid grid-cols-2 gap-3">
              {vibeOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => toggleArrayValue('vibe', option.value)}
                  className={`p-4 rounded-lg border-2 transition-all flex items-center space-x-3 ${
                    userPreferences.vibe.includes(option.value)
                      ? 'border-primary-600 bg-primary-50 text-primary-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <option.icon className="h-5 w-5" />
                  <span className="font-medium">{option.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Interests */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              What interests you most? * <span className="text-gray-500">(Select all that apply)</span>
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {interestOptions.map((interest) => (
                <button
                  key={interest}
                  onClick={() => toggleArrayValue('interests', interest)}
                  className={`p-3 rounded-lg border text-sm transition-all ${
                    userPreferences.interests.includes(interest)
                      ? 'border-primary-600 bg-primary-50 text-primary-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {interest}
                </button>
              ))}
            </div>
          </div>

          {/* Departure Airports */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Departure Airports * <span className="text-gray-500">(Select your preferred airports)</span>
            </label>
            <div className="grid grid-cols-4 md:grid-cols-8 gap-2">
              {airportOptions.map((airport) => (
                <button
                  key={airport}
                  onClick={() => toggleArrayValue('departure_airports', airport)}
                  className={`p-3 rounded-lg border text-sm font-mono transition-all ${
                    userPreferences.departure_airports.includes(airport)
                      ? 'border-primary-600 bg-primary-50 text-primary-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {airport}
                </button>
              ))}
            </div>
          </div>

          {/* Budget Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Budget (USD)
              </label>
              <input
                type="number"
                value={userPreferences.budget_min}
                onChange={(e) => updatePreferences('budget_min', parseInt(e.target.value) || 0)}
                min="0"
                step="100"
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Maximum Budget (USD)
              </label>
              <input
                type="number"
                value={userPreferences.budget_max}
                onChange={(e) => updatePreferences('budget_max', parseInt(e.target.value) || 0)}
                min="0"
                step="100"
                className="input-field"
              />
            </div>
          </div>

          {/* Trip Duration */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Preferred Trip Duration (days)
            </label>
            <input
              type="number"
              value={userPreferences.trip_duration}
              onChange={(e) => updatePreferences('trip_duration', parseInt(e.target.value) || 1)}
              min="1"
              max="30"
              className="input-field"
            />
          </div>

          {/* Travel Style and Pace */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Travel Style
              </label>
              <select
                value={userPreferences.travel_style}
                onChange={(e) => updatePreferences('travel_style', e.target.value)}
                className="input-field"
              >
                <option value="budget">Budget</option>
                <option value="balanced">Balanced</option>
                <option value="luxury">Luxury</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Trip Pace
              </label>
              <select
                value={userPreferences.pace}
                onChange={(e) => updatePreferences('pace', e.target.value)}
                className="input-field"
              >
                <option value="chill">Chill</option>
                <option value="balanced">Balanced</option>
                <option value="fast">Fast-paced</option>
              </select>
            </div>
          </div>

          {/* Accommodation and Room Sharing */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Accommodation Preference
              </label>
              <select
                value={userPreferences.accommodation_preference}
                onChange={(e) => updatePreferences('accommodation_preference', e.target.value)}
                className="input-field"
              >
                <option value="budget">Budget</option>
                <option value="standard">Standard</option>
                <option value="luxury">Luxury</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Room Sharing Preference
              </label>
              <select
                value={userPreferences.room_sharing}
                onChange={(e) => updatePreferences('room_sharing', e.target.value)}
                className="input-field"
              >
                <option value="private">Private room</option>
                <option value="share">Share room</option>
                <option value="any">Any</option>
              </select>
            </div>
          </div>

          {/* Availability Dates */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Available Dates * <span className="text-gray-500">(Select all dates you're available)</span>
            </label>
            
            <div className="space-y-6">
              {/* Date Range Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">Add Date Range</label>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <input
                      type="date"
                      id="start-date-prefs"
                      className="input-field"
                      min={new Date().toISOString().split('T')[0]}
                      placeholder="From"
                    />
                    <label htmlFor="start-date-prefs" className="block text-xs text-gray-500 mt-1">From</label>
                  </div>
                  <div>
                    <input
                      type="date"
                      id="end-date-prefs"
                      className="input-field"
                      min={new Date().toISOString().split('T')[0]}
                      placeholder="To"
                    />
                    <label htmlFor="end-date-prefs" className="block text-xs text-gray-500 mt-1">To</label>
                  </div>
                </div>
                <button
                  onClick={() => {
                    const startInput = document.getElementById('start-date-prefs') as HTMLInputElement
                    const endInput = document.getElementById('end-date-prefs') as HTMLInputElement
                    if (startInput.value && endInput.value) {
                      addDateRange(startInput.value, endInput.value)
                      startInput.value = ''
                      endInput.value = ''
                    }
                  }}
                  className="btn-secondary mt-3"
                >
                  Add Date Range
                </button>
              </div>

              {/* Single Date Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">Add Single Date</label>
                <input
                  type="date"
                  onChange={(e) => {
                    if (e.target.value && !userPreferences.availability_dates.includes(e.target.value)) {
                      updatePreferences('availability_dates', [...userPreferences.availability_dates, e.target.value])
                      e.target.value = '' // Clear the input
                    }
                  }}
                  className="input-field max-w-xs"
                  min={new Date().toISOString().split('T')[0]}
                />
              </div>

              {/* Selected Dates Summary */}
              {userPreferences.availability_dates.length > 0 && (
                <div className="border-t pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-medium text-gray-700">
                      Selected: {userPreferences.availability_dates.length} dates
                    </p>
                    <button
                      onClick={() => updatePreferences('availability_dates', [])}
                      className="text-sm text-red-600 hover:text-red-800"
                    >
                      Clear All
                    </button>
                  </div>
                  
                  <div className="max-h-24 overflow-y-auto">
                    <div className="flex flex-wrap gap-1">
                      {userPreferences.availability_dates
                        .sort((a, b) => new Date(a).getTime() - new Date(b).getTime())
                        .map((date, index) => (
                        <span 
                          key={index} 
                          className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                        >
                          {new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                          <button
                            onClick={() => {
                              const newDates = userPreferences.availability_dates.filter((_, i) => i !== index)
                              updatePreferences('availability_dates', newDates)
                            }}
                            className="text-gray-500 hover:text-red-600 ml-1"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Dietary Restrictions */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Dietary Restrictions <span className="text-gray-500">(Optional)</span>
            </label>
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
          </div>

          {/* Additional Info */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Additional Information <span className="text-gray-500">(Optional)</span>
            </label>
            <textarea
              value={userPreferences.additional_info}
              onChange={(e) => updatePreferences('additional_info', e.target.value)}
              placeholder="Any other preferences or requirements..."
              rows={3}
              className="input-field"
            />
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

          {/* Submit Button */}
          <div className="flex items-center justify-between pt-6 border-t border-gray-200">
            <button
              onClick={() => navigate('/dashboard')}
              className="btn-secondary flex items-center space-x-2"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Skip for Now</span>
            </button>

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
          </div>
        </motion.div>
      </div>
    </div>
  )
} 