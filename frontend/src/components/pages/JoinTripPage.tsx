import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { toast } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { 
  User, 
  Heart, 
  Calendar,
  ArrowRight,
  ArrowLeft,
  CheckCircle
} from 'lucide-react';
import { UserInput } from '../../types';
import { api } from '../../services/api';
import PersonalInfoStep from '../forms/PersonalInfoStep';
import PreferencesStep from '../forms/PreferencesStep';
import AvailabilityStep from '../forms/AvailabilityStep';
import ReviewStep from '../forms/ReviewStep';

const JoinTripPage: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  
  const { 
    register, 
    handleSubmit, 
    watch, 
    setValue, 
    formState: { errors },
    getValues
  } = useForm<UserInput>();

  const steps = [
    { id: 1, title: 'Personal Info', icon: User, description: 'Tell us about yourself' },
    { id: 2, title: 'Preferences', icon: Heart, description: 'What kind of trip do you want?' },
    { id: 3, title: 'Availability', icon: Calendar, description: 'When can you travel?' },
    { id: 4, title: 'Review', icon: CheckCircle, description: 'Confirm your details' },
  ];

  const onSubmit = async (data: UserInput) => {
    setIsLoading(true);
    try {
      await api.submitUser(data);
      toast.success('Successfully joined the trip! 🎉');
      navigate('/dashboard');
    } catch (error) {
      toast.error('Failed to submit your information. Please try again.');
      console.error('Submission error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const nextStep = () => {
    if (currentStep < steps.length) {
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
    const values = getValues();
    switch (currentStep) {
      case 1:
        return values.name && values.email && values.phone;
      case 2:
        return values.preferences?.vibe?.length > 0 && 
               values.preferences?.interests?.length > 0 &&
               values.preferences?.departure_airports?.length > 0 &&
               values.preferences?.budget?.min &&
               values.preferences?.budget?.max &&
               values.preferences?.trip_duration;
      case 3:
        return values.availability?.dates?.length > 0;
      case 4:
        return true;
      default:
        return false;
    }
  };

  return (
    <div className="min-h-screen pt-20 pb-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-white">
            Join the 
            <span className="bg-gradient-to-r from-primary-400 to-accent-cyan bg-clip-text text-transparent">
              {" "}Adventure
            </span>
          </h1>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Share your preferences and let us plan the perfect group trip for everyone.
          </p>
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