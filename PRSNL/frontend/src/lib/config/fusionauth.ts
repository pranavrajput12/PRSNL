/**
 * FusionAuth OAuth2 Configuration
 */

export const FUSIONAUTH_CONFIG = {
  // Application credentials from FusionAuth
  clientId: '4218d574-603a-48b4-b980-39a0b73e4cff',
  clientSecret: '6f16bb7d-08f6-4008-a7ce-bef1cee8398b', // Only use in secure backend
  
  // OAuth2 endpoints
  authUrl: 'http://localhost:9011/oauth2/authorize',
  tokenUrl: 'http://localhost:9011/oauth2/token',
  userInfoUrl: 'http://localhost:9011/oauth2/userinfo',
  logoutUrl: 'http://localhost:9011/oauth2/logout',
  
  // Redirect URIs
  redirectUri: 'http://localhost:3004/auth/callback',
  postLogoutRedirectUri: 'http://localhost:3004',
  
  // OAuth2 settings
  scope: 'openid profile email offline_access',
  responseType: 'code',
  grantType: 'authorization_code',
  
  // Application settings
  applicationId: '4218d574-603a-48b4-b980-39a0b73e4cff',
  tenantId: '12300110-2d09-0e53-73d2-9968e4b0abe4', // Default tenant
};

/**
 * Generate OAuth2 authorization URL
 */
export function getAuthorizationUrl(state?: string): string {
  const params = new URLSearchParams({
    client_id: FUSIONAUTH_CONFIG.clientId,
    redirect_uri: FUSIONAUTH_CONFIG.redirectUri,
    response_type: FUSIONAUTH_CONFIG.responseType,
    scope: FUSIONAUTH_CONFIG.scope,
    ...(state && { state })
  });
  
  return `${FUSIONAUTH_CONFIG.authUrl}?${params.toString()}`;
}

/**
 * Generate logout URL
 */
export function getLogoutUrl(): string {
  const params = new URLSearchParams({
    client_id: FUSIONAUTH_CONFIG.clientId,
    post_logout_redirect_uri: FUSIONAUTH_CONFIG.postLogoutRedirectUri
  });
  
  return `${FUSIONAUTH_CONFIG.logoutUrl}?${params.toString()}`;
}