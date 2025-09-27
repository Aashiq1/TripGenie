import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  Users,
  Loader2,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  MapPin,
  Calendar,
  DollarSign,
  User as UserIcon,
  Clock,
  Search,
  Coffee,
  Zap,
  Heart
} from 'lucide-react'
import { useAuthStore } from '../stores/authStore'

interface TripPreview {
  groupCode: string
  tripName: string
  destination: string
  departureDate: string
  returnDate: string
  budget: string
  memberCount: number
  creatorName: string
  accommodation: string
  description?: string
  status: 'planning' | 'planned' | 'completed'
}

interface JoinData {
  phone: string
}

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

export function JoinTrip() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(0) // 0: Search, 1: Preview, 2: Preferences, 3: Success
  const [groupCode, setGroupCode] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [isJoining, setIsJoining] = useState(false)
  const [tripPreview, setTripPreview] = useState<TripPreview | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [joinSuccess, setJoinSuccess] = useState(false)
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

  const handleSearch = async () => {
    if (!groupCode.trim()) {
      setError('Please enter a group code')
      return
    }

    setIsSearching(true)
    setError(null)
    
    try {
      const { tripAPI } = await import('../services/api')
      const result = await tripAPI.getTripPreview(groupCode)
      
      if (result && result.groupCode) {
        setTripPreview(result)
        setCurrentStep(1)
      } else {
        setError('Trip not found. Please check the group code and try again.')
      }
    } catch (error: any) {
      if (error.response?.status === 404) {
        setError('Trip not found. Please check the group code and try again.')
      } else if (error.response?.status === 403) {
        setError('You are not authorized to view this trip.')
      } else {
        console.error('Failed to find trip:', error)
        setError('Failed to find trip. Please try again.')
      }
    } finally {
      setIsSearching(false)
    }
  }

  const handleJoin = async () => {
    if (!tripPreview || !user) return

    // Comprehensive validation
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

    setIsJoining(true)
    try {
      const { tripAPI } = await import('../services/api')
      
      // Create comprehensive user input data
      const userInput = {
        name: user.fullName,
        email: user.email,
        phone: userPreferences.phone,
        role: 'member',
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

      const result = await tripAPI.joinTrip(tripPreview.groupCode, userInput)
      
      if (result.success) {
        if (result.requires_replan) {
          // If this edit impacts planning, inform the user right away
          console.warn('Preferences changed require re-planning')
        }
        // Show brief success state
        setJoinSuccess(true)
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
                navigate(`/trip/${tripPreview.groupCode}`)
                return null
              }
            })
          }, 1000)
        }
      } else {
        setError(result.message || 'Failed to join trip')
      }
    } catch (error: any) {
      console.error('Failed to join trip:', error)
      setError('Failed to join trip. Please try again.')
    } finally {
      setIsJoining(false)
    }
  }

  const handlePreferencesNext = () => {
    // Basic validation before proceeding
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

    setError(null)
    setCurrentStep(3)
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Not specified'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'planning':
        return 'bg-yellow-100 text-yellow-800'
      case 'planned':
        return 'bg-green-100 text-green-800'
      case 'completed':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  // Success state
  if (joinSuccess) {
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
              Successfully Joined! 🎉
            </h1>
            
            <p className="text-gray-600 mb-2">
              You've joined <strong>{tripPreview?.tripName}</strong>
            </p>
            
            {redirectCountdown !== null ? (
              <div className="mb-6">
                <p className="text-sm text-gray-500 mb-2">
                  You'll receive updates and can participate in planning decisions.
                </p>
                <div className="flex items-center justify-center space-x-2 text-primary-600">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm font-medium">
                    Redirecting to trip details in {redirectCountdown}...
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-500 mb-6">
                You'll receive updates and can participate in planning decisions.
              </p>
            )}
            
            <div className="space-y-3">
              <button
                onClick={() => navigate(`/trip/${tripPreview?.groupCode}`)}
                className="btn-primary w-full"
              >
                View Trip Details
              </button>
              
              <button
                onClick={() => navigate('/dashboard')}
                className="btn-secondary w-full"
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    )
  }

  // Step 0: Search
  if (currentStep === 0) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-8"
          >
            <div className="bg-secondary-600 p-4 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
              <Users className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Join a Trip
            </h1>
            <p className="text-gray-600">
              Enter a group code to join an existing trip
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="card mb-8"
          >
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Group Code
              </label>
              <div className="flex space-x-3">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={groupCode}
                    onChange={(e) => {
                      setGroupCode(e.target.value.toUpperCase())
                      setError(null)
                      setTripPreview(null)
                    }}
                    placeholder="Enter group code (e.g., DEMO123)"
                    className="input-field pr-10"
                    maxLength={15}
                  />
                  <Search className="absolute right-3 top-3 h-5 w-5 text-gray-400" />
                </div>
                <button
                  onClick={handleSearch}
                  disabled={isSearching || !groupCode.trim()}
                  className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSearching ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Searching...</span>
                    </>
                  ) : (
                    <>
                      <Search className="h-4 w-4" />
                      <span>Find Trip</span>
                    </>
                  )}
                </button>
              </div>
            </div>

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

            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800 mb-2">
                <strong>Don't have a group code?</strong>
              </p>
              <p className="text-sm text-blue-700">
                Ask your trip organizer to share the group code with you, or try the demo code: <strong>DEMO123</strong>
              </p>
            </div>
          </motion.div>
        </div>
      </div>
    )
  }

  // Step 1: Trip Preview
  if (currentStep === 1) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-8"
          >
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Trip Preview
            </h1>
            <p className="text-gray-600">
              Review the trip details before joining
            </p>
          </motion.div>

          {tripPreview && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="card mb-8"
            >
              <div className="space-y-6">
                {/* Trip Header */}
                <div className="text-center">
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    {tripPreview.tripName}
                  </h2>
                  <div className="flex items-center justify-center space-x-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(tripPreview.status)}`}>
                      {tripPreview.status}
                    </span>
                  </div>
                </div>

                {/* Trip Details Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="flex items-center space-x-3">
                      <MapPin className="h-5 w-5 text-primary-600" />
                      <div>
                        <p className="text-sm text-gray-500">Destination</p>
                        <p className="font-medium text-gray-900">{tripPreview.destination}</p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3">
                      <Calendar className="h-5 w-5 text-primary-600" />
                      <div>
                        <p className="text-sm text-gray-500">Dates</p>
                        <p className="font-medium text-gray-900">
                          {formatDate(tripPreview.departureDate)} - {formatDate(tripPreview.returnDate)}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center space-x-3">
                      <DollarSign className="h-5 w-5 text-primary-600" />
                      <div>
                        <p className="text-sm text-gray-500">Budget</p>
                        <p className="font-medium text-gray-900">${tripPreview.budget} per person</p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3">
                      <div className="h-10 w-10 rounded-full bg-primary-600 flex items-center justify-center">
                        <UserIcon className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Trip Creator</p>
                        <p className="font-medium text-gray-900">{tripPreview.creatorName}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {tripPreview.description && (
                  <div>
                    <p className="text-sm text-gray-500 mb-2">Description</p>
                    <p className="text-gray-700">{tripPreview.description}</p>
                  </div>
                )}

                <div className="border-t pt-6">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">Current Members</span>
                    <span className="font-medium text-gray-900">{tripPreview.memberCount} members</span>
                  </div>
                </div>
              </div>

              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => setCurrentStep(0)}
                  className="btn-secondary flex-1"
                >
                  Back to Search
                </button>
                <button
                  onClick={() => setCurrentStep(2)}
                  className="btn-primary flex-1 flex items-center justify-center space-x-2"
                >
                  <span>Continue to Preferences</span>
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </motion.div>
          )}

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
        </div>
      </div>
    )
  }

  // Step 2: Preferences
  if (currentStep === 2) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-8"
          >
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Join {tripPreview?.tripName}
            </h1>
            <p className="text-gray-600">
              Tell us about your preferences and availability to join the trip
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="card"
          >
            <div className="space-y-8">
              {/* Contact Information */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h3>
                <div className="max-w-md">
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
              </div>

              {/* Travel Preferences */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Travel Preferences</h3>
                <div className="space-y-6">

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                      What's your travel vibe? *
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      {vibeOptions.map((option) => (
                        <button
                          key={option.value}
                          onClick={() => toggleArrayValue('vibe', option.value)}
                          className={`flex items-center space-x-3 px-4 py-3 rounded-lg border-2 transition-all ${
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

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                      What interests you most? *
                    </label>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {interestOptions.map((interest) => (
                        <button
                          key={interest}
                          onClick={() => toggleArrayValue('interests', interest)}
                          className={`px-3 py-2 rounded-lg border text-sm font-medium transition-all ${
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

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                      Departure Airports *
                    </label>
                    <div className="grid grid-cols-4 md:grid-cols-8 gap-2">
                      {airportOptions.map((airport) => (
                        <button
                          key={airport}
                          onClick={() => toggleArrayValue('departure_airports', airport)}
                          className={`px-3 py-2 rounded-lg border text-sm font-mono font-medium transition-all ${
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

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Budget Range (USD) *
                      </label>
                      <div className="flex items-center space-x-3">
                        <input
                          type="number"
                          value={userPreferences.budget_min}
                          onChange={(e) => updatePreferences('budget_min', parseInt(e.target.value) || 0)}
                          className="input-field"
                          min="0"
                          placeholder="Min"
                        />
                        <span className="text-gray-500">–</span>
                        <input
                          type="number"
                          value={userPreferences.budget_max}
                          onChange={(e) => updatePreferences('budget_max', parseInt(e.target.value) || 0)}
                          className="input-field"
                          min="0"
                          placeholder="Max"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Trip Duration (days) *
                      </label>
                      <input
                        type="number"
                        value={userPreferences.trip_duration}
                        onChange={(e) => updatePreferences('trip_duration', parseInt(e.target.value) || 0)}
                        className="input-field"
                        min="1"
                        placeholder="Days"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Travel Style
                      </label>
                      <select
                        value={userPreferences.travel_style}
                        onChange={(e) => updatePreferences('travel_style', e.target.value as 'budget' | 'balanced' | 'luxury')}
                        className="input-field"
                      >
                        <option value="budget">Budget</option>
                        <option value="balanced">Balanced</option>
                        <option value="luxury">Luxury</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Trip Pace
                      </label>
                      <select
                        value={userPreferences.pace}
                        onChange={(e) => updatePreferences('pace', e.target.value as 'chill' | 'balanced' | 'fast')}
                        className="input-field"
                      >
                        <option value="chill">Chill</option>
                        <option value="balanced">Balanced</option>
                        <option value="fast">Fast</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Accommodation
                      </label>
                      <select
                        value={userPreferences.accommodation_preference}
                        onChange={(e) => updatePreferences('accommodation_preference', e.target.value as 'budget' | 'standard' | 'luxury')}
                        className="input-field"
                      >
                        <option value="budget">Budget</option>
                        <option value="standard">Standard</option>
                        <option value="luxury">Luxury</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Room Sharing
                      </label>
                      <select
                        value={userPreferences.room_sharing}
                        onChange={(e) => updatePreferences('room_sharing', e.target.value as 'private' | 'share' | 'any')}
                        className="input-field"
                      >
                        <option value="private">Private Room</option>
                        <option value="share">Share Room</option>
                        <option value="any">Any</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                      Dietary Restrictions (Optional)
                    </label>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      {dietaryOptions.map((diet) => (
                        <button
                          key={diet}
                          onClick={() => toggleArrayValue('dietary_restrictions', diet)}
                          className={`px-3 py-2 rounded-lg border text-sm font-medium transition-all ${
                            userPreferences.dietary_restrictions.includes(diet)
                              ? 'border-primary-600 bg-primary-50 text-primary-700'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          {diet}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Additional Information (Optional)
                    </label>
                    <textarea
                      value={userPreferences.additional_info}
                      onChange={(e) => updatePreferences('additional_info', e.target.value)}
                      placeholder="Any other preferences or requirements..."
                      rows={3}
                      className="input-field"
                    />
                  </div>
                </div>
              </div>

              {/* Availability */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Availability *</h3>
                <p className="text-sm text-gray-600 mb-6">Select all dates when you're available to travel. You can add individual dates or date ranges.</p>
                
                <div className="space-y-6">
                  {/* Date Range Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">Add Date Range</label>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <input
                          type="date"
                          id="start-date"
                          className="input-field"
                          min={new Date().toISOString().split('T')[0]}
                          placeholder="From"
                        />
                        <label htmlFor="start-date" className="block text-xs text-gray-500 mt-1">From</label>
                      </div>
                      <div>
                        <input
                          type="date"
                          id="end-date"
                          className="input-field"
                          min={new Date().toISOString().split('T')[0]}
                          placeholder="To"
                        />
                        <label htmlFor="end-date" className="block text-xs text-gray-500 mt-1">To</label>
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        const startInput = document.getElementById('start-date') as HTMLInputElement
                        const endInput = document.getElementById('end-date') as HTMLInputElement
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

              <div className="flex space-x-3">
                <button
                  onClick={() => setCurrentStep(1)}
                  className="btn-secondary flex-1"
                >
                  Back
                </button>
                <button
                  onClick={handlePreferencesNext}
                  className="btn-primary flex-1 flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span>Next</span>
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    )
  }

  // Step 3: Review and Join
  if (currentStep === 3) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-8"
          >
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Review & Join {tripPreview?.tripName}
            </h1>
            <p className="text-gray-600">
              Review your preferences and confirm to join the trip
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="card"
          >
            <div className="space-y-6">
              {/* Trip Summary */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Trip Summary</h4>
                <div className="text-sm text-gray-600 space-y-1">
                  <p><strong>Destination:</strong> {tripPreview?.destination}</p>
                  <p><strong>Dates:</strong> {formatDate(tripPreview?.departureDate || '')} - {formatDate(tripPreview?.returnDate || '')}</p>
                  <p><strong>Budget:</strong> ${tripPreview?.budget} per person</p>
                  <p><strong>Creator:</strong> {tripPreview?.creatorName}</p>
                </div>
              </div>

              {/* Your Preferences Summary */}
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Your Preferences</h4>
                <div className="text-sm text-gray-600 space-y-1">
                  <p><strong>Phone:</strong> {userPreferences.phone}</p>
                  <p><strong>Vibe:</strong> {userPreferences.vibe.join(', ')}</p>
                  <p><strong>Interests:</strong> {userPreferences.interests.join(', ')}</p>
                  <p><strong>Departure Airports:</strong> {userPreferences.departure_airports.join(', ')}</p>
                  <p><strong>Budget:</strong> ${userPreferences.budget_min} - ${userPreferences.budget_max}</p>
                  <p><strong>Trip Duration:</strong> {userPreferences.trip_duration} days</p>
                  <p><strong>Travel Style:</strong> {userPreferences.travel_style}</p>
                  <p><strong>Pace:</strong> {userPreferences.pace}</p>
                  {userPreferences.dietary_restrictions.length > 0 && (
                    <p><strong>Dietary Restrictions:</strong> {userPreferences.dietary_restrictions.join(', ')}</p>
                  )}
                  {userPreferences.additional_info && (
                    <p><strong>Additional Info:</strong> {userPreferences.additional_info}</p>
                  )}
                </div>
              </div>

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

              <div className="flex space-x-3">
                <button
                  onClick={() => setCurrentStep(2)}
                  className="btn-secondary flex-1"
                >
                  Back to Preferences
                </button>
                <button
                  onClick={handleJoin}
                  disabled={isJoining}
                  className="btn-primary flex-1 flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isJoining ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Joining...</span>
                    </>
                  ) : (
                    <span>Join Trip</span>
                  )}
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    )
  }

  return null
} 