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
  Edit3
} from 'lucide-react'
import { useAuthStore } from '../stores/authStore'

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

// Helper function to check if trip plan exists
function hasTripPlan(tripPlan: any): boolean {
  return tripPlan && tripPlan.agent_response
}

export function TripDetails() {
  const { groupCode } = useParams<{ groupCode: string }>()
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [trip, setTrip] = useState<TripDetails | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'overview' | 'itinerary' | 'members'>('overview')
  const [error, setError] = useState<string | null>(null)
  const [isPlanning, setIsPlanning] = useState(false)
  const [planError, setPlanError] = useState<string | null>(null)
  const [planSuccess, setPlanSuccess] = useState(false)
  const [isEditingDestinations, setIsEditingDestinations] = useState(false)
  const [editDestinations, setEditDestinations] = useState<string[]>(['', '', ''])
  const [isSavingDestinations, setIsSavingDestinations] = useState(false)
  const [tripPlan, setTripPlan] = useState<any>(null)

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
          
          const destinations = sourceData.destinations || []
          const budget = sourceData.budget || 1000
          
          // Store trip plan for separate display
          const tripPlan = tripDetails.tripPlan

          const transformedTrip: TripDetails = {
            groupCode: tripDetails.groupCode,
            tripName: sourceData.trip_name || `Trip to ${destinations.length > 0 ? destinations.join(', ') : 'Unknown'}`,
            destination: destinations.length > 0 ? destinations.join(', ') : 'Unknown',
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
            itinerary: [] // Keep empty for now, will add trip plan in separate section
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

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Not set'
    
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return 'Invalid date'
    
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
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
        
        // Only auto-reload in production, not development
        const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        
        if (!isDevelopment) {
          // Refresh trip details to get updated status
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
      const currentDestinations = trip.destination.split(', ').filter(d => d.trim() !== '')
      setEditDestinations([
        currentDestinations[0] || '',
        currentDestinations[1] || '',
        currentDestinations[2] || ''
      ])
      setIsEditingDestinations(true)
    }
  }

  const handleSaveDestinations = async () => {
    if (!groupCode || !trip) return

    const validDestinations = editDestinations.filter(dest => dest.trim() !== '')
    if (validDestinations.length === 0) {
      setError('At least one destination is required')
      return
    }

    setIsSavingDestinations(true)
    setError(null)

    try {
      // Create trip data with updated destinations
      const tripData = {
        group_code: groupCode,
        destinations: validDestinations,
        creator_email: user?.email || '',
        created_at: trip.createdAt,
        trip_name: trip.tripName,
        departure_date: trip.departureDate,
        return_date: trip.returnDate,
        budget: parseInt(trip.budget) || null,
        group_size: trip.members.length,
        accommodation: trip.accommodation,
        description: trip.description
      }

      const { tripAPI } = await import('../services/api')
      await tripAPI.createTrip(tripData) // This will update the existing trip

      // Update local state
      setTrip(prev => prev ? {
        ...prev,
        destination: validDestinations.join(', ')
      } : null)

      setIsEditingDestinations(false)
    } catch (error: any) {
      console.error('Failed to update destinations:', error)
      setError('Failed to update destinations. Please try again.')
    } finally {
      setIsSavingDestinations(false)
    }
  }

  const handleCancelEditDestinations = () => {
    setIsEditingDestinations(false)
    setEditDestinations(['', '', ''])
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
                      <div className="flex flex-col space-y-1">
                        {editDestinations.map((dest, index) => (
                          <input
                            key={index}
                            type="text"
                            value={dest}
                            onChange={(e) => {
                              const newDestinations = [...editDestinations]
                              newDestinations[index] = e.target.value
                              setEditDestinations(newDestinations)
                            }}
                            placeholder={index === 0 ? "Primary destination (required)" : `Optional destination ${index + 1}`}
                            className="text-sm px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                            style={{ minWidth: '200px' }}
                          />
                        ))}
                      </div>
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
                      onClick={() => {
                        setTrip(prev => prev ? {...prev, status: 'planning'} : null)
                      }}
                      className="btn-secondary flex items-center space-x-2 text-xs"
                    >
                      <span>Reset Status (Debug)</span>
                    </button>
                  )}
                  
                  <button className="btn-primary flex items-center space-x-2">
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

                {/* Quick Stats */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="card text-center">
                    <div className="text-2xl font-bold text-primary-600">
                      {(() => {
                        if (!trip.departureDate || !trip.returnDate) return 'TBD'
                        const start = new Date(trip.departureDate)
                        const end = new Date(trip.returnDate)
                        if (isNaN(start.getTime()) || isNaN(end.getTime())) return 'TBD'
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

              {/* Generated Trip Plan */}
              {tripPlan && (
                <div className="card">
                  <div className="flex items-center space-x-2 mb-4">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    <h3 className="text-lg font-bold text-gray-900">Generated Trip Plan</h3>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4 whitespace-pre-wrap text-sm text-gray-700 max-h-96 overflow-y-auto">
                    {tripPlan.agent_response}
                  </div>
                  
                  <div className="mt-4 text-xs text-gray-500">
                    Generated on {new Date(tripPlan.saved_at || Date.now()).toLocaleDateString()}
                  </div>
                </div>
              )}

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
                      Day {day.day} - {formatDate(day.date)}
                    </h4>
                  </div>

                  <div className="space-y-3">
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