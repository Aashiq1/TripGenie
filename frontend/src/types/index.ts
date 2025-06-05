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

export interface Destination {
  name: string;
  score: number;
}

export interface DateRange {
  start_date: string;
  end_date: string;
  user_count: number;
  users: string[];
  destinations: Destination[];
}

export interface GroupProfile {
  vibes: { [key: string]: number };
  interests: { [key: string]: number };
  budget_target: number;
  budget_min: number;
  budget_max: number;
}

export interface TripPlan {
  best_date_ranges: DateRange[];
  date_to_users_count: { [key: string]: number };
  common_dates: string[];
  group_profile: GroupProfile;
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