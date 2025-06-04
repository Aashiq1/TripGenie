import axios from 'axios';
import { UserInput, GroupInput, TripPlan, APIResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
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
  getGroup: async (): Promise<GroupInput> => {
    const response = await apiClient.get('/inputs/group');
    return response.data;
  },

  // Plan trip
  planTrip: async (): Promise<TripPlan> => {
    const response = await apiClient.post('/inputs/plan');
    return response.data;
  },
};

export default api; 