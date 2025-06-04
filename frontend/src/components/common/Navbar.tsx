import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Compass, Users, Map, Sparkles } from 'lucide-react';

const Navbar: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Home', icon: Compass },
    { path: '/join', label: 'Join Trip', icon: Users },
    { path: '/dashboard', label: 'Dashboard', icon: Map },
    { path: '/plan', label: 'Plan', icon: Sparkles },
  ];

  return (
    <nav className="relative z-50">
      <div className="glass-dark border-b border-glass-white-10 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-2 group">
              <motion.div
                whileHover={{ rotate: 180 }}
                transition={{ duration: 0.3 }}
                className="p-2 bg-gradient-primary rounded-xl shadow-glow"
              >
                <Compass className="w-6 h-6 text-white" />
              </motion.div>
              <span className="text-2xl font-bold bg-gradient-to-r from-primary-400 to-accent-cyan bg-clip-text text-transparent">
                TripGenie
              </span>
            </Link>

            {/* Navigation Links */}
            <div className="hidden md:block">
              <div className="flex items-center space-x-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className="relative group"
                    >
                      <motion.div
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className={`
                          flex items-center space-x-2 px-4 py-2 rounded-xl transition-all duration-200
                          ${isActive 
                            ? 'bg-primary-500/20 text-primary-400 shadow-glow' 
                            : 'text-gray-300 hover:text-white hover:bg-glass-white-10'
                          }
                        `}
                      >
                        <Icon className="w-5 h-5" />
                        <span className="font-medium">{item.label}</span>
                      </motion.div>
                      
                      {/* Active indicator */}
                      {isActive && (
                        <motion.div
                          layoutId="activeTab"
                          className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-primary rounded-full"
                          initial={false}
                          transition={{ type: "spring", stiffness: 300, damping: 30 }}
                        />
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden">
              <motion.button
                whileTap={{ scale: 0.95 }}
                className="p-2 rounded-xl bg-glass-white-10 hover:bg-glass-white-20 transition-all duration-200"
              >
                <div className="space-y-1">
                  <div className="w-5 h-0.5 bg-white rounded-full"></div>
                  <div className="w-5 h-0.5 bg-white rounded-full"></div>
                  <div className="w-5 h-0.5 bg-white rounded-full"></div>
                </div>
              </motion.button>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      <div className="md:hidden glass-dark border-b border-glass-white-10">
        <div className="px-2 pt-2 pb-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex items-center space-x-3 px-3 py-2 rounded-xl transition-all duration-200
                  ${isActive 
                    ? 'bg-primary-500/20 text-primary-400' 
                    : 'text-gray-300 hover:text-white hover:bg-glass-white-10'
                  }
                `}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 