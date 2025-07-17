/**
 * Unified Authentication Service for Keycloak + FusionAuth Integration
 * Provides a single interface for both authentication systems
 */

import Keycloak from 'keycloak-js';
import type { FusionAuthClient } from '@fusionauth/typescript-client';

export interface AuthUser {
  id: string;
  email: string;
  name?: string;
  firstName?: string;
  lastName?: string;
  roles: string[];
  source: 'keycloak' | 'fusionauth' | 'prsnl';
  isEmailVerified: boolean;
  preferences?: Record<string, any>;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: AuthUser | null;
  token: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  error: string | null;
  authSource: 'keycloak' | 'fusionauth' | 'prsnl' | null;
}

export interface LoginOptions {
  provider?: 'keycloak' | 'fusionauth' | 'auto';
  redirectUri?: string;
  socialProvider?: 'google' | 'github' | 'microsoft';
}

export interface SignupOptions {
  provider?: 'fusionauth' | 'prsnl';
  userData?: {
    firstName?: string;
    lastName?: string;
    email: string;
    password?: string;
  };
}

class UnifiedAuthService {
  private keycloak: Keycloak | null = null;
  private fusionAuthConfig: any = null;
  private currentState: AuthState = {
    isAuthenticated: false,
    user: null,
    token: null,
    refreshToken: null,
    isLoading: false,
    error: null,
    authSource: null
  };

  private stateListeners: Array<(state: AuthState) => void> = [];

  constructor() {
    this.initializeServices();
  }

  /**
   * Initialize authentication services
   */
  private async initializeServices() {
    try {
      // Initialize Keycloak
      this.keycloak = new Keycloak({
        url: 'http://localhost:8080',
        realm: 'prsnl',
        clientId: 'prsnl-frontend'
      });

      // Initialize FusionAuth configuration
      this.fusionAuthConfig = {
        url: 'http://localhost:9011',
        clientId: '4218d574-603a-48b4-b980-39a0b73e4cff',
        clientSecret: '6f16bb7d-08f6-4008-a7ce-bef1cee8398b',
        applicationId: '4218d574-603a-48b4-b980-39a0b73e4cff',
        redirectUri: 'http://localhost:3004/auth/callback',
        scope: 'openid profile email offline_access'
      };

      // Try to restore existing session
      await this.restoreSession();
    } catch (error) {
      console.error('Failed to initialize auth services:', error);
      this.updateState({ error: 'Failed to initialize authentication' });
    }
  }

  /**
   * Try to restore existing authentication session
   */
  private async restoreSession() {
    this.updateState({ isLoading: true });

    try {
      // Check for stored tokens
      const storedToken = localStorage.getItem('prsnl_auth_token');
      const storedSource = localStorage.getItem('prsnl_auth_source') as 'keycloak' | 'fusionauth' | 'prsnl';

      if (storedToken && storedSource) {
        // Verify token with backend using /me endpoint
        const response = await fetch('/api/auth/me', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${storedToken}`
          }
        });

        if (response.ok) {
          const userData = await response.json();
          this.updateState({
            isAuthenticated: true,
            user: this.normalizeUser(userData, storedSource),
            token: storedToken,
            authSource: storedSource,
            isLoading: false,
            error: null
          });
          return;
        }
      }

      // Try Keycloak session restore
      if (this.keycloak) {
        const authenticated = await this.keycloak.init({
          onLoad: 'check-sso',
          silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
          checkLoginIframe: false
        });

        if (authenticated && this.keycloak.token) {
          const user = await this.getKeycloakUser();
          this.updateState({
            isAuthenticated: true,
            user,
            token: this.keycloak.token,
            refreshToken: this.keycloak.refreshToken || null,
            authSource: 'keycloak',
            isLoading: false,
            error: null
          });
          this.storeTokens(this.keycloak.token, this.keycloak.refreshToken, 'keycloak');
          return;
        }
      }

      // No valid session found
      this.updateState({ isLoading: false });
    } catch (error) {
      console.error('Session restore failed:', error);
      this.updateState({ 
        isLoading: false, 
        error: 'Failed to restore session' 
      });
    }
  }

  /**
   * Login with specified provider
   */
  async login(options: LoginOptions = {}): Promise<void> {
    this.updateState({ isLoading: true, error: null });

    try {
      const provider = options.provider || 'auto';

      if (provider === 'keycloak' || provider === 'auto') {
        await this.loginWithKeycloak(options);
      } else if (provider === 'fusionauth') {
        await this.loginWithFusionAuth(options);
      }
    } catch (error) {
      console.error('Login failed:', error);
      this.updateState({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Login failed' 
      });
    }
  }

  /**
   * Login with Keycloak
   */
  private async loginWithKeycloak(options: LoginOptions) {
    if (!this.keycloak) {
      throw new Error('Keycloak not initialized');
    }

    const loginOptions: any = {
      redirectUri: options.redirectUri || window.location.origin + '/auth/callback'
    };

    // Handle social providers
    if (options.socialProvider) {
      loginOptions.kc_idp_hint = options.socialProvider;
    }

    await this.keycloak.login(loginOptions);
  }

  /**
   * Login with FusionAuth
   */
  private async loginWithFusionAuth(options: LoginOptions) {
    const redirectUri = options.redirectUri || window.location.origin + '/auth/fusionauth/callback';
    
    let authUrl = `${this.fusionAuthConfig.url}/oauth2/authorize?` +
      `client_id=${this.fusionAuthConfig.clientId}&` +
      `response_type=code&` +
      `redirect_uri=${encodeURIComponent(redirectUri)}&` +
      `scope=openid email profile`;

    // Handle social providers
    if (options.socialProvider) {
      authUrl += `&idp_hint=${options.socialProvider}`;
    }

    window.location.href = authUrl;
  }

  /**
   * Sign up new user
   */
  async signup(options: SignupOptions): Promise<void> {
    this.updateState({ isLoading: true, error: null });

    try {
      const provider = options.provider || 'fusionauth';

      if (provider === 'fusionauth') {
        await this.signupWithFusionAuth(options);
      } else if (provider === 'prsnl') {
        await this.signupWithPRSNL(options);
      }
    } catch (error) {
      console.error('Signup failed:', error);
      this.updateState({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Signup failed' 
      });
    }
  }

  /**
   * Signup with FusionAuth
   */
  private async signupWithFusionAuth(options: SignupOptions) {
    const redirectUri = window.location.origin + '/auth/fusionauth/callback';
    
    const registrationUrl = `${this.fusionAuthConfig.url}/oauth2/register?` +
      `client_id=${this.fusionAuthConfig.clientId}&` +
      `response_type=code&` +
      `redirect_uri=${encodeURIComponent(redirectUri)}&` +
      `scope=openid email profile`;

    window.location.href = registrationUrl;
  }

  /**
   * Signup with PRSNL backend
   */
  private async signupWithPRSNL(options: SignupOptions) {
    if (!options.userData) {
      throw new Error('User data required for PRSNL signup');
    }

    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(options.userData)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Signup failed');
    }

    const userData = await response.json();
    this.updateState({
      isAuthenticated: true,
      user: this.normalizeUser(userData, 'prsnl'),
      token: userData.access_token,
      refreshToken: userData.refresh_token,
      authSource: 'prsnl',
      isLoading: false,
      error: null
    });

    this.storeTokens(userData.access_token, userData.refresh_token, 'prsnl');
  }

  /**
   * Handle auth callback (for OAuth flows)
   */
  async handleCallback(provider: 'keycloak' | 'fusionauth'): Promise<void> {
    this.updateState({ isLoading: true, error: null });

    try {
      if (provider === 'keycloak') {
        await this.handleKeycloakCallback();
      } else if (provider === 'fusionauth') {
        await this.handleFusionAuthCallback();
      }
    } catch (error) {
      console.error('Callback handling failed:', error);
      this.updateState({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Authentication failed' 
      });
    }
  }

  /**
   * Handle Keycloak callback
   */
  private async handleKeycloakCallback() {
    if (!this.keycloak) {
      throw new Error('Keycloak not initialized');
    }

    const authenticated = await this.keycloak.init({
      onLoad: 'login-required'
    });

    if (authenticated && this.keycloak.token) {
      const user = await this.getKeycloakUser();
      this.updateState({
        isAuthenticated: true,
        user,
        token: this.keycloak.token,
        refreshToken: this.keycloak.refreshToken || null,
        authSource: 'keycloak',
        isLoading: false,
        error: null
      });

      this.storeTokens(this.keycloak.token, this.keycloak.refreshToken, 'keycloak');
    } else {
      throw new Error('Keycloak authentication failed');
    }
  }

  /**
   * Handle FusionAuth callback
   */
  private async handleFusionAuthCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    
    if (!code) {
      throw new Error('Authorization code not found');
    }

    // Exchange code for token
    const response = await fetch('/api/auth/fusionauth/callback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        code,
        redirectUri: window.location.origin + '/auth/fusionauth/callback'
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Token exchange failed');
    }

    const tokenData = await response.json();
    const user = this.normalizeUser(tokenData.user, 'fusionauth');

    this.updateState({
      isAuthenticated: true,
      user,
      token: tokenData.access_token,
      refreshToken: tokenData.refresh_token,
      authSource: 'fusionauth',
      isLoading: false,
      error: null
    });

    this.storeTokens(tokenData.access_token, tokenData.refresh_token, 'fusionauth');
  }

  /**
   * Logout from all systems
   */
  async logout(): Promise<void> {
    this.updateState({ isLoading: true });

    try {
      // Logout from backend
      if (this.currentState.token) {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.currentState.token}`
          }
        });
      }

      // Logout from Keycloak
      if (this.currentState.authSource === 'keycloak' && this.keycloak) {
        await this.keycloak.logout({
          redirectUri: window.location.origin
        });
      }

      // Clear stored tokens
      this.clearStoredTokens();

      // Reset state
      this.updateState({
        isAuthenticated: false,
        user: null,
        token: null,
        refreshToken: null,
        authSource: null,
        isLoading: false,
        error: null
      });

      // Redirect to home
      window.location.href = '/';
    } catch (error) {
      console.error('Logout failed:', error);
      this.updateState({ 
        isLoading: false, 
        error: 'Logout failed' 
      });
    }
  }

  /**
   * Refresh authentication token
   */
  async refreshToken(): Promise<boolean> {
    try {
      if (this.currentState.authSource === 'keycloak' && this.keycloak) {
        const refreshed = await this.keycloak.updateToken(30);
        if (refreshed && this.keycloak.token) {
          this.updateState({ token: this.keycloak.token });
          this.storeTokens(this.keycloak.token, this.keycloak.refreshToken, 'keycloak');
          return true;
        }
      } else if (this.currentState.refreshToken) {
        // Handle FusionAuth/PRSNL token refresh
        const response = await fetch('/api/auth/refresh', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            refresh_token: this.currentState.refreshToken
          })
        });

        if (response.ok) {
          const tokenData = await response.json();
          this.updateState({ 
            token: tokenData.access_token,
            refreshToken: tokenData.refresh_token 
          });
          this.storeTokens(tokenData.access_token, tokenData.refresh_token, this.currentState.authSource!);
          return true;
        }
      }

      return false;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  }

  /**
   * Get current authentication state
   */
  getState(): AuthState {
    return { ...this.currentState };
  }

  /**
   * Subscribe to authentication state changes
   */
  subscribe(listener: (state: AuthState) => void): () => void {
    this.stateListeners.push(listener);
    
    // Immediately call with current state
    listener(this.getState());
    
    // Return unsubscribe function
    return () => {
      const index = this.stateListeners.indexOf(listener);
      if (index > -1) {
        this.stateListeners.splice(index, 1);
      }
    };
  }

  // Private helper methods

  private async getKeycloakUser(): Promise<AuthUser> {
    if (!this.keycloak) {
      throw new Error('Keycloak not initialized');
    }

    const profile = await this.keycloak.loadUserProfile();
    const tokenParsed = this.keycloak.tokenParsed as any;

    return {
      id: profile.id || tokenParsed.sub,
      email: profile.email || tokenParsed.email || '',
      name: `${profile.firstName || ''} ${profile.lastName || ''}`.trim(),
      firstName: profile.firstName,
      lastName: profile.lastName,
      roles: tokenParsed.realm_access?.roles || [],
      source: 'keycloak',
      isEmailVerified: tokenParsed.email_verified || false
    };
  }

  private normalizeUser(userData: any, source: 'keycloak' | 'fusionauth' | 'prsnl'): AuthUser {
    return {
      id: userData.id || userData.sub || userData.user_id,
      email: userData.email || '',
      name: userData.name || `${userData.first_name || userData.firstName || ''} ${userData.last_name || userData.lastName || ''}`.trim(),
      firstName: userData.first_name || userData.firstName || userData.given_name,
      lastName: userData.last_name || userData.lastName || userData.family_name,
      roles: userData.roles || [],
      source,
      isEmailVerified: userData.email_verified || userData.is_verified || false,
      preferences: userData.preferences || {}
    };
  }

  private updateState(updates: Partial<AuthState>) {
    this.currentState = { ...this.currentState, ...updates };
    this.stateListeners.forEach(listener => listener(this.getState()));
  }

  private storeTokens(accessToken: string, refreshToken: string | null, source: string) {
    localStorage.setItem('prsnl_auth_token', accessToken);
    localStorage.setItem('prsnl_auth_source', source);
    if (refreshToken) {
      localStorage.setItem('prsnl_refresh_token', refreshToken);
    }
  }

  private clearStoredTokens() {
    localStorage.removeItem('prsnl_auth_token');
    localStorage.removeItem('prsnl_refresh_token');
    localStorage.removeItem('prsnl_auth_source');
  }
}

// Export singleton instance
export const unifiedAuth = new UnifiedAuthService();