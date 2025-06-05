import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { 
  MapPin, 
  Users, 
  Calendar,
  Sparkles,
  ArrowRight,
  Plus,
  Link,
  Copy,
  Check
} from 'lucide-react';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [groupCode, setGroupCode] = useState('');
  const [newGroupCode, setNewGroupCode] = useState('');
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [copied, setCopied] = useState(false);

  const createGroup = () => {
    // Generate a simple group code (in production, this would be server-generated)
    const code = 'TRIP-' + Math.random().toString(36).substring(2, 8).toUpperCase();
    setNewGroupCode(code);
    setShowCreateGroup(true);
    localStorage.setItem('currentGroupCode', code);
  };

  const joinGroup = () => {
    if (groupCode.trim()) {
      localStorage.setItem('currentGroupCode', groupCode.trim());
      navigate('/join');
    }
  };

  const copyGroupCode = () => {
    navigator.clipboard.writeText(newGroupCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const proceedWithNewGroup = () => {
    navigate('/join');
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Hero Section */}
      <div className="relative z-10 pt-20 pb-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-white via-primary-200 to-accent-cyan bg-clip-text text-transparent">
              TripGenie
            </h1>
            <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto">
              AI-powered group trip planning that finds the perfect destination and dates for everyone
            </p>
            
            {/* Group Actions */}
            <div className="max-w-2xl mx-auto space-y-6">
              {!showCreateGroup ? (
                <>
                  {/* Create New Group */}
                  <motion.button
                    onClick={createGroup}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="w-full md:w-auto btn-primary text-lg px-8 py-4 flex items-center justify-center space-x-3"
                  >
                    <Plus className="w-6 h-6" />
                    <span>Create New Trip Group</span>
                  </motion.button>

                  <div className="flex items-center space-x-4">
                    <div className="flex-1 h-px bg-gray-600"></div>
                    <span className="text-gray-400 text-sm">OR</span>
                    <div className="flex-1 h-px bg-gray-600"></div>
                  </div>

                  {/* Join Existing Group */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-white">Join an Existing Group</h3>
                    <div className="flex space-x-3">
                      <input
                        type="text"
                        value={groupCode}
                        onChange={(e) => setGroupCode(e.target.value)}
                        placeholder="Enter group code (e.g., TRIP-ABC123)"
                        className="input-field flex-1"
                      />
                      <motion.button
                        onClick={joinGroup}
                        disabled={!groupCode.trim()}
                        whileHover={groupCode.trim() ? { scale: 1.05 } : {}}
                        whileTap={groupCode.trim() ? { scale: 0.95 } : {}}
                        className={`px-6 py-3 rounded-xl font-semibold transition-all duration-200 flex items-center space-x-2 ${
                          groupCode.trim() 
                            ? 'btn-secondary' 
                            : 'opacity-50 cursor-not-allowed bg-dark-700 text-gray-500'
                        }`}
                      >
                        <Link className="w-5 h-5" />
                        <span>Join</span>
                      </motion.button>
                    </div>
                  </div>
                </>
              ) : (
                /* New Group Created */
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="card text-center"
                >
                  <h3 className="text-2xl font-bold text-white mb-4">🎉 Group Created!</h3>
                  <p className="text-gray-300 mb-6">Share this code with your friends to invite them:</p>
                  
                  <div className="flex items-center space-x-3 mb-6 p-4 bg-dark-700 rounded-xl">
                    <code className="flex-1 text-2xl font-bold text-primary-400">{newGroupCode}</code>
                    <motion.button
                      onClick={copyGroupCode}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="btn-secondary p-2"
                    >
                      {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                    </motion.button>
                  </div>

                  <motion.button
                    onClick={proceedWithNewGroup}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="btn-primary text-lg px-8 py-3 flex items-center space-x-2 mx-auto"
                  >
                    <span>Start Planning</span>
                    <ArrowRight className="w-5 h-5" />
                  </motion.button>
                </motion.div>
              )}
            </div>
          </motion.div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="card text-center"
            >
              <Users className="w-12 h-12 text-primary-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Smart Group Coordination</h3>
              <p className="text-gray-400">
                Automatically finds dates when everyone is available and preferences that work for the whole group.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="card text-center"
            >
              <MapPin className="w-12 h-12 text-accent-cyan mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Perfect Destinations</h3>
              <p className="text-gray-400">
                AI analyzes your group's vibes and interests to recommend destinations you'll all love.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.6 }}
              className="card text-center"
            >
              <Sparkles className="w-12 h-12 text-accent-amber mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Effortless Planning</h3>
              <p className="text-gray-400">
                No more endless group chats. Get personalized itineraries with booking links in minutes.
              </p>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage; 