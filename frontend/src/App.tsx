import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import HomePage from './components/pages/HomePage';
import JoinTripPage from './components/pages/JoinTripPage';
import GroupDashboard from './components/pages/GroupDashboard';
import TripPlanPage from './components/pages/TripPlanPage';
import Navbar from './components/common/Navbar';
import BackgroundEffects from './components/common/BackgroundEffects';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-dark-900 text-white relative overflow-hidden">
        {/* Background effects */}
        <BackgroundEffects />
        
        {/* Main content */}
        <div className="relative z-10">
          <Navbar />
          
          <main>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/join" element={<JoinTripPage />} />
              <Route path="/dashboard" element={<GroupDashboard />} />
              <Route path="/plan" element={<TripPlanPage />} />
            </Routes>
          </main>
        </div>

        {/* Toast notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#1e293b',
              color: '#fff',
              border: '1px solid #334155',
              borderRadius: '12px',
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#f43f5e',
                secondary: '#fff',
              },
            },
          }}
        />
      </div>
    </Router>
  );
}

export default App; 