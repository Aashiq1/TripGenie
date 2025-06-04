export interface Availability {
  dates: string[]; // Format: YYYY-MM-DD
}

export interface Budget {
  min: number;
  max: number;
}

export type Vibe = "relaxing" | "adventurous" | "party" | "culture";

export interface Preferences {
  vibe: Vibe[];
  interests: string[];
  departure_airports: string[];
  budget: Budget;
  trip_duration: number;
}

export interface UserInput {
  name: string;
  email: string;
  phone: string;
  preferences: Preferences;
  availability: Availability;
}

export interface GroupInput {
  users: UserInput[];
}

export interface TripPlan {
  best_dates: string[];
  available_users: string[];
  group_preferences: {
    common_vibes: Vibe[];
    common_interests: string[];
    budget_range: Budget;
    duration: number;
  };
  recommendations: {
    destinations: string[];
    activities: string[];
  };
}

// Form state types for multi-step form
export interface FormState {
  currentStep: number;
  userData: Partial<UserInput>;
  isLoading: boolean;
  errors: Record<string, string>;
}

// API response types
export interface APIResponse<T = any> {
  status: string;
  data?: T;
  message?: string;
  error?: string;
} 