import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Calendar, Users, MapPin, DollarSign } from 'lucide-react';
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
            {/* Best Dates */}
            <div className="card">
              <div className="flex items-center space-x-3 mb-4">
                <Calendar className="w-6 h-6 text-accent-cyan" />
                <h2 className="text-2xl font-bold text-white">Best Travel Dates</h2>
              </div>
              <div className="flex flex-wrap gap-2">
                {tripPlan.best_dates?.map((date, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-accent-cyan/20 text-accent-cyan rounded-lg text-sm"
                  >
                    {date}
                  </span>
                ))}
              </div>
            </div>

            {/* Available Users */}
            <div className="card">
              <div className="flex items-center space-x-3 mb-4">
                <Users className="w-6 h-6 text-accent-emerald" />
                <h2 className="text-2xl font-bold text-white">Available Members</h2>
              </div>
              <div className="flex flex-wrap gap-2">
                {tripPlan.available_users?.map((user, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-accent-emerald/20 text-accent-emerald rounded-lg text-sm"
                  >
                    {user}
                  </span>
                ))}
              </div>
            </div>

            {/* Group Preferences */}
            <div className="card">
              <div className="flex items-center space-x-3 mb-4">
                <DollarSign className="w-6 h-6 text-accent-amber" />
                <h2 className="text-2xl font-bold text-white">Group Preferences</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">Budget Range</h3>
                  <p className="text-gray-300">
                    ${tripPlan.group_preferences?.budget_range?.min} - ${tripPlan.group_preferences?.budget_range?.max}
                  </p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">Duration</h3>
                  <p className="text-gray-300">{tripPlan.group_preferences?.duration} days</p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">Common Vibes</h3>
                  <div className="flex flex-wrap gap-1">
                    {tripPlan.group_preferences?.common_vibes?.map((vibe, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-primary-500/20 text-primary-400 rounded text-sm"
                      >
                        {vibe}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">Common Interests</h3>
                  <div className="flex flex-wrap gap-1">
                    {tripPlan.group_preferences?.common_interests?.map((interest, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-accent-purple/20 text-accent-purple rounded text-sm"
                      >
                        {interest}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendations */}
            {tripPlan.recommendations && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="card">
                  <div className="flex items-center space-x-3 mb-4">
                    <MapPin className="w-6 h-6 text-accent-rose" />
                    <h2 className="text-2xl font-bold text-white">Recommended Destinations</h2>
                  </div>
                  <div className="space-y-2">
                    {tripPlan.recommendations.destinations?.map((destination, index) => (
                      <div key={index} className="p-3 bg-dark-700 rounded-lg">
                        <span className="text-white">{destination}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="card">
                  <div className="flex items-center space-x-3 mb-4">
                    <Sparkles className="w-6 h-6 text-accent-indigo" />
                    <h2 className="text-2xl font-bold text-white">Recommended Activities</h2>
                  </div>
                  <div className="space-y-2">
                    {tripPlan.recommendations.activities?.map((activity, index) => (
                      <div key={index} className="p-3 bg-dark-700 rounded-lg">
                        <span className="text-white">{activity}</span>
                      </div>
                    ))}
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