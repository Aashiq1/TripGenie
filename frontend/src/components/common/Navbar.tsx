import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Compass, Users, Map, Sparkles, LogOut } from 'lucide-react';
import { api } from '../../services/api';
import { toast } from 'react-hot-toast';

const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const isAuthenticated = !!localStorage.getItem('auth_token');

  const handleLogout = async () => {
    try {
      // Get the token before clearing it
      const token = localStorage.getItem('auth_token');
      if (token) {
        // Try to call the logout endpoint with the token
        await api.logout();
      }
    } catch (error) {
      console.log('Backend logout failed, but continuing with frontend logout');
    } finally {
      // Clear the token and redirect after attempting backend logout
      localStorage.removeItem('auth_token');
      toast.success('Logged out successfully');
      navigate('/login');
    }
  };

  const navItems = isAuthenticated ? [
    { path: '/trips', label: 'My Trips', icon: Compass },
    { path: '/dashboard', label: 'Dashboard', icon: Map },
    { path: '/plan', label: 'Plan', icon: Sparkles },
  ] : [
    { path: '/', label: 'Home', icon: Compass },
    { path: '/join', label: 'Join Trip', icon: Users },
  ];

  return (
    <nav className="relative z-50">
      <div className="glass-dark border-b border-glass-white-10 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to={isAuthenticated ? "/trips" : "/"} className="flex items-center space-x-2 group">
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
            <div className="flex items-center space-x-4">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-primary-400/10 text-primary-400'
                        : 'text-gray-300 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}

              {/* Auth Buttons */}
              {isAuthenticated ? (
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-2 px-4 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-white/5 transition-colors"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Logout</span>
                </button>
              ) : (
                <>
                  <Link
                    to="/login"
                    className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                      location.pathname === '/login'
                        ? 'bg-primary-400/10 text-primary-400'
                        : 'text-gray-300 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <span>Login</span>
                  </Link>
                  <Link
                    to="/register"
                    className="btn-primary px-4 py-2 rounded-lg"
                  >
                    <span>Sign Up</span>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 