import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  MapPin, 
  Calendar, 
  Users, 
  DollarSign, 
  Settings, 
  Share2,
  Clock,
  Plane,
  Building,
  Activity,
  MessageCircle,
  CheckCircle,
  AlertCircle,
  User,
  Star,
  Edit3,
  Search
} from 'lucide-react'
import { useAuthStore } from '../stores/authStore'
import { ActivitySearch } from '../components/ActivitySearch'

interface TripMember {
  id: string
  name: string
  email: string
  role: 'creator' | 'member'
  joinedAt: string
  avatar?: string
}

interface ItineraryItem {
  id: string
  day: number
  date: string
  activities: {
    time: string
    title: string
    description: string
    type: 'flight' | 'accommodation' | 'activity' | 'meal'
    confirmed: boolean
  }[]
}

interface TripDetails {
  groupCode: string
  tripName: string
  destination: string
  departureDate: string
  returnDate: string
  budget: string
  accommodation: string
  description: string
  status: 'planning' | 'planned' | 'completed'
  createdAt: string
  members: TripMember[]
  itinerary: ItineraryItem[]
}

// Helper function to check if trip plan exists (support structured plans too)
function hasTripPlan(tripPlan: any): boolean {
  if (!tripPlan) return false
  if (tripPlan.agent_response) return true
  if (tripPlan.daily_itinerary) return true
  if (tripPlan.date_range || tripPlan.cost_optimization) return true
  return false
}

// Helper function to transform backend itinerary data to frontend format
function transformItineraryData(tripPlan: any): ItineraryItem[] {
  if (!tripPlan) return []
  
  try {
    let parsedData = null
    
    // Case 1: Data is already structured (newer format)
    if (tripPlan.daily_itinerary || (tripPlan.MAD && tripPlan.MAD.daily_itinerary)) {
      parsedData = tripPlan
    }
    // Case 2: Data is in agent_response as JSON string (older format)
    else if (tripPlan.agent_response) {
      const agentResponse = tripPlan.agent_response
      const jsonMatch = agentResponse.match(/\{[\s\S]*\}/)
      if (!jsonMatch) return []
      parsedData = JSON.parse(jsonMatch[0])
    }
    
    if (!parsedData) return []
    
    // Find the daily_itinerary data (could be nested under destination)
    let dailyItinerary = parsedData.daily_itinerary
    if (!dailyItinerary) {
      // Try to find it under destination keys (MAD, BCN, etc.)
      const destKeys = Object.keys(parsedData)
      for (const key of destKeys) {
        if (parsedData[key]?.daily_itinerary) {
          dailyItinerary = parsedData[key].daily_itinerary
          break
        }
      }
    }
    
    if (!dailyItinerary) {
      // Fallback: synthesize empty days from optimized dates if available
      const start = parsedData?.date_range?.start_date || parsedData?.cost_optimization?.departure_date
      const end = parsedData?.date_range?.end_date || parsedData?.cost_optimization?.return_date

      const parseDateLocal = (s: string) => {
        if (!s) return null as any
        // If string includes time, rely on native parser
        if (s.includes('T')) {
          const d = new Date(s)
          return isNaN(d.getTime()) ? null : d
        }
        const parts = s.split('-').map(p => parseInt(p, 10))
        if (parts.length === 3) {
          const d = new Date(parts[0], parts[1] - 1, parts[2])
          return isNaN(d.getTime()) ? null : d
        }
        const d = new Date(s)
        return isNaN(d.getTime()) ? null : d
      }
      const toYMD = (d: Date) => {
        const y = d.getFullYear()
        const m = String(d.getMonth() + 1).padStart(2, '0')
        const dd = String(d.getDate()).padStart(2, '0')
        return `${y}-${m}-${dd}`
      }

      if (start && end) {
        const startDate = parseDateLocal(start)
        const endDate = parseDateLocal(end)
        if (startDate && endDate) {
          const dayMs = 1000 * 60 * 60 * 24
          const days = Math.max(0, Math.ceil((endDate.getTime() - startDate.getTime()) / dayMs))
          const items: ItineraryItem[] = []
          for (let i = 0; i < days; i++) {
            const d = new Date(startDate)
            d.setDate(d.getDate() + i)
            items.push({
              id: `day_${i+1}`,
              day: i+1,
              // Use date-only string to avoid TZ shifts
              date: toYMD(d),
              activities: []
            })
          }
          return items
        }
      }
      return []
    }
    
    // Transform to frontend format
    const itineraryItems: ItineraryItem[] = []
    
    Object.keys(dailyItinerary).forEach(dayKey => {
      if (dayKey.startsWith('day_') && dailyItinerary[dayKey].activities) {
        const dayData = dailyItinerary[dayKey]
        const dayNumber = dayData.day_number || parseInt(dayKey.replace('day_', ''))
        
        const activities = dayData.activities?.map((activity: any) => ({
          time: '09:00', // Default time since backend doesn't provide specific times
          title: activity.name || 'Activity',
          description: activity.description || `${activity.interest_category || ''} ${activity.activity_type || ''}`.trim(),
          type: 'activity' as const,
          confirmed: !!activity.booking_info // Consider it confirmed if it has booking info
        })) || []
        
        itineraryItems.push({
          id: dayKey,
          day: dayNumber,
          date: dayData.day_label || `Day ${dayNumber}`,
          activities
        })
      }
    })
    
    return itineraryItems.sort((a, b) => a.day - b.day)
  } catch (error) {
    console.error('Error parsing itinerary data:', error)
    return []
  }
}

export function TripDetails() {
  const { groupCode } = useParams<{ groupCode: string }>()
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [trip, setTrip] = useState<TripDetails | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'overview' | 'itinerary' | 'members' | 'activities'>('overview')
  const [error, setError] = useState<string | null>(null)
  const [isPlanning, setIsPlanning] = useState(false)
  const [planError, setPlanError] = useState<string | null>(null)
  const [planSuccess, setPlanSuccess] = useState(false)
  const [isEditingDestinations, setIsEditingDestinations] = useState(false)
  const [editDestination, setEditDestination] = useState<string>('')
  const [isSavingDestinations, setIsSavingDestinations] = useState(false)
  const [tripPlan, setTripPlan] = useState<any>(null)
  const [replanNotice, setReplanNotice] = useState(false)
  const [isResettingPlan, setIsResettingPlan] = useState(false)

  // Edit details (dates/budget/accommodation)
  const [isEditingDetails, setIsEditingDetails] = useState(false)
  const [editDepartureDate, setEditDepartureDate] = useState<string>('')
  const [editReturnDate, setEditReturnDate] = useState<string>('')
  const [editBudget, setEditBudget] = useState<string>('')
  const [editAccommodation, setEditAccommodation] = useState<string>('standard')

  // Extract hotel recommendations (recommended + alternates) from tripPlan if present
  const getHotelRecommendations = (plan: any) => {
    if (!plan) return null
    if (plan.hotel_recommendations) {
      const hr = plan.hotel_recommendations
      let recommended = hr.recommended || null
      let alternates = hr.alternates || []
      const all = hr.all || []
      // Fallback: if no explicit recommended/alternates but we have a list of hotels, promote top ones
      if (!recommended && (!alternates || alternates.length === 0) && all && all.length > 0) {
        recommended = all[0]
        alternates = all.slice(1, 3)
      }
      return { recommended, alternates, all }
    }
    // Direct top-level
    if (plan.recommended || plan.alternates) {
      return {
        recommended: plan.recommended || null,
        alternates: plan.alternates || []
      }
    }
    // Search nested (e.g., under destination keys like MAD/BCN or tool-specific blocks)
    try {
      const keys = Object.keys(plan)
      for (const k of keys) {
        const v = plan[k]
        if (v && typeof v === 'object' && (v.recommended || v.alternates)) {
          return {
            recommended: v.recommended || null,
            alternates: v.alternates || []
          }
        }
      }
    } catch {}
    return null
  }
  const handleResetPlan = async () => {
    if (!groupCode) return
    setIsResettingPlan(true)
    try {
      const { tripAPI } = await import('../services/api')
      await tripAPI.resetPlan(groupCode)
      setTripPlan(null)
      setTrip(prev => prev ? { ...prev, status: 'planning', itinerary: [] } : null)
      setReplanNotice(true)
    } catch (error: any) {
      console.error('Failed to reset plan:', error)
      window.alert(error?.response?.data?.detail || 'Failed to reset plan. Please try again.')
    } finally {
      setIsResettingPlan(false)
    }
  }

  useEffect(() => {
    const fetchTripDetails = async () => {
      if (!groupCode) return

      setIsLoading(true)
      try {
        const { tripAPI } = await import('../services/api')
        const tripDetails = await tripAPI.getTripDetails(groupCode)
        
        if (tripDetails) {
          // Transform the API response to match our TripDetails interface
          // Find the creator who has the enhanced trip data merged by the backend
          const creator = tripDetails.groupData?.find((user: any) => user.role === 'creator') || {}
          const fallbackData = tripDetails.groupData?.[0] || {}
          
          // Use creator data (which has trip_group data merged) or fallback
          const sourceData = Object.keys(creator).length > 0 ? creator : fallbackData
          
          const destination = sourceData.destination || 'Unknown'
          const budget = sourceData.budget || 1000
          
          // Store trip plan for separate display
          const tripPlan = tripDetails.tripPlan

          const transformedTrip: TripDetails = {
            groupCode: tripDetails.groupCode,
            tripName: sourceData.trip_name || `Trip to ${destination}`,
            destination: destination,
            departureDate: sourceData.departure_date || '',
            returnDate: sourceData.return_date || '',
            budget: budget.toString(),
            accommodation: sourceData.accommodation_preference || 'standard',
            description: sourceData.description || '',
            status: tripDetails.status || 'planning',
            createdAt: new Date().toISOString(),
            members: tripDetails.groupData?.map((user: any, index: number) => ({
              id: (index + 1).toString(),
              name: user.name || user.email?.split('@')[0] || 'Unknown User',
              email: user.email || '',
              role: user.role || 'member',
              joinedAt: user.submitted_at || new Date().toISOString()
            })) || [],
            itinerary: [] // Will be updated when trip plan is processed
          }
          
          setTrip(transformedTrip)
          
          // Store trip plan separately for display
          if (hasTripPlan(tripPlan)) {
            console.log('🎉 Trip plan found:', tripPlan)
            setTripPlan(tripPlan)
          }
        } else {
          setError('Trip not found or you don\'t have access to it.')
        }
      } catch (error: any) {
        console.error('Failed to fetch trip details:', error)
        if (error.response?.status === 404) {
          setError('Trip not found.')
        } else if (error.response?.status === 403) {
          setError('You don\'t have access to this trip.')
        } else {
          setError('Failed to load trip details. Please try again.')
        }
      } finally {
        setIsLoading(false)
      }
    }

    fetchTripDetails()
  }, [groupCode])

  useEffect(() => {
    if (tripPlan) {
      // Prefer optimized dates from cost_optimization block, then date_range
      const optimizedDeparture = tripPlan?.cost_optimization?.departure_date || tripPlan?.date_range?.start_date
      const optimizedReturn = tripPlan?.cost_optimization?.return_date || tripPlan?.date_range?.end_date

      setTrip(prev => prev ? {
        ...prev,
        itinerary: transformItineraryData(tripPlan),
        departureDate: optimizedDeparture || prev.departureDate,
        returnDate: optimizedReturn || prev.returnDate
      } : null)
    }
  }, [tripPlan])

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Not set'
    const parseDateLocal = (s: string) => {
      if (!s) return null as any
      if (s.includes('T')) {
        const d = new Date(s)
        return isNaN(d.getTime()) ? null : d
      }
      const parts = s.split('-').map(p => parseInt(p, 10))
      if (parts.length === 3) {
        const d = new Date(parts[0], parts[1] - 1, parts[2])
        return isNaN(d.getTime()) ? null : d
      }
      const d = new Date(s)
      return isNaN(d.getTime()) ? null : d
    }

    const date = parseDateLocal(dateString)
    if (!date) return 'Invalid date'

    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  // Format a day date with fallback to departureDate + (day-1)
  const formatDayDate = (dayItem: ItineraryItem) => {
    const primary = formatDate(dayItem.date)
    if (primary !== 'Invalid date') return primary
    // Fallback using trip.departureDate with local parsing
    if (trip?.departureDate) {
      const parseDateLocal = (s: string) => {
        if (!s) return null as any
        if (s.includes('T')) {
          const d = new Date(s)
          return isNaN(d.getTime()) ? null : d
        }
        const parts = s.split('-').map(p => parseInt(p, 10))
        if (parts.length === 3) {
          const d = new Date(parts[0], parts[1] - 1, parts[2])
          return isNaN(d.getTime()) ? null : d
        }
        const d = new Date(s)
        return isNaN(d.getTime()) ? null : d
      }
      const base = parseDateLocal(trip.departureDate)
      if (base) {
        const d = new Date(base)
        d.setDate(d.getDate() + Math.max(0, (dayItem.day || 1) - 1))
        return d.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
      }
    }
    return 'TBD'
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'planning':
        return 'bg-yellow-100 text-yellow-800 border border-yellow-200'
      case 'planned':
        return 'bg-green-100 text-green-800 border border-green-200'
      case 'completed':
        return 'bg-gray-100 text-gray-800 border border-gray-200'
      default:
        return 'bg-gray-100 text-gray-800 border border-gray-200'
    }
  }

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'flight':
        return <Plane className="h-4 w-4" />
      case 'accommodation':
        return <Building className="h-4 w-4" />
      case 'activity':
        return <Activity className="h-4 w-4" />
      case 'meal':
        return <Star className="h-4 w-4" />
      default:
        return <Clock className="h-4 w-4" />
    }
  }

  // Derive the signed-in user's departure city and flight/links from tripPlan
  const getMyFlight = () => {
    if (!tripPlan || !user?.email) return null
    try {
      const prefs = tripPlan.preferences_used
      const flights = tripPlan.flights?.by_departure_city || {}
      const booking = tripPlan.booking_links?.flights || {}
      if (!prefs || !prefs.flight_groups) return null

      // Map email to their group departure city
      let myDepartureCity: string | null = null
      for (const fg of prefs.flight_groups as any[]) {
        if (Array.isArray(fg.passengers) && fg.passengers.includes(user.email)) {
          myDepartureCity = fg.departure_city
          break
        }
      }
      if (!myDepartureCity) return null

      let myFlightInfo = flights[myDepartureCity]
      const bookingEntry = booking[myDepartureCity]
      const myLinks = bookingEntry?.booking_links || []

      // Fallback: if no Amadeus flight info, derive minimal info from booking links' flight_info
      if (!myFlightInfo && bookingEntry?.flight_info) {
        const fi = bookingEntry.flight_info
        myFlightInfo = {
          origin: fi.origin,
          destination: fi.destination,
          departure_date: fi.departure_date,
          return_date: fi.return_date,
          total_price: fi.price,
          airline_code: fi.airline_code,
          flight_number: fi.flight_number,
          // Unknown fields when coming from booking fallback
          stops: undefined,
          duration: undefined
        }
      }
      if (!myFlightInfo) return null

      return { departureCity: myDepartureCity, flight: myFlightInfo, links: myLinks }
    } catch {
      return null
    }
  }

  const shareTrip = () => {
    if (navigator.share) {
      navigator.share({
        title: `Join ${trip?.tripName}!`,
        text: `Join my group trip with code: ${trip?.groupCode}`,
        url: window.location.origin + '/join-trip'
      })
    } else {
      navigator.clipboard.writeText(`Join my trip "${trip?.tripName}" with code: ${trip?.groupCode}`)
    }
  }

  const handlePlanTrip = async () => {
    if (!groupCode) return

    setIsPlanning(true)
    setPlanError(null)

    try {
      console.log('🚀 Starting trip planning for group:', groupCode)
      const { tripAPI } = await import('../services/api')
      const result = await tripAPI.planTrip(groupCode)
      
      if (result.error) {
        setPlanError(result.error)
        console.error('❌ Trip planning failed:', result.error)
      } else {
        setPlanSuccess(true)
        console.log('✅ Trip planning completed successfully:', result)
        
        // In development: fetch saved plan immediately to update UI without reload
        const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        if (isDevelopment) {
          try {
            const latestPlan = await tripAPI.getTripPlan(groupCode)
            if (hasTripPlan(latestPlan)) {
              setTripPlan(latestPlan)
            }
          } catch (e) {
            console.warn('⚠️ Failed to fetch saved plan immediately:', e)
          }
        } else {
          // In production, keep the previous auto-reload behavior
          setTimeout(() => {
            window.location.reload()
          }, 2000)
        }
      }
    } catch (error: any) {
      console.error('❌ Trip planning error:', error)
      setPlanError(error.response?.data?.detail || 'Failed to plan trip. Please try again.')
    } finally {
      setIsPlanning(false)
    }
  }

  const handleEditDestinations = () => {
    if (trip) {
      setEditDestination(trip.destination || '')
      setIsEditingDestinations(true)
    }
  }

  // (removed duplicate handleResetPlan)

  const handleSaveDestinations = async () => {
    if (!groupCode || !trip) return

    if (!editDestination.trim()) {
      setError('Destination is required')
      return
    }

    setIsSavingDestinations(true)
    setError(null)

    try {
      const { tripAPI } = await import('../services/api')
      const res = await tripAPI.updateTrip(groupCode, {
        destination: editDestination.trim()
      })
      const updated = res?.group || {}
      const requiresReplan = !!(res?.requires_replan || res?.requires_replanning)
      setTrip(prev => prev ? {
        ...prev,
        destination: updated.destination || editDestination.trim(),
        status: requiresReplan ? 'planning' as any : prev.status
      } : null)
      if (requiresReplan) setReplanNotice(true)
      setIsEditingDestinations(false)
    } catch (error: any) {
      console.error('Failed to update destination:', error)
      // Avoid tripping the page-level fatal error overlay; surface inline feedback instead
      window.alert(error?.response?.data?.detail || 'Failed to update destination. Please try again.')
    } finally {
      setIsSavingDestinations(false)
    }
  }

  const handleEditDetails = () => {
    if (!trip) return
    setEditDepartureDate(trip.departureDate || '')
    setEditReturnDate(trip.returnDate || '')
    setEditBudget(trip.budget || '')
    setEditAccommodation(trip.accommodation || 'standard')
    setIsEditingDetails(true)
  }

  const handleCancelEditDetails = () => {
    setIsEditingDetails(false)
  }

  const handleSaveDetails = async () => {
    if (!groupCode || !trip) return
    const payload: any = {}
    if (editDepartureDate) payload.departure_date = editDepartureDate
    if (editReturnDate) payload.return_date = editReturnDate
    if (editBudget) payload.budget = parseInt(editBudget, 10)
    if (editAccommodation) payload.accommodation = editAccommodation
    try {
      const { tripAPI } = await import('../services/api')
      const res = await tripAPI.updateTrip(groupCode, payload)
      const updated = res?.group || {}
      const requiresReplan = !!(res?.requires_replan || res?.requires_replanning)
      setTrip(prev => prev ? {
        ...prev,
        departureDate: updated.departure_date || editDepartureDate || prev.departureDate,
        returnDate: updated.return_date || editReturnDate || prev.returnDate,
        budget: (updated.budget != null ? String(updated.budget) : (editBudget || prev.budget)),
        accommodation: updated.accommodation || editAccommodation || prev.accommodation,
        status: requiresReplan ? 'planning' as any : prev.status
      } : null)
      if (requiresReplan) setReplanNotice(true)
      setIsEditingDetails(false)
    } catch (error: any) {
      console.error('Failed to update trip details:', error)
      window.alert(error?.response?.data?.detail || 'Failed to update trip details. Please try again.')
    }
  }

  const handleCancelEditDestinations = () => {
    setIsEditingDestinations(false)
    setEditDestination('')
    setError(null)
  }

  const isCreator = trip?.members.find(m => m.email === user?.email)?.role === 'creator'

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent mx-auto mb-4"></div>
          <p className="text-gray-600">Loading trip details...</p>
        </div>
      </div>
    )
  }

  if (error || !trip) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="card max-w-md text-center">
          <AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">Trip Not Found</h2>
          <p className="text-gray-600 mb-6">
            {error || 'The trip you\'re looking for doesn\'t exist or you don\'t have access to it.'}
          </p>
          <button
            onClick={() => navigate('/dashboard')}
            className="btn-primary"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    )
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
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {trip.tripName}
              </h1>
              <div className="flex items-center space-x-4 text-gray-600">
                <div className="flex items-center">
                  <MapPin className="h-4 w-4 mr-1" />
                  {isCreator && !isEditingDestinations ? (
                    <div className="flex items-center space-x-2">
                      <span>{trip.destination}</span>
                      <button
                        onClick={handleEditDestinations}
                        className="text-primary-600 hover:text-primary-800 p-1"
                        title="Edit destinations"
                      >
                        <Edit3 className="h-3 w-3" />
                      </button>
                    </div>
                  ) : isCreator && isEditingDestinations ? (
                    <div className="flex items-center space-x-2">
                      <input
                        type="text"
                        value={editDestination}
                        onChange={(e) => setEditDestination(e.target.value)}
                        placeholder="Enter destination (e.g., Barcelona, Tokyo, Paris)"
                        className="text-sm px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                        style={{ minWidth: '200px' }}
                      />
                      <div className="flex flex-col space-y-1">
                        <button
                          onClick={handleSaveDestinations}
                          disabled={isSavingDestinations}
                          className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50"
                        >
                          {isSavingDestinations ? 'Saving...' : 'Save'}
                        </button>
                        <button
                          onClick={handleCancelEditDestinations}
                          disabled={isSavingDestinations}
                          className="px-2 py-1 bg-gray-500 text-white text-xs rounded hover:bg-gray-600 disabled:opacity-50"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <span>{trip.destination}</span>
                  )}
                </div>
                <div className="flex items-center">
                  <Users className="h-4 w-4 mr-1" />
                  <span>{trip.members.length} members</span>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${getStatusColor(trip.status)}`}>
                  {trip.status}
                </span>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={shareTrip}
                className="btn-secondary flex items-center space-x-2"
              >
                <Share2 className="h-4 w-4" />
                <span>Share</span>
              </button>
              
              <button
                onClick={() => navigate(`/trip/${groupCode}/my-preferences`)}
                className="btn-secondary flex items-center space-x-2"
              >
                <User className="h-4 w-4" />
                <span>My Preferences</span>
              </button>
              
              {isCreator && (
                <>
                  <button
                    onClick={handlePlanTrip}
                    disabled={isPlanning || trip.status === 'planned'}
                    className="btn-accent flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isPlanning ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                        <span>Planning...</span>
                      </>
                    ) : (
                      <>
                        <Activity className="h-4 w-4" />
                        <span>Plan Trip</span>
                      </>
                    )}
                  </button>
                  
                  {/* Temporary Debug Button */}
                  {trip.status === 'planned' && (
                    <button
                      onClick={handleResetPlan}
                      className="btn-secondary flex items-center space-x-2 text-xs disabled:opacity-50"
                      disabled={isResettingPlan}
                    >
                      <span>{isResettingPlan ? 'Resetting...' : 'Reset Plan'}</span>
                    </button>
                  )}
                  
                  <button className="btn-primary flex items-center space-x-2" onClick={handleEditDetails}>
                    <Settings className="h-4 w-4" />
                    <span>Settings</span>
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Trip Code */}
          <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-primary-700">Group Code</p>
                <p className="text-xl font-bold text-primary-900 tracking-wider">{trip.groupCode}</p>
              </div>
              <div className="text-sm text-primary-700">
                Share this code with friends to invite them
              </div>
            </div>
          </div>

          {/* Replan notice */}
          {replanNotice && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center space-x-2 p-4 bg-yellow-50 border border-yellow-200 rounded-lg mb-3"
            >
              <AlertCircle className="h-5 w-5 text-yellow-600" />
              <span className="text-yellow-700 text-sm">Trip details changed. Click “Plan Trip” to regenerate the itinerary.</span>
            </motion.div>
          )}

          {/* Plan Error */}
          {planError && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center space-x-2 p-4 bg-red-50 border border-red-200 rounded-lg"
            >
              <AlertCircle className="h-5 w-5 text-red-600" />
              <span className="text-red-700 text-sm">{planError}</span>
            </motion.div>
          )}

                    {/* Plan Success */}
          {planSuccess && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-green-50 border border-green-200 rounded-lg p-4"
            >
              <div className="flex items-center space-x-2 mb-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span className="text-green-700 text-sm font-medium">
                  Trip planning completed successfully!
                </span>
              </div>
              <p className="text-green-700 text-sm mb-2">
                Check the console logs for details.
              </p>
              {(window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && (
                <div className="text-xs text-orange-600 bg-orange-50 border border-orange-200 rounded p-2">
                  💡 Auto-reload disabled in development mode for console debugging. Manually refresh to see updated trip status.
                </div>
              )}
            </motion.div>
          )}
        </motion.div>

        {/* Navigation Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mb-8"
        >
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: 'overview', name: 'Overview', icon: MapPin },
                { id: 'itinerary', name: 'Itinerary', icon: Calendar },
                { id: 'activities', name: 'Activities', icon: Search },
                { id: 'members', name: 'Members', icon: Users }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <tab.icon className="h-4 w-4" />
                  <span>{tab.name}</span>
                </button>
              ))}
            </nav>
          </div>
        </motion.div>

        {/* Tab Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Trip Info */}
              <div className="lg:col-span-2 space-y-6">
                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Trip Information</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                        <Calendar className="h-5 w-5 text-primary-600" />
                        <div>
                          <div className="text-sm text-gray-600">Departure</div>
                          <div className="font-medium">{formatDate(trip.departureDate)}</div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                        <Calendar className="h-5 w-5 text-primary-600" />
                        <div>
                          <div className="text-sm text-gray-600">Return</div>
                          <div className="font-medium">{formatDate(trip.returnDate)}</div>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                        <DollarSign className="h-5 w-5 text-accent-600" />
                        <div>
                          <div className="text-sm text-gray-600">Budget per Person</div>
                          <div className="font-medium">${trip.budget}</div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                        <Building className="h-5 w-5 text-secondary-600" />
                        <div>
                          <div className="text-sm text-gray-600">Accommodation</div>
                          <div className="font-medium capitalize">{trip.accommodation}</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {trip.description && (
                    <div className="mt-6 pt-6 border-t border-gray-200">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">Description</h4>
                      <p className="text-gray-700">{trip.description}</p>
                    </div>
                  )}
                </div>

                {/* My Flight */}
                {(() => {
                  const mine = getMyFlight()
                  if (!mine) return null
                  const f = mine.flight
                  const links = mine.links
                  return (
                    <div className="card">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">My Flight</h3>
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-medium text-gray-900">
                            {f.origin} → {f.destination} ({f.airline_code || ''})
                          </div>
                          <div className="text-sm text-gray-600">
                            Depart {formatDate(f.departure_date || trip?.departureDate)} • Return {formatDate(f.return_date || trip?.returnDate)}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {f.flight_number ? `Flight ${f.flight_number}` : ''} {f.stops != null ? `• ${f.stops} stop${f.stops === 1 ? '' : 's'}` : ''} {f.duration ? `• ${f.duration}` : ''}
                          </div>
                        </div>
                        <div className="text-right">
                          {f.total_price && (
                            <>
                              <div className="text-xs text-gray-600">Est. total</div>
                              <div className="font-semibold text-gray-900">${f.total_price}</div>
                            </>
                          )}
                        </div>
                      </div>
                      {links && links.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {links.slice(0, 3).map((l: any, idx: number) => (
                            <a key={idx} href={l.url} target="_blank" rel="noreferrer" className="btn-secondary text-xs">
                              Book on {l.platform}
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })()}

                {/* Accommodation Recommendations */}
                {tripPlan && (() => {
                  const recs = getHotelRecommendations(tripPlan)
                  if (!recs || (!recs.recommended && (!recs.alternates || recs.alternates.length === 0))) return null
                  return (
                    <div className="card">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommended Hotel</h3>
                      {recs.recommended && (
                        <div className="p-4 border border-green-200 rounded-lg bg-green-50 mb-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="font-medium text-gray-900">{recs.recommended.hotel_name || 'Recommended'}</div>
                              <div className="text-sm text-gray-600">
                                {recs.recommended.hotel_rating ? `${recs.recommended.hotel_rating}★` : 'Unrated'}
                                {recs.recommended.distance_km_to_anchor != null && (
                                  <span> • {recs.recommended.distance_km_to_anchor.toFixed ? recs.recommended.distance_km_to_anchor.toFixed(1) : recs.recommended.distance_km_to_anchor} km to center</span>
                                )}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-sm text-gray-600">Total (group)</div>
                              <div className="font-semibold text-gray-900">${recs.recommended.total_trip_cost}</div>
                            </div>
                          </div>
                          {recs.recommended.address && (
                            <div className="mt-2 text-sm text-gray-600">{recs.recommended.address}</div>
                          )}
                          {/* Room breakdown and per-person split (summary tab) */}
                          {recs.recommended?.room_breakdown && (
                            <div className="mt-3 text-sm text-gray-700">
                              <div>
                                <b>Rooms</b>: {Object.entries(recs.recommended.room_breakdown.counts || {})
                                  .map(([t, n]) => `${n} ${t}`)
                                  .join(', ')}
                              </div>
                              {Array.isArray(recs.recommended.room_breakdown.details) && (
                                <ul className="list-disc ml-5 mt-1">
                                  {recs.recommended.room_breakdown.details.map((r: any, i: number) => (
                                    <li key={i}>
                                      {r.room_type} (cap {r.capacity}): {Array.isArray(r.occupant_names) ? r.occupant_names.join(', ') : ''}
                                      {r.total_room_cost != null ? ` — room total: $${Math.round(r.total_room_cost)}` : ''}
                                    </li>
                                  ))}
                                </ul>
                              )}
                            </div>
                          )}
                          {Array.isArray(recs.recommended?.individual_costs) && (
                            <div className="mt-3 text-sm text-gray-700">
                              <b>Per‑person costs</b>
                              <ul className="list-disc ml-5 mt-1">
                                {recs.recommended.individual_costs.map((p: any, i: number) => (
                                  <li key={i}>{(p.name || p.user_name || p.user_email)}: ${Math.round(p.total_cost)} ({p.room_type})</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                      {recs.alternates && recs.alternates.length > 0 && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 mb-2">Alternatives</h4>
                          <div className="space-y-2">
                            {recs.alternates.map((alt: any, idx: number) => (
                              <div key={idx} className="p-3 border border-gray-200 rounded-lg">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <div className="font-medium text-gray-900">{alt.hotel_name || 'Alternate'}</div>
                                    <div className="text-xs text-gray-600">
                                      {alt.hotel_rating ? `${alt.hotel_rating}★` : 'Unrated'}
                                      {alt.distance_km_to_anchor != null && (
                                        <span> • {alt.distance_km_to_anchor.toFixed ? alt.distance_km_to_anchor.toFixed(1) : alt.distance_km_to_anchor} km</span>
                                      )}
                                    </div>
                                  </div>
                                  <div className="text-right">
                                    <div className="text-xs text-gray-600">Total (group)</div>
                                    <div className="font-semibold text-gray-900">${alt.total_trip_cost}</div>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })()}

                {/* Quick Stats */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="card text-center">
                    <div className="text-2xl font-bold text-primary-600">
                      {(() => {
                        if (!trip.departureDate || !trip.returnDate) return 'TBD'
                        const parseDateLocal = (s: string) => {
                          if (!s) return null as any
                          if (s.includes('T')) {
                            const d = new Date(s)
                            return isNaN(d.getTime()) ? null : d
                          }
                          const parts = s.split('-').map(p => parseInt(p, 10))
                          if (parts.length === 3) {
                            const d = new Date(parts[0], parts[1] - 1, parts[2])
                            return isNaN(d.getTime()) ? null : d
                          }
                          const d = new Date(s)
                          return isNaN(d.getTime()) ? null : d
                        }
                        const start = parseDateLocal(trip.departureDate)
                        const end = parseDateLocal(trip.returnDate)
                        if (!start || !end) return 'TBD'
                        const days = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
                        return days > 0 ? days : 'TBD'
                      })()}
                    </div>
                    <div className="text-sm text-gray-600">Days</div>
                  </div>
                  <div className="card text-center">
                    <div className="text-2xl font-bold text-secondary-600">{trip.members.length}</div>
                    <div className="text-sm text-gray-600">Members</div>
                  </div>
                  <div className="card text-center">
                    <div className="text-2xl font-bold text-accent-600">
                      ${(() => {
                        const budget = parseInt(trip.budget)
                        if (isNaN(budget)) return '0'
                        return budget * trip.members.length
                      })()}
                    </div>
                    <div className="text-sm text-gray-600">Total Budget</div>
                  </div>
                </div>
              </div>

              {/* Recent Activity */}
              <div className="space-y-6">
                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
                  <div className="space-y-3">
                    <div className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                      <div className="flex-1">
                        <p className="text-sm text-gray-800">Trip created by <strong>{trip.members.find(m => m.role === 'creator')?.name || 'You'}</strong></p>
                        <p className="text-xs text-gray-500">Recently</p>
                      </div>
                    </div>
                    {trip.members.length > 1 && trip.members.filter(m => m.role !== 'creator').map((member, index) => (
                      <div key={member.id} className="flex items-start space-x-3">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                        <div className="flex-1">
                          <p className="text-sm text-gray-800"><strong>{member.name}</strong> joined the trip</p>
                          <p className="text-xs text-gray-500">Recently</p>
                        </div>
                      </div>
                    ))}
                    {trip.members.length === 1 && (
                      <div className="flex items-start space-x-3">
                        <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                        <div className="flex-1">
                          <p className="text-sm text-gray-800">Waiting for members to join...</p>
                          <p className="text-xs text-gray-500">Share the group code to invite friends!</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Next Steps</h3>
                  <div className="space-y-3">
                    <div className="flex items-center space-x-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <Clock className="h-4 w-4 text-yellow-600" />
                      <span className="text-sm text-yellow-800">Finalize accommodation bookings</span>
                    </div>
                    <div className="flex items-center space-x-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <Plane className="h-4 w-4 text-blue-600" />
                      <span className="text-sm text-blue-800">Book group flights</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'itinerary' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Trip Itinerary</h3>
                {isCreator && (
                  <button className="btn-primary flex items-center space-x-2">
                    <Edit3 className="h-4 w-4" />
                    <span>Edit Itinerary</span>
                  </button>
                )}
              </div>

              {/* My Flight card also in Itinerary tab */}
              {(() => {
                const mine = getMyFlight()
                if (!mine) return null
                const f = mine.flight
                const links = mine.links
                return (
                  <div className="card">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">My Flight</h3>
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-medium text-gray-900">
                          {f.origin} → {f.destination} ({f.airline_code || ''})
                        </div>
                        <div className="text-xs text-gray-600 mt-1">
                          {f.flight_number ? `Flight ${f.flight_number}` : ''} {f.stops != null ? `• ${f.stops} stop${f.stops === 1 ? '' : 's'}` : ''} {f.duration ? `• ${f.duration}` : ''}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">
                          Depart {formatDate(f.departure_date || trip?.departureDate)} • Return {formatDate(f.return_date || trip?.returnDate)}
                        </div>
                      </div>
                      <div className="text-right">
                        {f.total_price && (
                          <>
                            <div className="text-xs text-gray-600">Est. total</div>
                            <div className="font-semibold text-gray-900">${f.total_price}</div>
                          </>
                        )}
                      </div>
                    </div>
                    {links && links.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {links.slice(0, 3).map((l: any, idx: number) => (
                          <a key={idx} href={l.url} target="_blank" rel="noreferrer" className="btn-secondary text-xs">
                            Book on {l.platform}
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })()}

              {/* Recommended hotel summary */}
              {tripPlan && (() => {
                const recs = getHotelRecommendations(tripPlan)
                if (!recs || (!recs.recommended && (!recs.alternates || recs.alternates.length === 0))) return null
                return (
                  <div className="card">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Accommodation Picks</h3>
                    {recs.recommended && (
                      <div className="p-3 border border-green-200 rounded-lg bg-green-50 mb-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium text-gray-900">{recs.recommended.hotel_name || 'Recommended'}</div>
                            <div className="text-xs text-gray-600">
                              {recs.recommended.hotel_rating ? `${recs.recommended.hotel_rating}★` : 'Unrated'}
                              {recs.recommended.distance_km_to_anchor != null && (
                                <span> • {recs.recommended.distance_km_to_anchor.toFixed ? recs.recommended.distance_km_to_anchor.toFixed(1) : recs.recommended.distance_km_to_anchor} km</span>
                              )}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-xs text-gray-600">Total (group)</div>
                            <div className="font-semibold text-gray-900">${recs.recommended.total_trip_cost}</div>
                          </div>
                        </div>
                        {/* Room breakdown and per-person split (itinerary tab) */}
                        {recs.recommended?.room_breakdown && (
                          <div className="mt-2 text-xs text-gray-700">
                            <div>
                              <b>Rooms</b>: {Object.entries(recs.recommended.room_breakdown.counts || {})
                                .map(([t, n]) => `${n} ${t}`)
                                .join(', ')}
                            </div>
                            {Array.isArray(recs.recommended.room_breakdown.details) && (
                              <ul className="list-disc ml-5 mt-1">
                                {recs.recommended.room_breakdown.details.map((r: any, i: number) => (
                                  <li key={i}>
                                    {r.room_type} (cap {r.capacity}): {Array.isArray(r.occupant_names) ? r.occupant_names.join(', ') : ''}
                                    {r.total_room_cost != null ? ` — room total: $${Math.round(r.total_room_cost)}` : ''}
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        )}
                        {Array.isArray(recs.recommended?.individual_costs) && (
                          <div className="mt-2 text-xs text-gray-700">
                            <b>Per‑person costs</b>
                            <ul className="list-disc ml-5 mt-1">
                              {recs.recommended.individual_costs.map((p: any, i: number) => (
                                <li key={i}>{(p.name || p.user_name || p.user_email)}: ${Math.round(p.total_cost)} ({p.room_type})</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                    {recs.alternates && recs.alternates.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 mb-2">Alternatives</h4>
                        <div className="space-y-2">
                          {recs.alternates.map((alt: any, idx: number) => (
                            <div key={idx} className="p-3 border border-gray-200 rounded-lg">
                              <div className="flex items-center justify-between">
                                <div>
                                  <div className="font-medium text-gray-900">{alt.hotel_name || 'Alternate'}</div>
                                  <div className="text-xs text-gray-600">
                                    {alt.hotel_rating ? `${alt.hotel_rating}★` : 'Unrated'}
                                    {alt.distance_km_to_anchor != null && (
                                      <span> • {alt.distance_km_to_anchor.toFixed ? alt.distance_km_to_anchor.toFixed(1) : alt.distance_km_to_anchor} km</span>
                                    )}
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="text-xs text-gray-600">Total (group)</div>
                                  <div className="font-semibold text-gray-900">${alt.total_trip_cost}</div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })()}

              {/* Removed Generated Trip Plan section to avoid duplication */}

              {/* No Trip Plan Message */}
              {!tripPlan && trip.itinerary.length === 0 && (
                <div className="text-center py-12">
                  <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Itinerary Yet</h3>
                  <p className="text-gray-600 mb-6">
                    Once trip planning is complete, your detailed itinerary will appear here.
                  </p>
                  {isCreator && trip.status === 'planning' && (
                    <button
                      onClick={handlePlanTrip}
                      disabled={isPlanning}
                      className="btn-primary flex items-center space-x-2 mx-auto"
                    >
                      {isPlanning ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                          <span>Planning...</span>
                        </>
                      ) : (
                        <>
                          <Activity className="h-4 w-4" />
                          <span>Generate Itinerary</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              )}

              {/* Regular Itinerary Items */}
              {trip.itinerary.map((day) => (
                <div key={day.id} className="card">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-lg font-semibold text-gray-900">
                      Day {day.day} - {formatDayDate(day)}
                    </h4>
                  </div>

                  <div className="space-y-3">
                    {day.activities.length === 0 && (
                      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800 text-sm">
                        No scheduled activities for this day.
                      </div>
                    )}
                    {day.activities.map((activity, index) => (
                      <div key={index} className="flex items-start space-x-4 p-4 bg-gray-50 rounded-lg">
                        <div className="flex-shrink-0">
                          <div className={`p-2 rounded-lg ${
                            activity.type === 'flight' ? 'bg-blue-100 text-blue-600' :
                            activity.type === 'accommodation' ? 'bg-green-100 text-green-600' :
                            activity.type === 'activity' ? 'bg-purple-100 text-purple-600' :
                            'bg-orange-100 text-orange-600'
                          }`}>
                            {getActivityIcon(activity.type)}
                          </div>
                        </div>
                        
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <h5 className="font-medium text-gray-900">{activity.title}</h5>
                            <div className="flex items-center space-x-2">
                              <span className="text-sm text-gray-500">{activity.time}</span>
                              {activity.confirmed ? (
                                <CheckCircle className="h-4 w-4 text-green-500" />
                              ) : (
                                <Clock className="h-4 w-4 text-yellow-500" />
                              )}
                            </div>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{activity.description}</p>
                          <span className={`inline-block mt-2 px-2 py-1 text-xs rounded-full ${
                            activity.confirmed 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {activity.confirmed ? 'Confirmed' : 'Pending'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'activities' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Find Activities</h3>
                <div className="text-sm text-gray-500">
                  Powered by Google Places
                </div>
              </div>

              <ActivitySearch 
                destination={trip.destination} 
                onActivitySelect={(activity) => {
                  // TODO: Add activity to itinerary
                  console.log('Selected activity:', activity)
                  alert(`Activity "${activity.name}" selected! (Integration with itinerary coming soon)`)
                }}
              />
            </div>
          )}

          {activeTab === 'members' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Trip Members</h3>
                <button className="btn-primary flex items-center space-x-2">
                  <Share2 className="h-4 w-4" />
                  <span>Invite Members</span>
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {trip.members.map((member) => (
                  <div key={member.id} className="card">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        <div className="h-12 w-12 rounded-full bg-primary-600 flex items-center justify-center">
                          <span className="text-white font-medium">
                            {member.name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{member.name}</h4>
                        <p className="text-sm text-gray-600">{member.email}</p>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            member.role === 'creator' 
                              ? 'bg-primary-100 text-primary-800' 
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {member.role}
                          </span>
                          <span className="text-xs text-gray-500">
                            Joined {new Date(member.joinedAt).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="card">
                <h4 className="font-medium text-gray-900 mb-4">Group Chat</h4>
                <div className="flex items-center justify-center py-8 text-gray-500">
                  <div className="text-center">
                    <MessageCircle className="h-8 w-8 mx-auto mb-2" />
                    <p className="text-sm">Group chat coming soon!</p>
                    <p className="text-xs">Stay tuned for real-time messaging with your travel companions.</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
} 