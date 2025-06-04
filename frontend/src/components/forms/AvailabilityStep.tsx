import React from 'react';

interface AvailabilityStepProps {
  register: any;
  errors: any;
  watch: any;
  setValue: any;
}

const AvailabilityStep: React.FC<AvailabilityStepProps> = ({ register, errors, watch, setValue }) => {
  return (
    <div className="space-y-8">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Availability</h2>
        <p className="text-gray-400">When are you available to travel?</p>
      </div>

      <div className="space-y-4">
        <label className="text-sm font-medium text-gray-300">
          Available Dates (comma-separated, YYYY-MM-DD format)
        </label>
        <textarea
          {...register('availability.dates', { 
            required: 'Please provide your available dates',
            validate: (value: string) => {
              const dates = value.split(',').map(d => d.trim());
              return dates.every(date => {
                const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
                return dateRegex.test(date);
              }) || 'Please use YYYY-MM-DD format';
            }
          })}
          className="input-field w-full h-32"
          placeholder="2024-06-01, 2024-06-15, 2024-07-01"
        />
        {errors.availability?.dates && (
          <p className="text-red-400 text-sm">
            {errors.availability.dates.message}
          </p>
        )}
        
        <p className="text-sm text-gray-400">
          Example: 2024-06-01, 2024-06-15, 2024-07-01
        </p>
      </div>
    </div>
  );
};

export default AvailabilityStep; 