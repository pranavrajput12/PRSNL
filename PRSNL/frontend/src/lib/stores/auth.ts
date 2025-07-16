/**
 * PRSNL Authentication Store
 * Manages user authentication state and JWT tokens
 */

import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';
import { addNotification } from './app.js';

// Auth Types
export interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  is_verified: boolean;
  user_type: string;
  onboarding_completed: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  user_type?: 'individual' | 'team' | 'enterprise';
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  emailVerificationSent: boolean;
  magicLinkSent: boolean;
}

// Auth API base URL
const API_BASE = browser ? window.location.origin : '';
const AUTH_API = `${API_BASE}/api/auth`;

// Token keys for localStorage
const ACCESS_TOKEN_KEY = 'prsnl-access-token';
const REFRESH_TOKEN_KEY = 'prsnl-refresh-token';
const USER_KEY = 'prsnl-user';

// Load stored auth data
function loadStoredAuth(): Partial<AuthState> {
  if (!browser) {
    return { user: null, accessToken: null, refreshToken: null, isAuthenticated: false };
  }

  try {
    const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    const userJson = localStorage.getItem(USER_KEY);
    
    if (accessToken && refreshToken && userJson) {
      const user = JSON.parse(userJson);
      return {
        user,
        accessToken,
        refreshToken,
        isAuthenticated: true
      };
    }
  } catch (e) {
    console.error('Failed to load stored auth data:', e);
    // Clear corrupted data
    clearStoredAuth();
  }

  return { user: null, accessToken: null, refreshToken: null, isAuthenticated: false };
}

// Clear stored auth data
function clearStoredAuth() {
  if (browser) {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
}

// Store stored auth data
function storeAuthData(tokens: AuthTokens) {
  if (browser) {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
    localStorage.setItem(USER_KEY, JSON.stringify(tokens.user));
  }
}

// Initial state
const initialState: AuthState = {
  ...loadStoredAuth(),
  isLoading: false,
  error: null,
  emailVerificationSent: false,
  magicLinkSent: false
} as AuthState;

// Create the auth store
export const authStore = writable<AuthState>(initialState);

// Derived stores
export const user = derived(authStore, ($auth) => $auth.user);
export const isAuthenticated = derived(authStore, ($auth) => $auth.isAuthenticated);
export const isLoading = derived(authStore, ($auth) => $auth.isLoading);
export const authError = derived(authStore, ($auth) => $auth.error);

// Helper function to make authenticated API calls
export function getAuthHeaders(): HeadersInit {
  const auth = get(authStore);
  if (auth.accessToken) {
    return {
      'Authorization': `Bearer ${auth.accessToken}`,
      'Content-Type': 'application/json'
    };
  }
  return { 'Content-Type': 'application/json' };
}

// Generic API call function
async function apiCall(endpoint: string, options: RequestInit = {}): Promise<any> {
  try {
    const response = await fetch(`${AUTH_API}${endpoint}`, {
      ...options,
      headers: {
        ...getAuthHeaders(),
        ...options.headers
      },
      credentials: 'include' // Include cookies for authentication
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Network error' }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API call failed: ${endpoint}`, error);
    throw error;
  }
}

// Auth Actions
export const authActions = {
  // Set loading state
  setLoading: (loading: boolean) => {
    authStore.update(state => ({ ...state, isLoading: loading, error: null }));
  },

  // Set error state
  setError: (error: string | null) => {
    authStore.update(state => ({ ...state, error, isLoading: false }));
  },

  // Register new user
  register: async (data: RegisterData): Promise<boolean> => {
    authActions.setLoading(true);
    
    try {
      const response = await apiCall('/register', {
        method: 'POST',
        body: JSON.stringify(data)
      });

      // Store auth data
      storeAuthData(response);
      
      authStore.update(state => ({
        ...state,
        user: response.user,
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        emailVerificationSent: !response.user.is_verified
      }));

      addNotification({
        type: 'success',
        message: response.user.is_verified 
          ? 'Account created successfully!'
          : 'Account created! Please check your email to verify your account.'
      });

      return true;
    } catch (error) {
      authActions.setError(error instanceof Error ? error.message : 'Registration failed');
      return false;
    }
  },

  // Login user
  login: async (credentials: LoginCredentials): Promise<boolean> => {
    authActions.setLoading(true);
    
    try {
      const response = await apiCall('/login', {
        method: 'POST',
        body: JSON.stringify(credentials)
      });

      // Store auth data
      storeAuthData(response);
      
      authStore.update(state => ({
        ...state,
        user: response.user,
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
        isAuthenticated: true,
        isLoading: false,
        error: null
      }));

      addNotification({
        type: 'success',
        message: 'Welcome back!'
      });

      return true;
    } catch (error) {
      authActions.setError(error instanceof Error ? error.message : 'Login failed');
      return false;
    }
  },

  // Logout user
  logout: async (): Promise<void> => {
    const auth = get(authStore);
    
    try {
      if (auth.accessToken) {
        await apiCall('/logout', { method: 'POST' });
      }
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      // Clear state regardless of API call result
      clearStoredAuth();
      authStore.set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        emailVerificationSent: false,
        magicLinkSent: false
      });

      addNotification({
        type: 'info',
        message: 'You have been logged out'
      });
    }
  },

  // Refresh access token
  refreshToken: async (): Promise<boolean> => {
    const auth = get(authStore);
    
    if (!auth.refreshToken) {
      return false;
    }

    try {
      const response = await apiCall('/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: auth.refreshToken })
      });

      // Update auth data
      storeAuthData(response);
      
      authStore.update(state => ({
        ...state,
        user: response.user,
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
        error: null
      }));

      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      // If refresh fails, logout user
      await authActions.logout();
      return false;
    }
  },

  // Send magic link
  sendMagicLink: async (email: string): Promise<boolean> => {
    authActions.setLoading(true);
    
    try {
      const response = await apiCall('/magic-link', {
        method: 'POST',
        body: JSON.stringify({ email })
      });

      authStore.update(state => ({
        ...state,
        isLoading: false,
        error: null,
        magicLinkSent: true
      }));

      addNotification({
        type: 'success',
        message: response.message || 'Magic link sent! Check your email.'
      });

      return true;
    } catch (error) {
      authActions.setError(error instanceof Error ? error.message : 'Failed to send magic link');
      return false;
    }
  },

  // Verify magic link
  verifyMagicLink: async (token: string): Promise<boolean> => {
    authActions.setLoading(true);
    
    try {
      const response = await apiCall('/magic-link/verify', {
        method: 'POST',
        body: JSON.stringify({ token })
      });

      // Store auth data
      storeAuthData(response);
      
      authStore.update(state => ({
        ...state,
        user: response.user,
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        magicLinkSent: false
      }));

      addNotification({
        type: 'success',
        message: 'Successfully signed in!'
      });

      return true;
    } catch (error) {
      authActions.setError(error instanceof Error ? error.message : 'Invalid magic link');
      return false;
    }
  },

  // Verify email
  verifyEmail: async (token: string): Promise<boolean> => {
    authActions.setLoading(true);
    
    try {
      const response = await apiCall('/verify-email', {
        method: 'POST',
        body: JSON.stringify({ token })
      });

      // Update user verification status
      authStore.update(state => ({
        ...state,
        user: state.user ? { ...state.user, is_verified: true } : null,
        isLoading: false,
        error: null,
        emailVerificationSent: false
      }));

      // Update stored user data
      const auth = get(authStore);
      if (auth.user) {
        localStorage.setItem(USER_KEY, JSON.stringify(auth.user));
      }

      addNotification({
        type: 'success',
        message: 'Email verified successfully!'
      });

      return true;
    } catch (error) {
      authActions.setError(error instanceof Error ? error.message : 'Email verification failed');
      return false;
    }
  },

  // Resend verification email
  resendVerification: async (): Promise<boolean> => {
    authActions.setLoading(true);
    
    try {
      const response = await apiCall('/resend-verification', {
        method: 'POST'
      });

      authStore.update(state => ({
        ...state,
        isLoading: false,
        error: null,
        emailVerificationSent: true
      }));

      addNotification({
        type: 'success',
        message: 'Verification email sent!'
      });

      return true;
    } catch (error) {
      authActions.setError(error instanceof Error ? error.message : 'Failed to send verification email');
      return false;
    }
  },

  // Get current user profile
  getCurrentUser: async (): Promise<User | null> => {
    try {
      const response = await apiCall('/me');
      
      authStore.update(state => ({
        ...state,
        user: response,
        error: null
      }));

      // Update stored user data
      if (browser) {
        localStorage.setItem(USER_KEY, JSON.stringify(response));
      }

      return response;
    } catch (error) {
      console.error('Failed to get current user:', error);
      // If getting user fails, the token might be invalid
      await authActions.logout();
      return null;
    }
  },

  // Clear auth error
  clearError: () => {
    authStore.update(state => ({ ...state, error: null }));
  },

  // Clear email verification sent flag
  clearEmailVerificationSent: () => {
    authStore.update(state => ({ ...state, emailVerificationSent: false }));
  },

  // Clear magic link sent flag
  clearMagicLinkSent: () => {
    authStore.update(state => ({ ...state, magicLinkSent: false }));
  }
};

// Create a promise that resolves when auth is initialized
let authInitialized: Promise<void>;
let authInitializedResolve: () => void;

if (browser) {
  authInitialized = new Promise((resolve) => {
    authInitializedResolve = resolve;
  });
  
  // Initialize auth state
  setTimeout(async () => {
    const auth = get(authStore);
    if (auth.isAuthenticated && auth.refreshToken) {
      // Try to refresh token on app start
      try {
        await authActions.refreshToken();
      } catch (error) {
        console.log('Token refresh on startup failed, using existing token');
      }
    }
    authInitializedResolve();
  }, 0);
} else {
  authInitialized = Promise.resolve();
}

// Export the initialization promise
export { authInitialized };