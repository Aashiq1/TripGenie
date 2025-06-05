import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Calendar, Users, MapPin, DollarSign, Star } from 'lucide-react';
import { TripPlan } from '../../types';
import { api } from '../../services/api';

const TripPlanPage: React.FC = () => {
  const [tripPlan, setTripPlan] = useState<TripPlan | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const generatePlan = async () => {
    setIsLoading(true);
    try {
      const plan = await api.planTrip();
      setTripPlan(plan);
      console.log('Trip plan received:', plan);
    } catch (error) {
      console.error('Failed to generate trip plan:', error);
    } finally {
      setIsLoading(false);
    }
  };

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
            Trip 
            <span className="bg-gradient-to-r from-primary-400 to-accent-cyan bg-clip-text text-transparent">
              {" "}Planner
            </span>
          </h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto mb-8">
            Generate the perfect trip plan based on everyone's preferences
          </p>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={generatePlan}
            disabled={isLoading}
            className="btn-primary text-lg px-8 py-4 flex items-center space-x-2 mx-auto"
          >
            {isLoading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Generating Plan...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                <span>Generate Trip Plan</span>
              </>
            )}
          </motion.button>
        </motion.div>

        {tripPlan && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="space-y-8"
          >
            {/* Best Date Ranges */}
            {tripPlan.best_date_ranges && tripPlan.best_date_ranges.length > 0 && (
              <div className="card">
                <div className="flex items-center space-x-3 mb-6">
                  <Calendar className="w-6 h-6 text-accent-cyan" />
                  <h2 className="text-2xl font-bold text-white">Best Travel Windows</h2>
                </div>
                <div className="space-y-4">
                  {tripPlan.best_date_ranges.map((range, index) => (
                    <div key={index} className="p-4 bg-dark-700 rounded-lg">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h3 className="text-lg font-semibold text-white">
                            {range.start_date} to {range.end_date}
                          </h3>
                          <p className="text-accent-cyan">
                            {range.user_count} {range.user_count === 1 ? 'person' : 'people'} available
                          </p>
                        </div>
                        <span className="px-2 py-1 bg-accent-cyan/20 text-accent-cyan rounded text-sm">
                          Option {index + 1}
                        </span>
                      </div>
                      
                      {range.destinations && range.destinations.length > 0 && (
                        <div>
                          <h4 className="text-white font-medium mb-2">Top Destinations:</h4>
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                            {range.destinations.slice(0, 3).map((dest, destIndex) => (
                              <div key={destIndex} className="flex items-center justify-between p-2 bg-dark-600 rounded">
                                <span className="text-white text-sm">{dest.name}</span>
                                <div className="flex items-center space-x-1">
                                  <Star className="w-3 h-3 text-accent-amber" />
                                  <span className="text-accent-amber text-xs">{dest.score.toFixed(1)}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Common Dates */}
            {tripPlan.common_dates && tripPlan.common_dates.length > 0 && (
              <div className="card">
                <div className="flex items-center space-x-3 mb-4">
                  <Users className="w-6 h-6 text-accent-emerald" />
                  <h2 className="text-2xl font-bold text-white">Dates Everyone Can Go</h2>
                </div>
                <div className="flex flex-wrap gap-2">
                  {tripPlan.common_dates.map((date, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-accent-emerald/20 text-accent-emerald rounded-lg text-sm"
                    >
                      {date}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Group Profile */}
            {tripPlan.group_profile && (
              <div className="card">
                <div className="flex items-center space-x-3 mb-4">
                  <DollarSign className="w-6 h-6 text-accent-amber" />
                  <h2 className="text-2xl font-bold text-white">Group Profile</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-2">Budget Range</h3>
                    <p className="text-gray-300">
                      ${tripPlan.group_profile.budget_min} - ${tripPlan.group_profile.budget_max}
                    </p>
                    <p className="text-sm text-gray-400">
                      Target: ${tripPlan.group_profile.budget_target}
                    </p>
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-2">Popular Vibes</h3>
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(tripPlan.group_profile.vibes || {})
                        .sort(([,a], [,b]) => b - a)
                        .slice(0, 3)
                        .map(([vibe, count]) => (
                        <span
                          key={vibe}
                          className="px-2 py-1 bg-primary-500/20 text-primary-400 rounded text-sm"
                        >
                          {vibe} ({count})
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  <div className="md:col-span-2">
                    <h3 className="text-lg font-semibold text-white mb-2">Popular Interests</h3>
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(tripPlan.group_profile.interests || {})
                        .sort(([,a], [,b]) => b - a)
                        .slice(0, 6)
                        .map(([interest, count]) => (
                        <span
                          key={interest}
                          className="px-2 py-1 bg-accent-purple/20 text-accent-purple rounded text-sm"
                        >
                          {interest} ({count})
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {!tripPlan && !isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center py-12"
          >
            <Sparkles className="w-16 h-16 text-gray-500 mx-auto mb-4" />
            <h3 className="text-2xl font-semibold text-white mb-2">No trip plan yet</h3>
            <p className="text-gray-400">Click the button above to generate your perfect trip plan!</p>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default TripPlanPage; 