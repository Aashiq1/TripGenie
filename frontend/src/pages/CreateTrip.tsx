import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Plane, 
  Users, 
  MapPin, 
  Calendar, 
  DollarSign, 
  ArrowRight, 
  ArrowLeft,
  Check,
  Copy,
  Share,
  User
} from 'lucide-react'
import { useAuthStore } from '../stores/authStore'

interface TripFormData {
  tripName: string
  destinations: string[]
  departureDate: string
  returnDate: string
  budget: string
  groupSize: number
  accommodation: 'budget' | 'standard' | 'luxury'
  description: string
}

export function CreateTrip() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(0)
  const [isCreating, setIsCreating] = useState(false)
  const [createdTrip, setCreatedTrip] = useState<{ groupCode: string } | null>(null)
  const [formData, setFormData] = useState<TripFormData>({
    tripName: '',
    destinations: ['', '', ''],
    departureDate: '',
    returnDate: '',
    budget: '',
    groupSize: 2,
    accommodation: 'standard',
    description: ''
  })

  const steps = [
    {
      title: 'Basic Info',
      description: 'Tell us about your trip',
      icon: MapPin
    },
    {
      title: 'Travel Details',
      description: 'When and where',
      icon: Calendar
    },
    {
      title: 'Group & Budget',
      description: 'Size and spending',
      icon: Users
    },
    {
      title: 'Review',
      description: 'Confirm details',
      icon: Check
    }
  ]

  const updateFormData = (field: keyof TripFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const updateDestination = (index: number, value: string) => {
    setFormData(prev => {
      const newDestinations = [...prev.destinations]
      newDestinations[index] = value
      return { ...prev, destinations: newDestinations }
    })
  }

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSubmit = async () => {
    setIsCreating(true)
    try {
      const { tripAPI } = await import('../services/api')
      
      // Filter out empty destinations
      const validDestinations = formData.destinations.filter(dest => dest.trim() !== '')
      
      // Generate a unique group code based on first destination
      const firstDestination = validDestinations[0] || 'TRIP'
      const groupCode = `TRIP-${Math.random().toString(36).substr(2, 6).toUpperCase()}`
      
      // Create the trip data with ALL form data in the format expected by TripGroup model
      const tripData = {
        group_code: groupCode,
        destinations: validDestinations,
        creator_email: user?.email || '',
        created_at: new Date().toISOString(),
        trip_name: formData.tripName,
        departure_date: formData.departureDate,
        return_date: formData.returnDate,
        budget: parseInt(formData.budget) || null,
        group_size: formData.groupSize,
        accommodation: formData.accommodation,
        description: formData.description
      }
      
      const result = await tripAPI.createTrip(tripData)
      
      if (result.group && result.group.group_code) {
        setCreatedTrip({ groupCode: result.group.group_code })
      } else {
        // Fallback to the generated group code
        setCreatedTrip({ groupCode: groupCode })
      }
    } catch (error) {
      console.error('Failed to create trip:', error)
      // Show the actual error to help debug
      const errorMessage = error instanceof Error ? error.message : 
        (error as any)?.response?.data?.detail || 'Unknown error occurred'
      alert(`Failed to create trip: ${errorMessage}`)
      // Generate fallback group code for graceful degradation
      const validDestinations = formData.destinations.filter(dest => dest.trim() !== '')
      const firstDestination = validDestinations[0] || 'TRIP'
      const fallbackGroupCode = `TRIP-${Math.random().toString(36).substr(2, 6).toUpperCase()}`
      setCreatedTrip({ groupCode: fallbackGroupCode })
    } finally {
      setIsCreating(false)
    }
  }

  const copyGroupCode = () => {
    if (createdTrip) {
      navigator.clipboard.writeText(createdTrip.groupCode)
    }
  }

  const shareTrip = () => {
    if (createdTrip && navigator.share) {
      navigator.share({
        title: 'Join my trip!',
        text: `Join my group trip with code: ${createdTrip.groupCode}`,
        url: window.location.origin + '/join-trip'
      })
    }
  }

  if (createdTrip) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="max-w-md w-full"
        >
          <div className="card text-center">
            <div className="gradient-bg p-6 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-6">
              <Check className="h-10 w-10 text-white" />
            </div>
            
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Trip Created Successfully! 🎉
            </h1>
            
            <p className="text-gray-600 mb-6">
              Your group trip has been created. Share the code below with your friends!
            </p>
            
            <div className="bg-gray-50 p-4 rounded-lg mb-6">
              <p className="text-sm text-gray-600 mb-2">Group Code</p>
              <div className="flex items-center justify-center space-x-2">
                <span className="text-2xl font-bold text-primary-600 tracking-wider">
                  {createdTrip.groupCode}
                </span>
                <button
                  onClick={copyGroupCode}
                  className="p-2 text-gray-500 hover:text-primary-600 transition-colors"
                  title="Copy code"
                >
                  <Copy className="h-4 w-4" />
                </button>
              </div>
            </div>
            
            <div className="space-y-3">
              <button
                onClick={() => navigate(`/trip/${createdTrip.groupCode}/preferences`)}
                className="btn-primary w-full flex items-center justify-center space-x-2"
              >
                <User className="h-4 w-4" />
                <span>Add Your Preferences</span>
              </button>
              
              <button
                onClick={shareTrip}
                className="btn-secondary w-full flex items-center justify-center space-x-2"
              >
                <Share className="h-4 w-4" />
                <span>Share Trip Code</span>
              </button>
              
              <button
                onClick={() => navigate('/dashboard')}
                className="text-gray-500 hover:text-gray-700 text-sm font-medium"
              >
                Skip for now - Go to Dashboard
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-8"
        >
          <div className="gradient-bg p-4 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
            <Plane className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Create New Trip
          </h1>
          <p className="text-gray-600">
            Plan your next group adventure in just a few steps
          </p>
        </motion.div>

        {/* Progress Steps */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mb-8"
        >
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={index} className="flex items-center">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all ${
                  index <= currentStep 
                    ? 'bg-primary-600 border-primary-600 text-white' 
                    : 'bg-white border-gray-300 text-gray-500'
                }`}>
                  <step.icon className="h-5 w-5" />
                </div>
                {index < steps.length - 1 && (
                  <div className={`h-1 w-16 mx-2 transition-all ${
                    index < currentStep ? 'bg-primary-600' : 'bg-gray-300'
                  }`} />
                )}
              </div>
            ))}
          </div>
          <div className="mt-4 text-center">
            <h2 className="text-xl font-semibold text-gray-900">
              {steps[currentStep].title}
            </h2>
            <p className="text-gray-600">
              {steps[currentStep].description}
            </p>
          </div>
        </motion.div>

        {/* Form Steps */}
        <div className="card">
          <AnimatePresence mode="wait">
            {currentStep === 0 && (
              <motion.div
                key="step0"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="space-y-6"
              >
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Trip Name
                  </label>
                  <input
                    type="text"
                    value={formData.tripName}
                    onChange={(e) => updateFormData('tripName', e.target.value)}
                    placeholder="e.g., Summer Europe Adventure"
                    className="input-field"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Destinations (1-3 locations)
                  </label>
                  <div className="space-y-3">
                    {formData.destinations.map((destination, index) => (
                      <div key={index}>
                        <input
                          type="text"
                          value={destination}
                          onChange={(e) => updateDestination(index, e.target.value)}
                          placeholder={
                            index === 0 
                              ? "Primary destination (required)" 
                              : `Optional destination ${index + 1}`
                          }
                          className="input-field"
                          required={index === 0}
                        />
                      </div>
                    ))}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    Add 1-3 destinations for your trip. At least one is required.
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description (Optional)
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => updateFormData('description', e.target.value)}
                    placeholder="Tell your group what this trip is about..."
                    rows={4}
                    className="input-field"
                  />
                </div>
              </motion.div>
            )}

            {currentStep === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="space-y-6"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Departure Date
                    </label>
                    <input
                      type="date"
                      value={formData.departureDate}
                      onChange={(e) => updateFormData('departureDate', e.target.value)}
                      className="input-field"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Return Date
                    </label>
                    <input
                      type="date"
                      value={formData.returnDate}
                      onChange={(e) => updateFormData('returnDate', e.target.value)}
                      className="input-field"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Accommodation Preference
                  </label>
                  <div className="grid grid-cols-3 gap-4">
                    {[
                      { value: 'budget', label: 'Budget', desc: 'Hostels, basic hotels' },
                      { value: 'standard', label: 'Standard', desc: '3-4 star hotels' },
                      { value: 'luxury', label: 'Luxury', desc: '5 star hotels, resorts' }
                    ].map((option) => (
                      <button
                        key={option.value}
                        onClick={() => updateFormData('accommodation', option.value)}
                        className={`p-4 border-2 rounded-lg transition-all ${
                          formData.accommodation === option.value
                            ? 'border-primary-600 bg-primary-50'
                            : 'border-gray-300 hover:border-gray-400'
                        }`}
                      >
                        <div className="text-sm font-medium">{option.label}</div>
                        <div className="text-xs text-gray-500">{option.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {currentStep === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="space-y-6"
              >
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Expected Group Size
                  </label>
                  <div className="flex items-center space-x-4">
                    <button
                      onClick={() => updateFormData('groupSize', Math.max(1, formData.groupSize - 1))}
                      className="w-10 h-10 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50"
                    >
                      -
                    </button>
                    <span className="text-xl font-semibold w-12 text-center">
                      {formData.groupSize}
                    </span>
                    <button
                      onClick={() => updateFormData('groupSize', formData.groupSize + 1)}
                      className="w-10 h-10 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50"
                    >
                      +
                    </button>
                  </div>
                  <p className="text-sm text-gray-500 mt-2">
                    Including yourself ({formData.groupSize} people total)
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Budget per Person (USD)
                  </label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                    <input
                      type="number"
                      value={formData.budget}
                      onChange={(e) => updateFormData('budget', e.target.value)}
                      placeholder="1000"
                      className="input-field pl-10"
                    />
                  </div>
                  <p className="text-sm text-gray-500 mt-2">
                    Estimated budget for flights, accommodation, and activities
                  </p>
                </div>
              </motion.div>
            )}

            {currentStep === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="space-y-6"
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Review Your Trip Details
                </h3>
                
                <div className="bg-gray-50 rounded-lg p-6 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-gray-600">Trip Name</div>
                      <div className="font-medium">{formData.tripName}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Destinations</div>
                      <div className="font-medium">
                        {formData.destinations.filter(dest => dest.trim() !== '').join(', ') || 'None specified'}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Departure</div>
                      <div className="font-medium">
                        {new Date(formData.departureDate).toLocaleDateString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Return</div>
                      <div className="font-medium">
                        {new Date(formData.returnDate).toLocaleDateString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Group Size</div>
                      <div className="font-medium">{formData.groupSize} people</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Budget per Person</div>
                      <div className="font-medium">${formData.budget}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Accommodation</div>
                      <div className="font-medium capitalize">{formData.accommodation}</div>
                    </div>
                  </div>
                  
                  {formData.description && (
                    <div>
                      <div className="text-sm text-gray-600">Description</div>
                      <div className="font-medium">{formData.description}</div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Navigation Buttons */}
          <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
            <button
              onClick={handlePrevious}
              disabled={currentStep === 0}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
                currentStep === 0
                  ? 'text-gray-400 cursor-not-allowed'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Previous</span>
            </button>

            {currentStep < steps.length - 1 ? (
              <button
                onClick={handleNext}
                disabled={
                  (currentStep === 0 && (!formData.tripName || !formData.destinations[0].trim())) ||
                  (currentStep === 1 && (!formData.departureDate || !formData.returnDate))
                }
                className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>Next</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={isCreating}
                className="btn-primary flex items-center space-x-2 disabled:opacity-50"
              >
                {isCreating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                    <span>Creating...</span>
                  </>
                ) : (
                  <>
                    <Check className="h-4 w-4" />
                    <span>Create Trip</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
} 