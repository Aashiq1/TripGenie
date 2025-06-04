import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { 
  Users, 
  Calendar, 
  MapPin, 
  Star,
  RefreshCw,
  UserPlus,
  Copy,
  Check,
  Home
} from 'lucide-react';
import { api } from '../../services/api';
import { GroupInput, TripPlan } from '../../types';

const DashboardPage: React.FC = () => {
  const [groupData, setGroupData] = useState<GroupInput | null>(null);
  const [tripPlan, setTripPlan] = useState<TripPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [planLoading, setPlanLoading] = useState(false);
  const [groupCode, setGroupCode] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Get group code from localStorage
    const storedGroupCode = localStorage.getItem('currentGroupCode');
    if (storedGroupCode) {
      setGroupCode(storedGroupCode);
      fetchGroupData(storedGroupCode);
    } else {
      // If no group code, redirect to home
      navigate('/');
    }
  }, [navigate]);

  const fetchGroupData = async (code?: string) => {
    setLoading(true);
    try {
      const currentGroupCode = code || groupCode;
      const data = await api.getGroup(currentGroupCode);
      setGroupData(data);
    } catch (error) {
      console.error('Error fetching group data:', error);
      // If we can't fetch the group data, clear localStorage and redirect to home
      api.clearCurrentGroup();
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const planTrip = async () => {
    setPlanLoading(true);
    try {
      const plan = await api.planTrip(groupCode);
      setTripPlan(plan);
    } catch (error) {
      console.error('Error planning trip:', error);
      alert('Error planning trip. Please make sure you have at least one user in the group.');
    } finally {
      setPlanLoading(false);
    }
  };

  const copyGroupCode = () => {
    navigator.clipboard.writeText(groupCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const inviteMoreUsers = () => {
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
            Trip 
            <span className="bg-gradient-to-r from-primary-400 to-accent-cyan bg-clip-text text-transparent">
              {" "}Dashboard
            </span>
          </h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto mb-6">
            Track your group's progress and plan the perfect adventure together.
          </p>

          {/* Group Code Display */}
          {groupCode && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="inline-flex items-center space-x-3 bg-dark-700 rounded-xl px-6 py-3 mb-4"
            >
              <span className="text-gray-300">Group Code:</span>
              <code className="text-primary-400 font-bold text-lg">{groupCode}</code>
              <motion.button
                onClick={copyGroupCode}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="text-gray-400 hover:text-white transition-colors"
                title="Copy group code"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              </motion.button>
            </motion.div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-wrap justify-center gap-4 mb-8">
            <motion.button
              onClick={() => fetchGroupData()}
              disabled={loading}
              whileHover={!loading ? { scale: 1.05 } : {}}
              whileTap={!loading ? { scale: 0.95 } : {}}
              className="btn-secondary flex items-center space-x-2"
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh Data</span>
            </motion.button>

            <motion.button
              onClick={inviteMoreUsers}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="btn-secondary flex items-center space-x-2"
            >
              <UserPlus className="w-5 h-5" />
              <span>Invite More Users</span>
            </motion.button>

            <motion.button
              onClick={() => navigate('/')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="btn-secondary flex items-center space-x-2"
            >
              <Home className="w-5 h-5" />
              <span>Back to Home</span>
            </motion.button>
          </div>
        </motion.div>

        {/* Group Overview */}
        {groupData && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="card mb-8"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white flex items-center">
                <Users className="w-6 h-6 mr-2 text-primary-400" />
                Group Members ({groupData.users.length})
              </h2>
              
              {groupData.users.length >= 2 && (
                <motion.button
                  onClick={planTrip}
                  disabled={planLoading}
                  whileHover={!planLoading ? { scale: 1.05 } : {}}
                  whileTap={!planLoading ? { scale: 0.95 } : {}}
                  className="btn-primary flex items-center space-x-2"
                >
                  {planLoading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Planning...</span>
                    </>
                  ) : (
                    <>
                      <MapPin className="w-5 h-5" />
                      <span>Plan Our Trip</span>
                    </>
                  )}
                </motion.button>
              )}
            </div>

            {loading ? (
              <div className="text-center py-8">
                <div className="w-8 h-8 border-2 border-primary-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                <p className="text-gray-400">Loading group data...</p>
              </div>
            ) : groupData.users.length === 0 ? (
              <div className="text-center py-8">
                <Users className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400 text-lg mb-4">No members yet</p>
                <p className="text-gray-500">Share the group code with friends to get started!</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {groupData.users.map((user, index) => (
                  <motion.div
                    key={user.email}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.4, delay: index * 0.1 }}
                    className="bg-dark-700 rounded-xl p-4 border border-dark-600"
                  >
                    <h3 className="font-semibold text-white mb-2">{user.name}</h3>
                    <p className="text-gray-400 text-sm mb-3">{user.email}</p>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-500">Budget:</span>
                        <span className="text-accent-emerald">${user.preferences.budget.min} - ${user.preferences.budget.max}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-500">Duration:</span>
                        <span className="text-accent-cyan">{user.preferences.trip_duration} days</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-500">Available dates:</span>
                        <span className="text-accent-purple">{user.availability.dates.length} dates</span>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}

            {groupData.users.length === 1 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-6 p-4 bg-accent-amber/10 border border-accent-amber/20 rounded-xl"
              >
                <p className="text-accent-amber text-center">
                  <Calendar className="w-5 h-5 inline mr-2" />
                  Invite at least one more person to start planning your trip!
                </p>
              </motion.div>
            )}
          </motion.div>
        )}

        {/* Trip Plan */}
        {tripPlan && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="card"
          >
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
              <Star className="w-6 h-6 mr-2 text-accent-amber" />
              Your Perfect Trip Plan
            </h2>

            {/* Date Ranges */}
            {tripPlan.best_date_ranges && tripPlan.best_date_ranges.length > 0 && (
              <div className="mb-8">
                <h3 className="text-lg font-semibold text-white mb-4">Best Available Dates</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {tripPlan.best_date_ranges.map((dateRange: any, index: number) => (
                    <div key={index} className="bg-dark-700 rounded-xl p-4 border border-primary-500/30">
                      <div className="text-center">
                        <Calendar className="w-8 h-8 text-primary-400 mx-auto mb-2" />
                        <p className="text-white font-semibold">{dateRange.start_date} to {dateRange.end_date}</p>
                        <p className="text-gray-400 text-sm">{dateRange.available_users || 'All'} members available</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Destination Recommendations */}
            {(tripPlan as any).destination_scores && (tripPlan as any).destination_scores.length > 0 && (
              <div className="mb-8">
                <h3 className="text-lg font-semibold text-white mb-4">Recommended Destinations</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {(tripPlan as any).destination_scores.slice(0, 6).map((dest: any, index: number) => (
                    <div key={dest.destination} className="bg-dark-700 rounded-xl p-4 border border-accent-cyan/30">
                      <div className="text-center">
                        <MapPin className="w-8 h-8 text-accent-cyan mx-auto mb-2" />
                        <h4 className="text-white font-semibold">{dest.destination}</h4>
                        <div className="flex items-center justify-center mt-2">
                          <Star className="w-4 h-4 text-accent-amber mr-1" />
                          <span className="text-accent-amber font-semibold">{dest.score?.toFixed(1) || 'N/A'}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Group Profile */}
            {tripPlan.group_profile && (
              <div className="bg-dark-700 rounded-xl p-6 border border-dark-600">
                <h3 className="text-lg font-semibold text-white mb-4">Group Profile</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-accent-emerald font-semibold mb-2">Budget Range</h4>
                    <p className="text-white">${(tripPlan.group_profile as any).budget_range?.min || 'N/A'} - ${(tripPlan.group_profile as any).budget_range?.max || 'N/A'}</p>
                  </div>
                  <div>
                    <h4 className="text-accent-cyan font-semibold mb-2">Trip Duration</h4>
                    <p className="text-white">{(tripPlan.group_profile as any).trip_duration || 'N/A'} days</p>
                  </div>
                  <div>
                    <h4 className="text-accent-purple font-semibold mb-2">Group Vibes</h4>
                    <div className="flex flex-wrap gap-2">
                      {((tripPlan.group_profile as any).common_vibes || []).map((vibe: string) => (
                        <span key={vibe} className="px-3 py-1 bg-accent-purple/20 text-accent-purple rounded-lg text-sm">
                          {vibe}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-accent-amber font-semibold mb-2">Common Interests</h4>
                    <div className="flex flex-wrap gap-2">
                      {((tripPlan.group_profile as any).common_interests || []).map((interest: string) => (
                        <span key={interest} className="px-3 py-1 bg-accent-amber/20 text-accent-amber rounded-lg text-sm">
                          {interest}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage; 