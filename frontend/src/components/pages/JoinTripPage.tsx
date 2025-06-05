import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowRight, 
  ArrowLeft, 
  CheckCircle,
  User,
  Heart,
  Calendar,
  FileText,
  Copy,
  Check
} from 'lucide-react';
import PersonalInfoStep from '../forms/PersonalInfoStep';
import PreferencesStep from '../forms/PreferencesStep';
import AvailabilityStep from '../forms/AvailabilityStep';
import ReviewStep from '../forms/ReviewStep';
import { api } from '../../services/api';
import { UserInput } from '../../types';

const steps = [
  { id: 1, title: 'Personal Info', description: 'Basic details', icon: User },
  { id: 2, title: 'Preferences', description: 'Trip vibes & budget', icon: Heart },
  { id: 3, title: 'Availability', description: 'When can you go?', icon: Calendar },
  { id: 4, title: 'Review', description: 'Confirm details', icon: FileText }
];

const JoinTripPage: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [groupCode, setGroupCode] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const navigate = useNavigate();

  const { register, handleSubmit, formState: { errors }, watch, setValue, getValues } = useForm<UserInput>();

  // Watch all form values to trigger re-renders when they change
  const watchedValues = watch();

  useEffect(() => {
    // Get group code from localStorage
    const storedGroupCode = localStorage.getItem('currentGroupCode');
    if (storedGroupCode) {
      setGroupCode(storedGroupCode);
    } else {
      // If no group code, redirect to home
      navigate('/');
    }
  }, [navigate]);

  // Set default form values
  useEffect(() => {
    // Set budget defaults
    setValue('preferences.budget.min', 300);
    setValue('preferences.budget.max', 800);
    setValue('preferences.trip_duration', 4);
    
    // Set default vibes, interests, airports
    setValue('preferences.vibe', ['relaxing']);
    setValue('preferences.interests', ['food']);
    setValue('preferences.departure_airports', ['LAX']);
    
    // Set default availability dates
    const today = new Date();
    const nextWeek = new Date(today);
    nextWeek.setDate(today.getDate() + 7);
    const twoWeeksLater = new Date(today);
    twoWeeksLater.setDate(today.getDate() + 14);
    
    const defaultDates = [
      nextWeek.toISOString().split('T')[0],
      twoWeeksLater.toISOString().split('T')[0]
    ];
    setValue('availability.dates', defaultDates);
  }, [setValue]);

  const copyGroupCode = () => {
    navigator.clipboard.writeText(groupCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const onSubmit = async (data: UserInput) => {
    setIsLoading(true);
    try {
      // Include group code in the submission
      const submissionData = {
        ...data,
        group_code: groupCode
      };
      
      await api.submitUser(submissionData);
      navigate('/dashboard');
    } catch (error) {
      console.error('Error submitting user input:', error);
      alert('There was an error submitting your information. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const nextStep = () => {
    if (currentStep < steps.length && canProceed()) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return <PersonalInfoStep register={register} errors={errors} />;
      case 2:
        return <PreferencesStep register={register} errors={errors} watch={watch} setValue={setValue} />;
      case 3:
        return <AvailabilityStep register={register} errors={errors} watch={watch} setValue={setValue} />;
      case 4:
        return <ReviewStep data={getValues()} />;
      default:
        return null;
    }
  };

  const canProceed = () => {
    const values = watchedValues;
    
    switch (currentStep) {
      case 1:
        // Only validate step 1 - personal information is required
        return !!(values.name && values.email && values.phone);
      case 2:
      case 3:
      case 4:
        // Steps 2-4 always allow proceeding since we have defaults
        return true;
      default:
        return false;
    }
  };

  return (
    <div className="min-h-screen pt-20 pb-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header with Group Code */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-white">
            Join the 
            <span className="bg-gradient-to-r from-primary-400 to-accent-cyan bg-clip-text text-transparent">
              {" "}Adventure
            </span>
          </h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto mb-6">
            Share your preferences and let us plan the perfect group trip for everyone.
          </p>
          
          {/* Group Code Display */}
          {groupCode && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="inline-flex items-center space-x-3 bg-dark-700 rounded-xl px-6 py-3 mb-4"
            >
              <span className="text-gray-300">Group Code:</span>
              <code className="text-primary-400 font-bold text-lg">{groupCode}</code>
              <motion.button
                onClick={copyGroupCode}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="text-gray-400 hover:text-white transition-colors"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              </motion.button>
            </motion.div>
          )}
        </motion.div>

        {/* Progress Steps */}
        <div className="mb-12">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isActive = currentStep === step.id;
              const isCompleted = currentStep > step.id;
              
              return (
                <React.Fragment key={step.id}>
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.4, delay: index * 0.1 }}
                    className="flex flex-col items-center relative"
                  >
                    <div className={`
                      w-16 h-16 rounded-full flex items-center justify-center mb-2 transition-all duration-300
                      ${isActive 
                        ? 'bg-gradient-primary shadow-glow scale-110' 
                        : isCompleted 
                          ? 'bg-accent-emerald shadow-lg' 
                          : 'bg-dark-700 border-2 border-dark-600'
                      }
                    `}>
                      <Icon className={`w-6 h-6 ${isActive || isCompleted ? 'text-white' : 'text-gray-400'}`} />
                    </div>
                    <div className="text-center">
                      <p className={`font-semibold text-sm ${isActive ? 'text-primary-400' : isCompleted ? 'text-accent-emerald' : 'text-gray-400'}`}>
                        {step.title}
                      </p>
                      <p className="text-xs text-gray-500 hidden sm:block">{step.description}</p>
                    </div>
                  </motion.div>
                  
                  {index < steps.length - 1 && (
                    <div className={`
                      flex-1 h-0.5 mx-4 transition-all duration-500
                      ${currentStep > step.id 
                        ? 'bg-gradient-to-r from-accent-emerald to-primary-500' 
                        : 'bg-dark-700'
                      }
                    `} />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {/* Form Content */}
        <form onSubmit={handleSubmit(onSubmit)}>
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.4 }}
            className="card mb-8"
          >
            <AnimatePresence mode="wait">
              {renderStepContent()}
            </AnimatePresence>
          </motion.div>

          {/* Navigation Buttons */}
          <div className="flex justify-between items-center">
            <motion.button
              type="button"
              onClick={prevStep}
              disabled={currentStep === 1}
              whileHover={currentStep > 1 ? { scale: 1.05 } : {}}
              whileTap={currentStep > 1 ? { scale: 0.95 } : {}}
              className={`
                flex items-center space-x-2 px-6 py-3 rounded-xl font-semibold transition-all duration-200
                ${currentStep > 1 
                  ? 'btn-secondary' 
                  : 'opacity-50 cursor-not-allowed bg-dark-700 text-gray-500'
                }
              `}
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Previous</span>
            </motion.button>

            {currentStep < steps.length ? (
              <motion.button
                type="button"
                onClick={nextStep}
                disabled={!canProceed()}
                whileHover={canProceed() ? { scale: 1.05 } : {}}
                whileTap={canProceed() ? { scale: 0.95 } : {}}
                className={`
                  flex items-center space-x-2 px-6 py-3 rounded-xl font-semibold transition-all duration-200
                  ${canProceed() 
                    ? 'btn-primary' 
                    : 'opacity-50 cursor-not-allowed bg-dark-700 text-gray-500'
                  }
                `}
              >
                <span>Next</span>
                <ArrowRight className="w-5 h-5" />
              </motion.button>
            ) : (
              <motion.button
                type="submit"
                disabled={!canProceed() || isLoading}
                whileHover={canProceed() && !isLoading ? { scale: 1.05 } : {}}
                whileTap={canProceed() && !isLoading ? { scale: 0.95 } : {}}
                className={`
                  flex items-center space-x-2 px-8 py-3 rounded-xl font-semibold transition-all duration-200
                  ${canProceed() && !isLoading
                    ? 'btn-primary' 
                    : 'opacity-50 cursor-not-allowed bg-dark-700 text-gray-500'
                  }
                `}
              >
                {isLoading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Joining...</span>
                  </>
                ) : (
                  <>
                    <span>Join Trip</span>
                    <CheckCircle className="w-5 h-5" />
                  </>
                )}
              </motion.button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

export default JoinTripPage; 