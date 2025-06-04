import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface PreferencesStepProps {
  register: any;
  errors: any;
  watch: any;
  setValue: any;
}

const PreferencesStep: React.FC<PreferencesStepProps> = ({ register, errors, watch, setValue }) => {
  const [selectedVibes, setSelectedVibes] = useState<string[]>(['relaxing']);
  const [selectedInterests, setSelectedInterests] = useState<string[]>(['food']);
  const [selectedAirports, setSelectedAirports] = useState<string[]>(['LAX']);

  const vibeOptions = [
    { id: 'relaxing', label: 'Relaxing', emoji: '🧘' },
    { id: 'adventurous', label: 'Adventurous', emoji: '🏔️' },
    { id: 'party', label: 'Party', emoji: '🎉' },
    { id: 'culture', label: 'Culture', emoji: '🎭' }
  ];

  const interestOptions = [
    { id: 'food', label: 'Food & Dining', emoji: '🍽️' },
    { id: 'hiking', label: 'Hiking', emoji: '🥾' },
    { id: 'museums', label: 'Museums', emoji: '🏛️' },
    { id: 'nightlife', label: 'Nightlife', emoji: '🌃' },
    { id: 'nature', label: 'Nature', emoji: '🌿' },
    { id: 'shopping', label: 'Shopping', emoji: '🛍️' }
  ];

  const airportOptions = [
    { id: 'LAX', label: 'Los Angeles (LAX)' },
    { id: 'SFO', label: 'San Francisco (SFO)' },
    { id: 'SAN', label: 'San Diego (SAN)' },
    { id: 'SJC', label: 'San Jose (SJC)' }
  ];

  // Update form values when selections change
  useEffect(() => {
    setValue('preferences.vibe', selectedVibes);
    setValue('preferences.interests', selectedInterests);
    setValue('preferences.departure_airports', selectedAirports);
  }, [selectedVibes, selectedInterests, selectedAirports, setValue]);

  // Set initial default values immediately on mount
  useEffect(() => {
    setValue('preferences.budget.min', 300);
    setValue('preferences.budget.max', 800);
    setValue('preferences.trip_duration', 4);
  }, [setValue]);

  const toggleSelection = (item: string, selected: string[], setSelected: (items: string[]) => void) => {
    if (selected.includes(item)) {
      setSelected(selected.filter(i => i !== item));
    } else {
      setSelected([...selected, item]);
    }
  };

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
              min: { value: 100, message: 'Budget must be at least $100' }
            })}
            className="input-field w-full"
            placeholder="500"
            defaultValue="300"
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
              min: { value: 100, message: 'Budget must be at least $100' }
            })}
            className="input-field w-full"
            placeholder="2000"
            defaultValue="800"
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
            max: { value: 30, message: 'Duration must be less than 30 days' }
          })}
          className="input-field w-full"
          placeholder="7"
          defaultValue="4"
        />
        {errors.preferences?.trip_duration && (
          <p className="text-red-400 text-sm">
            {errors.preferences.trip_duration.message}
          </p>
        )}
      </div>

      {/* Trip Vibes */}
      <div className="space-y-4">
        <label className="text-sm font-medium text-gray-300">
          What's your vibe? (Select at least one)
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {vibeOptions.map((vibe) => (
            <motion.button
              key={vibe.id}
              type="button"
              onClick={() => toggleSelection(vibe.id, selectedVibes, setSelectedVibes)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className={`
                p-4 rounded-xl text-center transition-all duration-200 border-2
                ${selectedVibes.includes(vibe.id)
                  ? 'bg-primary-600 border-primary-500 text-white'
                  : 'bg-dark-700 border-dark-600 text-gray-300 hover:border-primary-600'
                }
              `}
            >
              <div className="text-2xl mb-2">{vibe.emoji}</div>
              <div className="text-sm font-medium">{vibe.label}</div>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Interests */}
      <div className="space-y-4">
        <label className="text-sm font-medium text-gray-300">
          What interests you? (Select at least one)
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {interestOptions.map((interest) => (
            <motion.button
              key={interest.id}
              type="button"
              onClick={() => toggleSelection(interest.id, selectedInterests, setSelectedInterests)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className={`
                p-3 rounded-xl text-center transition-all duration-200 border-2
                ${selectedInterests.includes(interest.id)
                  ? 'bg-accent-cyan/20 border-accent-cyan text-accent-cyan'
                  : 'bg-dark-700 border-dark-600 text-gray-300 hover:border-accent-cyan'
                }
              `}
            >
              <div className="text-lg mb-1">{interest.emoji}</div>
              <div className="text-sm">{interest.label}</div>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Departure Airports */}
      <div className="space-y-4">
        <label className="text-sm font-medium text-gray-300">
          Departure Airports (Select at least one)
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {airportOptions.map((airport) => (
            <motion.button
              key={airport.id}
              type="button"
              onClick={() => toggleSelection(airport.id, selectedAirports, setSelectedAirports)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`
                p-3 rounded-xl text-left transition-all duration-200 border-2
                ${selectedAirports.includes(airport.id)
                  ? 'bg-accent-emerald/20 border-accent-emerald text-accent-emerald'
                  : 'bg-dark-700 border-dark-600 text-gray-300 hover:border-accent-emerald'
                }
              `}
            >
              <div className="font-medium">{airport.label}</div>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Hidden inputs to register the values with react-hook-form */}
      <input type="hidden" {...register('preferences.vibe')} />
      <input type="hidden" {...register('preferences.interests')} />
      <input type="hidden" {...register('preferences.departure_airports')} />
    </div>
  );
};

export default PreferencesStep; 