import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Plus, Users, MapPin, Calendar, Plane, TrendingUp, Clock } from 'lucide-react'
import { useAuthStore } from '../stores/authStore'

interface Trip {
  groupCode: string
  tripStatus: string
  memberCount: number
  role: string
  joinedAt: string
  destination?: string
  departureDate?: string
}

export function Dashboard() {
  const { user } = useAuthStore()
  const [trips, setTrips] = useState<Trip[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchUserTrips = async () => {
      // Don't fetch if no user is logged in
      if (!user?.id) {
        setTrips([])
        setIsLoading(false)
        return
      }

      setIsLoading(true)
      try {
        const { authAPI } = await import('../services/api')
        const userTrips = await authAPI.getTrips()
        
        // Transform the API response to match our Trip interface
        const transformedTrips: Trip[] = userTrips.map((trip: any) => ({
          groupCode: trip.groupCode,
          tripStatus: trip.tripStatus,
          memberCount: trip.memberCount,
          role: trip.role,
          joinedAt: trip.joinedAt,
          destination: trip.destination || 'Unknown',
          departureDate: trip.departureDate
        }))
        
        setTrips(transformedTrips)
      } catch (error) {
        console.error('Failed to fetch user trips:', error)
        // Show empty state on error
        setTrips([])
      } finally {
        setIsLoading(false)
      }
    }

    // Add a small delay to ensure auth state is synchronized
    const timeoutId = setTimeout(fetchUserTrips, 100)
    return () => clearTimeout(timeoutId)
  }, [user?.id]) // Re-fetch when user changes

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

  const getRoleColor = (role: string) => {
    return role === 'creator' 
      ? 'bg-primary-100 text-primary-800 border border-primary-200' 
      : 'bg-gray-100 text-gray-800 border border-gray-200'
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'planning':
        return <Clock className="h-3 w-3" />
      case 'planned':
        return <TrendingUp className="h-3 w-3" />
      default:
        return <MapPin className="h-3 w-3" />
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Welcome back, {user?.fullName?.split(' ')[0] || 'Traveler'}! 👋
          </h1>
          <p className="text-lg text-gray-600">
            Manage your group trips and start planning new adventures.
          </p>
        </motion.div>

        {/* Stats Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
        >
          <div className="card text-center">
            <div className="text-3xl font-bold text-primary-600">{trips.length}</div>
            <div className="text-gray-600">Active Trips</div>
          </div>
          <div className="card text-center">
            <div className="text-3xl font-bold text-secondary-600">
              {trips.filter(t => t.role === 'creator').length}
            </div>
            <div className="text-gray-600">Trips Created</div>
          </div>
          <div className="card text-center">
            <div className="text-3xl font-bold text-accent-600">
              {trips.reduce((sum, trip) => sum + trip.memberCount, 0)}
            </div>
            <div className="text-gray-600">Total Members</div>
          </div>
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8"
        >
          <Link
            to="/create-trip"
            className="card hover:shadow-xl hover:scale-[1.02] transition-all duration-300 group cursor-pointer border-2 border-transparent hover:border-primary-200"
          >
            <div className="flex items-center space-x-4">
              <div className="gradient-bg p-4 rounded-xl group-hover:scale-105 transition-transform">
                <Plus className="h-8 w-8 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
                  Create New Trip
                </h3>
                <p className="text-gray-600">
                  Start planning a new group adventure
                </p>
              </div>
            </div>
          </Link>

          <Link
            to="/join-trip"
            className="card hover:shadow-xl hover:scale-[1.02] transition-all duration-300 group cursor-pointer border-2 border-transparent hover:border-secondary-200"
          >
            <div className="flex items-center space-x-4">
              <div className="bg-secondary-600 p-4 rounded-xl group-hover:scale-105 transition-transform">
                <Users className="h-8 w-8 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900 group-hover:text-secondary-600 transition-colors">
                  Join a Trip
                </h3>
                <p className="text-gray-600">
                  Join an existing group trip with a code
                </p>
              </div>
            </div>
          </Link>
        </motion.div>

        {/* Your Trips */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-3xl font-bold text-gray-900">Your Trips</h2>
            {trips.length > 0 && (
              <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                {trips.length} trip{trips.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="card animate-pulse">
                  <div className="h-6 bg-gray-200 rounded mb-4"></div>
                  <div className="h-4 bg-gray-200 rounded mb-3"></div>
                  <div className="h-4 bg-gray-200 rounded mb-3"></div>
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                </div>
              ))}
            </div>
          ) : trips.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
              className="text-center py-16"
            >
              <div className="gradient-bg p-8 rounded-full w-32 h-32 flex items-center justify-center mx-auto mb-8">
                <Plane className="h-16 w-16 text-white" />
              </div>
              <h3 className="text-2xl font-semibold text-gray-900 mb-3">
                No trips yet
              </h3>
              <p className="text-gray-600 mb-8 max-w-md mx-auto">
                Create your first group trip or join an existing one to get started on your adventure!
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center space-y-3 sm:space-y-0 sm:space-x-4">
                <Link to="/create-trip" className="btn-primary px-6 py-3">
                  Create New Trip
                </Link>
                <Link to="/join-trip" className="btn-secondary px-6 py-3">
                  Join a Trip
                </Link>
              </div>
            </motion.div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {trips.map((trip, index) => (
                <motion.div
                  key={trip.groupCode}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="h-full"
                >
                  <Link
                    to={`/trip/${trip.groupCode}`}
                    className="card hover:shadow-xl hover:scale-[1.02] transition-all duration-300 group cursor-pointer border-2 border-transparent hover:border-primary-200 h-full flex flex-col"
                  >
                    {/* Card Header */}
                    <div className="flex flex-col space-y-3 mb-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-bold text-gray-900 group-hover:text-primary-600 transition-colors truncate">
                            {trip.groupCode}
                          </h3>
                          {trip.destination && (
                            <div className="flex items-center text-gray-600 mt-1">
                              <MapPin className="h-3 w-3 mr-1 flex-shrink-0" />
                              <span className="text-sm font-medium truncate">{trip.destination}</span>
                            </div>
                          )}
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ml-2 flex-shrink-0 ${getStatusColor(trip.tripStatus)}`}>
                          {getStatusIcon(trip.tripStatus)}
                          <span className="capitalize">{trip.tripStatus}</span>
                        </span>
                      </div>
                    </div>

                    {/* Card Content */}
                    <div className="flex-1 space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex items-center text-gray-600">
                          <Users className="h-4 w-4 mr-2 text-secondary-500 flex-shrink-0" />
                          <span className="text-sm">{trip.memberCount} members</span>
                        </div>
                        <div className="flex justify-end">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRoleColor(trip.role)}`}>
                            {trip.role}
                          </span>
                        </div>
                      </div>
                      
                      {trip.departureDate && (
                        <div className="flex items-center text-gray-600">
                          <Calendar className="h-4 w-4 mr-2 text-primary-500 flex-shrink-0" />
                          <span className="text-sm">
                            Departs {new Date(trip.departureDate).toLocaleDateString()}
                          </span>
                        </div>
                      )}

                      <div className="flex items-center text-gray-500">
                        <Calendar className="h-4 w-4 mr-2 flex-shrink-0" />
                        <span className="text-xs">
                          Joined {new Date(trip.joinedAt).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    
                    {/* Card Footer */}
                    <div className="mt-4 pt-4 border-t border-gray-100">
                      <div className="flex items-center justify-between">
                        <span className="text-primary-600 text-sm font-medium group-hover:text-primary-700 transition-colors">
                          View Details
                        </span>
                        <span className="text-primary-600 group-hover:text-primary-700 group-hover:translate-x-1 transition-all duration-200">
                          →
                        </span>
                      </div>
                    </div>
                  </Link>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>

        {/* Recent Activity */}
        {trips.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="mt-12"
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Recent Activity</h2>
            <div className="card">
              <div className="space-y-4">
                <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-gray-700 flex-1">
                    <strong className="text-green-700">PARIS2024</strong> planning completed
                  </span>
                  <span className="text-xs text-gray-500">2 days ago</span>
                </div>
                <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-gray-700 flex-1">
                    New member joined <strong className="text-blue-700">TOKYO2024</strong>
                  </span>
                  <span className="text-xs text-gray-500">5 days ago</span>
                </div>
                <div className="flex items-center space-x-3 p-3 bg-purple-50 rounded-lg">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  <span className="text-gray-700 flex-1">
                    You created <strong className="text-purple-700">TOKYO2024</strong>
                  </span>
                  <span className="text-xs text-gray-500">1 week ago</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
} 