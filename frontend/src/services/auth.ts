import { api } from './api';
import { LoginCredentials, RegisterCredentials, User, UserTrip } from '../types/auth';

class AuthService {
  private static instance: AuthService;
  private token: string | null = null;

  private constructor() {
    // Initialize token from localStorage
    this.token = localStorage.getItem('auth_token');
  }

  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  private setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  public getToken(): string | null {
    return this.token;
  }

  public isAuthenticated(): boolean {
    return !!this.token;
  }

  public async login(credentials: LoginCredentials): Promise<User> {
    const response = await api.login(credentials);
    this.setToken(response.token);
    return response.user;
  }

  public async register(credentials: RegisterCredentials): Promise<User> {
    const response = await api.register(credentials);
    this.setToken(response.token);
    return response.user;
  }

  public async logout(): Promise<void> {
    try {
      await api.logout();
    } finally {
      this.setToken(null);
    }
  }

  public async getCurrentUser(): Promise<User | null> {
    if (!this.token) return null;
    try {
      const response = await api.getCurrentUser();
      return response.user;
    } catch {
      this.setToken(null);
      return null;
    }
  }

  public async getUserTrips(): Promise<UserTrip[]> {
    const response = await api.getUserTrips();
    return response.trips;
  }
}

export const authService = AuthService.getInstance(); 