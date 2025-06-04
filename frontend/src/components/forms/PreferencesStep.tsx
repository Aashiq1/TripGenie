import React, { useState } from 'react';

interface PreferencesStepProps {
  register: any;
  errors: any;
  watch: any;
  setValue: any;
}

const PreferencesStep: React.FC<PreferencesStepProps> = ({ register, errors, watch, setValue }) => {
  return (
    <div className="space-y-8">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Trip Preferences</h2>
        <p className="text-gray-400">Tell us what kind of adventure you're dreaming of</p>
      </div>

      {/* Budget Range */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-300">
            Min Budget (USD)
          </label>
          <input
            type="number"
            {...register('preferences.budget.min', { 
              required: 'Minimum budget is required',
              min: { value: 0, message: 'Budget must be positive' }
            })}
            className="input-field w-full"
            placeholder="500"
          />
          {errors.preferences?.budget?.min && (
            <p className="text-red-400 text-sm">
              {errors.preferences.budget.min.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-300">
            Max Budget (USD)
          </label>
          <input
            type="number"
            {...register('preferences.budget.max', { 
              required: 'Maximum budget is required',
              min: { value: 0, message: 'Budget must be positive' }
            })}
            className="input-field w-full"
            placeholder="2000"
          />
          {errors.preferences?.budget?.max && (
            <p className="text-red-400 text-sm">
              {errors.preferences.budget.max.message}
            </p>
          )}
        </div>
      </div>

      {/* Trip Duration */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-300">
          Trip Duration (days)
        </label>
        <input
          type="number"
          {...register('preferences.trip_duration', { 
            required: 'Trip duration is required',
            min: { value: 1, message: 'Duration must be at least 1 day' },
            max: { value: 365, message: 'Duration must be less than a year' }
          })}
          className="input-field w-full"
          placeholder="7"
        />
        {errors.preferences?.trip_duration && (
          <p className="text-red-400 text-sm">
            {errors.preferences.trip_duration.message}
          </p>
        )}
      </div>

      {/* Hidden fields for other preferences */}
      <input
        type="hidden"
        {...register('preferences.vibe', { 
          value: ['relaxing'],
          required: 'Please select at least one vibe'
        })}
      />
      <input
        type="hidden"
        {...register('preferences.interests', { 
          value: ['Food & Dining'],
          required: 'Please select at least one interest'
        })}
      />
      <input
        type="hidden"
        {...register('preferences.departure_airports', { 
          value: ['LAX'],
          required: 'Please select at least one airport'
        })}
      />
    </div>
  );
};

export default PreferencesStep; 