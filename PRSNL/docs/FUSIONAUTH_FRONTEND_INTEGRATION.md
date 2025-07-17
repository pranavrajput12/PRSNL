# FusionAuth Frontend Integration Guide

## Quick Integration Steps

### 1. Configuration is Ready
The FusionAuth configuration is already set up in:
```typescript
// frontend/src/lib/config/fusionauth.ts
export const FUSIONAUTH_CONFIG = {
  clientId: '4218d574-603a-48b4-b980-39a0b73e4cff',
  redirectUri: 'http://localhost:3004/auth/callback',
  authUrl: 'http://localhost:9011/oauth2/authorize',
  tokenUrl: 'http://localhost:9011/oauth2/token',
  userInfoUrl: 'http://localhost:9011/oauth2/userinfo'
}
```

### 2. OAuth Callback Handler is Ready
The callback page (`/auth/callback`) now handles both Keycloak and FusionAuth OAuth flows automatically.

### 3. Add FusionAuth Login Button

To add a FusionAuth login option to your login page, add this button in `/routes/auth/login/+page.svelte`:

```svelte
<!-- Add this import at the top -->
import { getAuthorizationUrl } from '$lib/config/fusionauth';

<!-- Add this button in the SSO section (after Google/GitHub/Microsoft buttons) -->
<button 
  on:click={() => window.location.href = getAuthorizationUrl()}
  disabled={$isLoading}
  class="w-full inline-flex justify-center py-3 px-4 border border-white/20 rounded-lg bg-gradient-to-r from-orange-500/10 to-red-500/10 text-sm font-medium text-white hover:from-orange-500/20 hover:to-red-500/20 transition-all disabled:opacity-50"
>
  <Icon name="users" class="w-5 h-5" />
  <span class="ml-2">Continue with FusionAuth</span>
</button>
```

### 4. Update Unified Auth Store

The unified auth store needs a method to handle FusionAuth login. Add this to `unified-auth.ts`:

```typescript
async handleFusionAuthLogin(data: {
  user: any;
  access_token: string;
  refresh_token: string;
}) {
  const authState: AuthState = {
    isAuthenticated: true,
    user: {
      id: data.user.sub,
      email: data.user.email,
      firstName: data.user.given_name,
      lastName: data.user.family_name,
      name: data.user.name,
      roles: data.user.roles || ['user'],
      isEmailVerified: data.user.email_verified || false,
      source: 'fusionauth'
    },
    token: data.access_token,
    refreshToken: data.refresh_token,
    authSource: 'fusionauth',
    isLoading: false,
    error: null
  };
  
  authStore.set(authState);
  
  // Store tokens in localStorage
  if (browser) {
    localStorage.setItem('fusionauth_token', data.access_token);
    localStorage.setItem('fusionauth_refresh', data.refresh_token);
  }
}
```

### 5. Protected Routes

The auth guard already works with the unified auth store, so protected routes will automatically work with FusionAuth users.

### 6. Logout

To logout from FusionAuth:

```typescript
import { getLogoutUrl } from '$lib/config/fusionauth';

// In your logout function
async function logout() {
  // Clear local state
  authActions.logout();
  
  // Redirect to FusionAuth logout
  window.location.href = getLogoutUrl();
}
```

## Testing the Integration

1. **Start all services**:
   ```bash
   # Ensure FusionAuth is running
   docker-compose -f docker-compose.auth.yml up -d
   
   # Start frontend
   cd frontend && npm run dev -- --port 3004
   ```

2. **Test login flow**:
   - Navigate to http://localhost:3004/auth/login
   - Click "Continue with FusionAuth"
   - Login with any migrated user (e.g., prsnlfyi@gmail.com)
   - You'll be redirected back to the app, authenticated

3. **Verify authentication**:
   - Check browser DevTools > Application > Local Storage
   - You should see `fusionauth_token` and `fusionauth_refresh`
   - The auth store should show `authSource: 'fusionauth'`

## Advanced Features

### Social Login via FusionAuth
Configure social providers in FusionAuth admin:
1. Go to Settings → Identity Providers
2. Add Google, GitHub, Microsoft, etc.
3. Users can then use social login through FusionAuth

### Multi-Factor Authentication
1. Enable in FusionAuth admin per user or application
2. FusionAuth handles the MFA flow automatically

### Password Reset
FusionAuth handles password reset emails once SMTP is configured.

## Troubleshooting

### CORS Issues
If you get CORS errors, add your frontend URL to FusionAuth:
1. Go to Applications → PRSNL → OAuth tab
2. Add `http://localhost:3004` to Authorized Origins

### Token Validation
To validate tokens on the backend:
```python
# In your FastAPI backend
import jwt

def verify_fusionauth_token(token: str):
    # FusionAuth uses HS256 by default
    decoded = jwt.decode(
        token,
        options={"verify_signature": False}  # Or use proper verification
    )
    return decoded
```

## Benefits of This Integration

1. **Unified Login Experience**: Users can choose between:
   - Traditional email/password (PRSNL)
   - Enterprise SSO (Keycloak)
   - Modern identity management (FusionAuth)

2. **Progressive Enhancement**: Start with basic auth, add social login later

3. **Analytics**: FusionAuth provides login analytics out of the box

4. **User Management**: Admins can manage users in FusionAuth UI

5. **Security**: OAuth2/OIDC standard implementation with PKCE support