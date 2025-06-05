import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { 
  Users, 
  Calendar, 
  MapPin, 
  Plus,
  LogOut,
  Copy,
  Check
} from 'lucide-react';
import { api } from '../../services/api';
import { UserTrip } from '../../types/auth';

const TripsDashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [trips, setTrips] = useState<UserTrip[]>([]);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    
    const fetchTrips = async () => {
      try {
        setLoading(true);
        const { trips } = await api.getUserTrips();
        if (isMounted) {
          setTrips(trips);
        }
      } catch (error: any) {
        if (isMounted) {
          console.error('Failed to load trips:', error);
          toast.error('Failed to load trips');
          if (error.response?.status === 401) {
            // Unauthorized, redirect to login
            navigate('/login');
          }
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };
    
    fetchTrips();
    
    return () => {
      isMounted = false;
    };
  }, [navigate]);

  const handleLogout = async () => {
    try {
      await api.logout();
      navigate('/login');
    } catch (error) {
      toast.error('Failed to logout');
    }
  };

  const copyGroupCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const createNewTrip = () => {
    navigate('/');
  };

  return (
    <div className="min-h-screen pt-20 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-white">
            My 
            <span className="bg-gradient-to-r from-primary-400 to-accent-cyan bg-clip-text text-transparent">
              {" "}Trips
            </span>
          </h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto mb-6">
            Manage all your group trips in one place
          </p>

          {/* Action Buttons */}
          <div className="flex flex-wrap justify-center gap-4 mb-8">
            <motion.button
              onClick={createNewTrip}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="btn-primary flex items-center space-x-2"
            >
              <Plus className="w-5 h-5" />
              <span>Create New Trip</span>
            </motion.button>

            <motion.button
              onClick={handleLogout}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="btn-secondary flex items-center space-x-2"
            >
              <LogOut className="w-5 h-5" />
              <span>Logout</span>
            </motion.button>
          </div>
        </motion.div>

        {/* Trips Grid */}
        {loading ? (
          <div className="text-center py-12">
            <div className="w-12 h-12 border-4 border-primary-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-400">Loading your trips...</p>
          </div>
        ) : trips.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12 bg-dark-700 rounded-xl border border-dark-600"
          >
            <MapPin className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No trips yet</h3>
            <p className="text-gray-400 mb-6">Create your first trip to get started!</p>
            <motion.button
              onClick={createNewTrip}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="btn-primary flex items-center space-x-2 mx-auto"
            >
              <Plus className="w-5 h-5" />
              <span>Create New Trip</span>
            </motion.button>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {trips.map((trip, index) => (
              <motion.div
                key={trip.groupCode}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className="bg-dark-700 rounded-xl p-6 border border-dark-600 hover:border-primary-500/30 transition-colors"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <Users className="w-5 h-5 text-primary-400" />
                    <span className="text-gray-400">{trip.memberCount} members</span>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm ${
                    trip.tripStatus === 'planned' 
                      ? 'bg-accent-emerald/20 text-accent-emerald' 
                      : 'bg-accent-amber/20 text-accent-amber'
                  }`}>
                    {trip.tripStatus === 'planned' ? 'Planned' : 'Planning'}
                  </span>
                </div>

                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-400">Group Code:</span>
                    <button
                      onClick={() => copyGroupCode(trip.groupCode)}
                      className="text-gray-400 hover:text-white transition-colors"
                      title="Copy group code"
                    >
                      {copiedCode === trip.groupCode ? (
                        <Check className="w-4 h-4" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                  <code className="block w-full px-3 py-2 bg-dark-800 rounded-lg text-primary-400 font-mono text-sm">
                    {trip.groupCode}
                  </code>
                </div>

                <div className="flex items-center justify-between text-sm text-gray-400 mb-4">
                  <div className="flex items-center space-x-1">
                    <Calendar className="w-4 h-4" />
                    <span>Joined {new Date(trip.joinedAt).toLocaleDateString()}</span>
                  </div>
                  <span className="capitalize">{trip.role}</span>
                </div>

                <motion.button
                  onClick={() => navigate(`/dashboard?group_code=${trip.groupCode}`)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full btn-secondary py-2"
                >
                  View Details
                </motion.button>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TripsDashboardPage; 