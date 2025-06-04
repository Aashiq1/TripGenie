import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Users, MapPin, Calendar, DollarSign, User } from 'lucide-react';
import { GroupInput, UserInput } from '../../types';
import { api } from '../../services/api';

const GroupDashboard: React.FC = () => {
  const [groupData, setGroupData] = useState<GroupInput | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchGroupData = async () => {
      try {
        const data = await api.getGroup();
        setGroupData(data);
      } catch (error) {
        console.error('Failed to fetch group data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchGroupData();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen pt-20 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading group data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-20 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-white">
            Group 
            <span className="bg-gradient-to-r from-primary-400 to-accent-cyan bg-clip-text text-transparent">
              {" "}Dashboard
            </span>
          </h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            See who's joined the trip and their preferences
          </p>
        </motion.div>

        {/* Group Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="card text-center"
          >
            <Users className="w-8 h-8 text-primary-400 mx-auto mb-2" />
            <h3 className="text-2xl font-bold text-white">{groupData?.users?.length || 0}</h3>
            <p className="text-gray-400">Trip Members</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="card text-center"
          >
            <Calendar className="w-8 h-8 text-accent-cyan mx-auto mb-2" />
            <h3 className="text-2xl font-bold text-white">
              {groupData?.users?.reduce((total, user) => total + (user.availability?.dates?.length || 0), 0) || 0}
            </h3>
            <p className="text-gray-400">Available Dates</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="card text-center"
          >
            <DollarSign className="w-8 h-8 text-accent-amber mx-auto mb-2" />
            <h3 className="text-2xl font-bold text-white">
              ${Math.min(...(groupData?.users?.map(u => u.preferences?.budget?.min) || [0]))} - 
              ${Math.max(...(groupData?.users?.map(u => u.preferences?.budget?.max) || [0]))}
            </h3>
            <p className="text-gray-400">Budget Range</p>
          </motion.div>
        </div>

        {/* Members List */}
        {groupData?.users && groupData.users.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {groupData.users.map((user: UserInput, index: number) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="card"
              >
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-gradient-primary rounded-full flex items-center justify-center">
                    <User className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-white mb-1">{user.name}</h3>
                    <p className="text-gray-400 text-sm mb-4">{user.email}</p>
                    
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-400">Budget:</span>
                        <span className="text-white ml-2">
                          ${user.preferences?.budget?.min} - ${user.preferences?.budget?.max}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">Duration:</span>
                        <span className="text-white ml-2">{user.preferences?.trip_duration} days</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Vibe:</span>
                        <span className="text-white ml-2">
                          {user.preferences?.vibe?.join(', ') || 'None'}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">Dates:</span>
                        <span className="text-white ml-2">
                          {user.availability?.dates?.length || 0} available
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center py-12"
          >
            <Users className="w-16 h-16 text-gray-500 mx-auto mb-4" />
            <h3 className="text-2xl font-semibold text-white mb-2">No members yet</h3>
            <p className="text-gray-400 mb-6">Be the first to join this trip!</p>
            <a href="/join" className="btn-primary">
              Join Trip
            </a>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default GroupDashboard; 