import React from 'react';
import { motion } from 'framer-motion';
import { User, Mail, Phone } from 'lucide-react';

interface PersonalInfoStepProps {
  register: any;
  errors: any;
}

const PersonalInfoStep: React.FC<PersonalInfoStepProps> = ({ register, errors }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Personal Information</h2>
        <p className="text-gray-400">Let's start with the basics about you</p>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {/* Name Field */}
        <div className="space-y-2">
          <label className="flex items-center space-x-2 text-sm font-medium text-gray-300">
            <User className="w-4 h-4" />
            <span>Full Name</span>
          </label>
          <input
            type="text"
            {...register('name', { 
              required: 'Name is required',
              minLength: { value: 2, message: 'Name must be at least 2 characters' }
            })}
            className="input-field w-full"
            placeholder="Enter your full name"
          />
          {errors.name && (
            <motion.p 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-accent-rose text-sm"
            >
              {errors.name.message}
            </motion.p>
          )}
        </div>

        {/* Email Field */}
        <div className="space-y-2">
          <label className="flex items-center space-x-2 text-sm font-medium text-gray-300">
            <Mail className="w-4 h-4" />
            <span>Email Address</span>
          </label>
          <input
            type="email"
            {...register('email', { 
              required: 'Email is required',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Invalid email address'
              }
            })}
            className="input-field w-full"
            placeholder="Enter your email address"
          />
          {errors.email && (
            <motion.p 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-accent-rose text-sm"
            >
              {errors.email.message}
            </motion.p>
          )}
        </div>

        {/* Phone Field */}
        <div className="space-y-2">
          <label className="flex items-center space-x-2 text-sm font-medium text-gray-300">
            <Phone className="w-4 h-4" />
            <span>Phone Number</span>
          </label>
          <input
            type="tel"
            {...register('phone', { 
              required: 'Phone number is required',
              minLength: { value: 10, message: 'Phone number must be at least 10 digits' }
            })}
            className="input-field w-full"
            placeholder="Enter your phone number"
          />
          {errors.phone && (
            <motion.p 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-accent-rose text-sm"
            >
              {errors.phone.message}
            </motion.p>
          )}
        </div>
      </div>

      <div className="mt-8 p-4 glass rounded-xl border border-glass-white-10">
        <p className="text-sm text-gray-300 leading-relaxed">
          <span className="text-primary-400 font-semibold">Privacy Note:</span> Your information 
          is only shared with your trip group members to coordinate the perfect adventure together.
        </p>
      </div>
    </motion.div>
  );
};

export default PersonalInfoStep; 