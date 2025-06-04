import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface AvailabilityStepProps {
  register: any;
  errors: any;
  watch: any;
  setValue: any;
}

const AvailabilityStep: React.FC<AvailabilityStepProps> = ({ register, errors, watch, setValue }) => {
  const [selectedDates, setSelectedDates] = useState<string[]>([]);
  const [customDates, setCustomDates] = useState<string>('');

  // Generate some preset date options for the next few months
  const generatePresetDates = () => {
    const dates = [];
    const today = new Date();
    
    // Generate dates for the next 8 weeks
    for (let i = 7; i <= 60; i += 7) { // Every week for next 8 weeks
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      dates.push({
        date: date.toISOString().split('T')[0],
        label: date.toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric',
          weekday: 'short'
        })
      });
    }
    return dates;
  };

  const presetDates = generatePresetDates();

  // Set default dates (next 3 weekends)
  useEffect(() => {
    if (presetDates.length > 0) {
      const defaultDates = presetDates.slice(0, 3).map(d => d.date);
      setSelectedDates(defaultDates);
      setValue('availability.dates', defaultDates);
    }
  }, [setValue]);

  // Update form when dates change
  useEffect(() => {
    setValue('availability.dates', selectedDates);
  }, [selectedDates, setValue]);

  const toggleDate = (date: string) => {
    if (selectedDates.includes(date)) {
      setSelectedDates(selectedDates.filter(d => d !== date));
    } else {
      setSelectedDates([...selectedDates, date]);
    }
  };

  const addCustomDates = () => {
    if (!customDates.trim()) return;
    
    const dates = customDates.split(',').map(d => d.trim()).filter(d => {
      const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
      return dateRegex.test(d);
    });
    
    const newDates = Array.from(new Set([...selectedDates, ...dates]));
    setSelectedDates(newDates);
    setCustomDates('');
  };

  return (
    <div className="space-y-8">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">When Can You Travel?</h2>
        <p className="text-gray-400">Select your available dates or add custom ones</p>
      </div>

      {/* Preset Date Options */}
      <div className="space-y-4">
        <label className="text-sm font-medium text-gray-300">
          Quick Select (Click to toggle)
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {presetDates.map((preset) => (
            <motion.button
              key={preset.date}
              type="button"
              onClick={() => toggleDate(preset.date)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className={`
                p-3 rounded-xl text-center transition-all duration-200 border-2
                ${selectedDates.includes(preset.date)
                  ? 'bg-primary-600 border-primary-500 text-white'
                  : 'bg-dark-700 border-dark-600 text-gray-300 hover:border-primary-600'
                }
              `}
            >
              <div className="text-sm font-medium">{preset.label}</div>
              <div className="text-xs text-gray-400">{preset.date}</div>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Custom Date Input */}
      <div className="space-y-4">
        <label className="text-sm font-medium text-gray-300">
          Add Custom Dates (Optional)
        </label>
        <div className="flex space-x-2">
          <input
            type="text"
            value={customDates}
            onChange={(e) => setCustomDates(e.target.value)}
            className="input-field flex-1"
            placeholder="2024-07-15, 2024-07-20, 2024-08-01"
          />
          <motion.button
            type="button"
            onClick={addCustomDates}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="btn-secondary px-4"
          >
            Add
          </motion.button>
        </div>
        <p className="text-sm text-gray-400">
          Format: YYYY-MM-DD, separated by commas
        </p>
      </div>

      {/* Selected Dates Display */}
      {selectedDates.length > 0 && (
        <div className="space-y-4">
          <label className="text-sm font-medium text-gray-300">
            Selected Dates ({selectedDates.length})
          </label>
          <div className="flex flex-wrap gap-2">
            {selectedDates.sort().map((date) => (
              <motion.span
                key={date}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="inline-flex items-center px-3 py-1 bg-accent-emerald/20 text-accent-emerald rounded-lg text-sm"
              >
                {date}
                <button
                  type="button"
                  onClick={() => toggleDate(date)}
                  className="ml-2 text-accent-emerald hover:text-white"
                >
                  ×
                </button>
              </motion.span>
            ))}
          </div>
        </div>
      )}

      {selectedDates.length === 0 && (
        <div className="text-center py-4">
          <p className="text-gray-400">Please select at least one available date</p>
        </div>
      )}

      {/* Hidden input for form registration */}
      <input 
        type="hidden" 
        {...register('availability.dates', { 
          required: 'Please select at least one available date'
        })} 
      />
      
      {errors.availability?.dates && (
        <p className="text-red-400 text-sm">
          {errors.availability.dates.message}
        </p>
      )}
    </div>
  );
};

export default AvailabilityStep; 