import React from 'react';
import { UserInput } from '../../types';

interface ReviewStepProps {
  data: Partial<UserInput>;
}

const ReviewStep: React.FC<ReviewStepProps> = ({ data }) => {
  return (
    <div className="space-y-8">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Review Your Information</h2>
        <p className="text-gray-400">Please review your details before submitting</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Personal Information */}
        <div className="card-glass p-6">
          <h3 className="text-xl font-semibold text-white mb-4">Personal Information</h3>
          <div className="space-y-3">
            <div>
              <span className="text-gray-400">Name:</span>
              <span className="text-white ml-2">{data.name || 'Not provided'}</span>
            </div>
            <div>
              <span className="text-gray-400">Email:</span>
              <span className="text-white ml-2">{data.email || 'Not provided'}</span>
            </div>
            <div>
              <span className="text-gray-400">Phone:</span>
              <span className="text-white ml-2">{data.phone || 'Not provided'}</span>
            </div>
          </div>
        </div>

        {/* Trip Preferences */}
        <div className="card-glass p-6">
          <h3 className="text-xl font-semibold text-white mb-4">Trip Preferences</h3>
          <div className="space-y-3">
            <div>
              <span className="text-gray-400">Budget:</span>
              <span className="text-white ml-2">
                ${data.preferences?.budget?.min || '0'} - ${data.preferences?.budget?.max || '0'}
              </span>
            </div>
            <div>
              <span className="text-gray-400">Duration:</span>
              <span className="text-white ml-2">{data.preferences?.trip_duration || 0} days</span>
            </div>
            <div>
              <span className="text-gray-400">Vibe:</span>
              <span className="text-white ml-2">
                {data.preferences?.vibe?.join(', ') || 'Not specified'}
              </span>
            </div>
          </div>
        </div>

        {/* Availability */}
        <div className="card-glass p-6 lg:col-span-2">
          <h3 className="text-xl font-semibold text-white mb-4">Availability</h3>
          <div>
            <span className="text-gray-400">Available Dates:</span>
            <div className="text-white mt-2">
              {data.availability?.dates?.join(', ') || 'No dates provided'}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-8 p-4 glass rounded-xl border border-glass-white-10">
        <p className="text-sm text-gray-300 text-center">
          By submitting, you agree to share this information with your trip group members.
        </p>
      </div>
    </div>
  );
};

export default ReviewStep; 