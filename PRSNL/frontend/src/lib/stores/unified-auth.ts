/**
 * Svelte store for unified authentication state management
 * Integrates with Keycloak + FusionAuth unified service
 */

import { writable, derived, type Readable } from 'svelte/store';
import { unifiedAuth, type AuthState, type AuthUser, type LoginOptions, type SignupOptions } from '../services/unified-auth';

// Auth state store
const authStateStore = writable<AuthState>({
  isAuthenticated: false,
  user: null,
  token: null,
  refreshToken: null,
  isLoading: false, // Start as not loading
  error: null,
  authSource: null
});

// Subscribe to auth service changes
unifiedAuth.subscribe((state) => {
  authStateStore.set(state);
});

// Derived stores for convenience
export const isAuthenticated = derived(authStateStore, ($auth) => $auth.isAuthenticated);
export const currentUser = derived(authStateStore, ($auth) => $auth.user);
export const authToken = derived(authStateStore, ($auth) => $auth.token);
export const isLoading = derived(authStateStore, ($auth) => $auth.isLoading);
export const authError = derived(authStateStore, ($auth) => $auth.error);
export const authSource = derived(authStateStore, ($auth) => $auth.authSource);

// User role checking
export const userRoles = derived(authStateStore, ($auth) => $auth.user?.roles || []);
export const isAdmin = derived(userRoles, ($roles) => 
  $roles.some(role => ['admin', 'realm-admin', 'prsnl-admin'].includes(role))
);
export const isPremium = derived(userRoles, ($roles) => 
  $roles.some(role => ['premium', 'enterprise'].includes(role))
);

// Auth actions
export const authActions = {
  /**
   * Login with various options
   */
  async login(options: LoginOptions = {}) {
    try {
      await unifiedAuth.login(options);
    } catch (error) {
      console.error('Login action failed:', error);
      throw error;
    }
  },

  /**
   * Login with specific provider
   */
  async loginWithKeycloak(socialProvider?: 'google' | 'github' | 'microsoft') {
    return this.login({ 
      provider: 'keycloak', 
      socialProvider 
    });
  },

  async loginWithFusionAuth(socialProvider?: 'google' | 'github' | 'microsoft') {
    return this.login({ 
      provider: 'fusionauth', 
      socialProvider 
    });
  },

  async loginWithGoogle() {
    return this.login({ 
      provider: 'keycloak', 
      socialProvider: 'google' 
    });
  },

  async loginWithGitHub() {
    return this.login({ 
      provider: 'keycloak', 
      socialProvider: 'github' 
    });
  },

  async loginWithMicrosoft() {
    return this.login({ 
      provider: 'keycloak', 
      socialProvider: 'microsoft' 
    });
  },

  /**
   * Sign up new users
   */
  async signup(options: SignupOptions) {
    try {
      await unifiedAuth.signup(options);
    } catch (error) {
      console.error('Signup action failed:', error);
      throw error;
    }
  },

  /**
   * Sign up with FusionAuth (recommended for new users)
   */
  async signupWithFusionAuth() {
    return this.signup({ provider: 'fusionauth' });
  },

  /**
   * Sign up with PRSNL backend (for custom registration)
   */
  async signupWithPRSNL(userData: { firstName?: string; lastName?: string; email: string; password: string }) {
    return this.signup({ 
      provider: 'prsnl', 
      userData 
    });
  },

  /**
   * Login with PRSNL backend
   */
  async loginWithPRSNL(credentials: { email: string; password: string }) {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(credentials)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Incorrect email or password');
      }

      const data = await response.json();
      
      // Update auth state with the response
      unifiedAuth.updateState({
        isAuthenticated: true,
        user: unifiedAuth.normalizeUser(data.user, 'prsnl'),
        token: data.access_token,
        refreshToken: data.refresh_token,
        authSource: 'prsnl',
        isLoading: false,
        error: null
      });

      // Store tokens
      unifiedAuth.storeTokens(data.access_token, data.refresh_token, 'prsnl');
    } catch (error) {
      unifiedAuth.updateState({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Login failed' 
      });
      throw error;
    }
  },

  /**
   * Handle OAuth callbacks
   */
  async handleCallback(provider: 'keycloak' | 'fusionauth') {
    try {
      await unifiedAuth.handleCallback(provider);
    } catch (error) {
      console.error('Callback handling failed:', error);
      throw error;
    }
  },

  /**
   * Logout from all systems
   */
  async logout() {
    try {
      await unifiedAuth.logout();
    } catch (error) {
      console.error('Logout action failed:', error);
      throw error;
    }
  },

  /**
   * Refresh authentication token
   */
  async refreshToken(): Promise<boolean> {
    try {
      return await unifiedAuth.refreshToken();
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  },

  /**
   * Clear any auth errors
   */
  clearError() {
    authStateStore.update(state => ({ ...state, error: null }));
  },

  /**
   * Get current auth state
   */
  getState(): AuthState {
    return unifiedAuth.getState();
  }
};

// Utility functions for components
export const authUtils = {
  /**
   * Check if user has specific role
   */
  hasRole(role: string): Readable<boolean> {
    return derived(userRoles, ($roles) => $roles.includes(role));
  },

  /**
   * Check if user has any of the specified roles
   */
  hasAnyRole(roles: string[]): Readable<boolean> {
    return derived(userRoles, ($userRoles) => 
      roles.some(role => $userRoles.includes(role))
    );
  },

  /**
   * Get user display name
   */
  getDisplayName(): Readable<string> {
    return derived(currentUser, ($user) => {
      if (!$user) return 'Guest';
      return $user.name || $user.firstName || $user.email.split('@')[0] || 'User';
    });
  },

  /**
   * Get user initials for avatar
   */
  getUserInitials(): Readable<string> {
    return derived(currentUser, ($user) => {
      if (!$user) return 'G';
      
      if ($user.firstName && $user.lastName) {
        return `${$user.firstName.charAt(0)}${$user.lastName.charAt(0)}`.toUpperCase();
      }
      
      if ($user.name) {
        const nameParts = $user.name.split(' ');
        if (nameParts.length >= 2) {
          return `${nameParts[0].charAt(0)}${nameParts[1].charAt(0)}`.toUpperCase();
        }
        return nameParts[0].charAt(0).toUpperCase();
      }
      
      return $user.email.charAt(0).toUpperCase();
    });
  },

  /**
   * Format auth source for display
   */
  getAuthSourceDisplay(): Readable<string> {
    return derived(authSource, ($source) => {
      switch ($source) {
        case 'keycloak': return 'Single Sign-On';
        case 'fusionauth': return 'FusionAuth';
        case 'prsnl': return 'PRSNL Account';
        default: return 'Unknown';
      }
    });
  }
};

// Export the main store
export const authStore = authStateStore;

// Export everything for convenience
export {
  type AuthState,
  type AuthUser,
  type LoginOptions,
  type SignupOptions
} from '../services/unified-auth';