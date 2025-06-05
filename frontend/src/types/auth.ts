export interface User {
  id: string;
  email: string;
  fullName: string;
  createdAt: string;
}

export interface UserTrip {
  groupCode: string;
  tripStatus: 'planning' | 'planned';
  memberCount: number;
  role: 'admin' | 'member';
  joinedAt: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials extends LoginCredentials {
  fullName: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface UserTripsResponse {
  trips: UserTrip[];
} 