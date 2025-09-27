import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Search, 
  MapPin, 
  Star, 
  Clock, 
  DollarSign, 
  ExternalLink,
  Filter,
  Loader2,
  X,
  Plus,
  Check
} from 'lucide-react'
import { activityAPI } from '../services/api'

interface Activity {
  name: string
  description: string
  interest: string
  activity_type: string
  location: {
    address: string
    lat?: number
    lng?: number
  }
  is_free: boolean
  price_info: {
    price_level: string
    amount_usd?: number
  }
  rating?: number
  user_ratings_total?: number
  photos?: string[]
  website?: string
  phone?: string
  opening_hours?: {
    open_now?: boolean
    weekday_text?: string[]
  }
  duration?: number
  google_place_id: string
  source: string
}

interface ActivitySearchResponse {
  destination: string
  interests: string[]
  travel_style: string
  total_found: number
  activities: Activity[]
}

interface ActivitySearchProps {
  destination?: string
  onActivitySelect?: (activity: Activity) => void
  className?: string
}

export function ActivitySearch({ destination = '', onActivitySelect, className = '' }: ActivitySearchProps) {
  const [searchDestination, setSearchDestination] = useState(destination)
  const [selectedInterests, setSelectedInterests] = useState<string[]>([])
  const [travelStyle, setTravelStyle] = useState('balanced')
  const [isSearching, setIsSearching] = useState(false)
  const [results, setResults] = useState<ActivitySearchResponse | null>(null)
  const [availableInterests, setAvailableInterests] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  // Load available interests on component mount, and auto-select a few + auto-search
  useEffect(() => {
    const loadInterests = async () => {
      try {
        const response = await activityAPI.getAvailableInterests()
        const interests = response.available_interests || []
        setAvailableInterests(interests)
        // If none selected yet, pick up to 3 defaults to ensure results render
        if (interests.length > 0 && selectedInterests.length === 0) {
          const defaults = interests.slice(0, Math.min(3, interests.length))
          setSelectedInterests(defaults)
          // Trigger an initial search if we have a destination
          if ((destination || searchDestination).trim()) {
            setTimeout(() => {
              handleSearch()
            }, 0)
          }
        }
      } catch (error) {
        console.error('Failed to load interests:', error)
      }
    }
    loadInterests()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSearch = async () => {
    if (!searchDestination.trim()) {
      setError('Please enter a destination')
      return
    }

    if (selectedInterests.length === 0) {
      setError('Please select at least one interest')
      return
    }

    setIsSearching(true)
    setError(null)

    try {
      const response = await activityAPI.searchActivities(
        searchDestination,
        selectedInterests,
        travelStyle
      )
      setResults(response)
    } catch (error: any) {
      console.error('Search failed:', error)
      setError(error.response?.data?.detail || 'Failed to search activities')
    } finally {
      setIsSearching(false)
    }
  }

  const toggleInterest = (interest: string) => {
    setSelectedInterests(prev => 
      prev.includes(interest) 
        ? prev.filter(i => i !== interest)
        : [...prev, interest]
    )
  }

  const getPriceDisplay = (activity: Activity) => {
    if (activity.is_free) {
      return <span className="text-green-600 font-medium">Free</span>
    }
    return <span className="text-gray-600">{activity.price_info.price_level}</span>
  }

  const getStatusDisplay = (activity: Activity) => {
    if (activity.opening_hours?.open_now !== undefined) {
      return activity.opening_hours.open_now ? (
        <span className="text-green-600 text-sm">🟢 Open</span>
      ) : (
        <span className="text-red-600 text-sm">🔴 Closed</span>
      )
    }
    return null
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-gray-900">
          🎯 Activity Search
        </h3>
      </div>

      {/* Search Form */}
      <div className="space-y-4 mb-6">
        {/* Destination Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Destination
          </label>
          <div className="relative">
            <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={searchDestination}
              onChange={(e) => setSearchDestination(e.target.value)}
              placeholder="Enter city name (e.g., Barcelona, Paris)"
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Interests Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Interests ({selectedInterests.length} selected)
          </label>
          <div className="flex flex-wrap gap-2">
            {availableInterests.map((interest) => (
              <button
                key={interest}
                onClick={() => toggleInterest(interest)}
                className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                  selectedInterests.includes(interest)
                    ? 'bg-blue-500 text-white border-blue-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-blue-500'
                }`}
              >
                {selectedInterests.includes(interest) && <Check className="inline h-3 w-3 mr-1" />}
                {interest}
              </button>
            ))}
          </div>
        </div>

        {/* Search Button */}
        <button
          onClick={handleSearch}
          disabled={isSearching || !searchDestination.trim() || selectedInterests.length === 0}
          className="w-full flex items-center justify-center gap-2 bg-blue-500 text-white px-4 py-3 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {isSearching ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Search className="h-4 w-4" />
          )}
          {isSearching ? 'Searching...' : 'Search Activities'}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Results */}
      {results && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-lg font-medium text-gray-900">
              Found {results.total_found} activities in {results.destination}
            </h4>
            <div className="text-sm text-gray-500">
              {results.interests.join(', ')} • {results.travel_style}
            </div>
          </div>

          <div className="space-y-4 max-h-96 overflow-y-auto">
            {results.activities.map((activity, index) => (
              <motion.div
                key={`${activity.google_place_id}-${index}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start mb-2">
                  <h5 className="font-semibold text-gray-900">{activity.name}</h5>
                  {onActivitySelect && (
                    <button
                      onClick={() => onActivitySelect(activity)}
                      className="p-1 text-blue-500 hover:text-blue-700 transition-colors"
                      title="Add to itinerary"
                    >
                      <Plus className="h-4 w-4" />
                    </button>
                  )}
                </div>

                <p className="text-gray-600 text-sm mb-3">{activity.description}</p>

                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <MapPin className="h-3 w-3" />
                    {activity.location.address}
                  </div>

                  <div className="flex items-center gap-4 text-sm">
                    {activity.rating && (
                      <div className="flex items-center gap-1">
                        <Star className="h-3 w-3 text-yellow-500" />
                        <span>{activity.rating}</span>
                        {activity.user_ratings_total && (
                          <span className="text-gray-500">({activity.user_ratings_total})</span>
                        )}
                      </div>
                    )}

                    <div className="flex items-center gap-1">
                      <DollarSign className="h-3 w-3" />
                      {getPriceDisplay(activity)}
                    </div>

                    {activity.duration && (
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {activity.duration}h
                      </div>
                    )}

                    {getStatusDisplay(activity)}
                  </div>

                  {activity.website && (
                    <div className="pt-2">
                      <a
                        href={activity.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-blue-500 hover:text-blue-700 text-sm transition-colors"
                      >
                        <ExternalLink className="h-3 w-3" />
                        Visit Website
                      </a>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}