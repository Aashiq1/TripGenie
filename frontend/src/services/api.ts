import axios from 'axios';
import { UserInput, GroupInput, TripPlan, APIResponse } from '../types';
import { LoginCredentials, RegisterCredentials, User, UserTrip } from '../types/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for logging and auth token
apiClient.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const api = {
  // Health check
  ping: async (): Promise<{ message: string }> => {
    const response = await apiClient.get('/ping');
    return response.data;
  },

  // Submit user input
  submitUser: async (userData: UserInput): Promise<APIResponse<UserInput>> => {
    const response = await apiClient.post('/inputs/user', userData);
    return response.data;
  },

  // Get group data
  getGroup: async (groupCode?: string): Promise<GroupInput> => {
    const params = groupCode ? { group_code: groupCode } : {};
    const response = await apiClient.get('/inputs/group', { params });
    return response.data;
  },

  // Plan trip
  planTrip: async (groupCode?: string): Promise<TripPlan> => {
    const params = groupCode ? { group_code: groupCode } : {};
    const response = await apiClient.post('/inputs/plan', null, { params });
    return response.data;
  },

  // List all groups
  listGroups: async (): Promise<{ groups: Array<{ group_code: string; user_count: number; users: string[] }> }> => {
    const response = await apiClient.get('/inputs/groups');
    return response.data;
  },

  // Clear group data
  clearGroup: async (groupCode?: string): Promise<{ message: string }> => {
    const params = groupCode ? { group_code: groupCode } : {};
    const response = await apiClient.delete('/inputs/clear', { params });
    // Clear localStorage if the group code matches or if no group code is specified
    const storedGroupCode = localStorage.getItem('currentGroupCode');
    if (!groupCode || storedGroupCode === groupCode) {
      localStorage.removeItem('currentGroupCode');
    }
    return response.data;
  },

  // Clear current group from localStorage
  clearCurrentGroup: (): void => {
    localStorage.removeItem('currentGroupCode');
  },

  // Auth endpoints
  login: async (credentials: LoginCredentials): Promise<{ user: User; token: string }> => {
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);  // OAuth2 expects 'username' field
    formData.append('password', credentials.password);
    
    const response = await apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  register: async (credentials: RegisterCredentials): Promise<{ user: User; token: string }> => {
    const response = await apiClient.post('/auth/register', credentials);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
  },

  getCurrentUser: async (): Promise<{ user: User }> => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  getUserTrips: async (): Promise<{ trips: UserTrip[] }> => {
    const response = await apiClient.get('/auth/trips');
    return { trips: response.data };
  },
};

export default api; 