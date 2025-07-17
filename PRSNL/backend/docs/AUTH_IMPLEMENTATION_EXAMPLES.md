# Authentication Implementation Examples: SuperTokens vs Keycloak

## FastAPI Backend Implementation Comparison

### SuperTokens Implementation

#### 1. Project Structure
```
backend/
├── app/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── middleware.py
│   ├── api/
│   │   ├── auth.py
│   │   └── users.py
│   ├── models/
│   │   └── user.py
│   └── main.py
├── requirements.txt
└── docker-compose.yml
```

#### 2. Configuration (app/auth/config.py)
```python
from supertokens_python import init, InputAppInfo, SupertokensConfig
from supertokens_python.recipe import emailpassword, session, dashboard
from supertokens_python.recipe.emailpassword import InputFormField
from supertokens_python.recipe.session import InputErrorHandlers
import os

def init_supertokens():
    init(
        app_info=InputAppInfo(
            app_name="PRSNL",
            api_domain=os.getenv("API_DOMAIN", "http://localhost:8000"),
            website_domain=os.getenv("WEBSITE_DOMAIN", "http://localhost:3000"),
            api_base_path="/auth",
            website_base_path="/auth"
        ),
        supertokens_config=SupertokensConfig(
            connection_uri=os.getenv("SUPERTOKENS_URI", "http://localhost:3567"),
            api_key=os.getenv("SUPERTOKENS_API_KEY")
        ),
        framework='fastapi',
        recipe_list=[
            emailpassword.init(
                sign_up_feature=emailpassword.InputSignUpFeature(
                    form_fields=[
                        InputFormField(id="email"),
                        InputFormField(id="password"),
                        InputFormField(
                            id="name",
                            validate=lambda value: "Name is required" if not value else None
                        ),
                    ]
                ),
                override=emailpassword.InputOverrideConfig(
                    apis=override_email_password_apis,
                    functions=override_email_password_functions
                )
            ),
            session.init(
                anti_csrf="VIA_TOKEN",
                cookie_domain=os.getenv("COOKIE_DOMAIN"),
                session_expired_status_code=401,
                invalid_claim_status_code=403,
                override=session.InputOverrideConfig(
                    error_handlers=InputErrorHandlers(
                        on_invalid_claim=lambda err, req, res: handle_invalid_claim(err, req, res),
                        on_token_theft_detected=lambda session_handle, user_id, req, res: handle_token_theft(session_handle, user_id, req, res),
                        on_unauthorised=lambda err, req, res: handle_unauthorised(err, req, res)
                    )
                )
            ),
            dashboard.init(api_key=os.getenv("SUPERTOKENS_API_KEY"))
        ]
    )

# Custom overrides
async def override_email_password_apis(original_implementation):
    original_sign_up_post = original_implementation.sign_up_post
    
    async def sign_up_post(form_fields, api_options, user_context):
        # Custom validation
        email = next(field.value for field in form_fields if field.id == "email")
        if email.endswith("@blacklisted.com"):
            return emailpassword.SignUpPostEmailAlreadyExistsError()
        
        # Call original implementation
        response = await original_sign_up_post(form_fields, api_options, user_context)
        
        # Post-signup logic
        if isinstance(response, emailpassword.SignUpPostOkResult):
            await create_user_profile(response.user.user_id, form_fields)
        
        return response
    
    original_implementation.sign_up_post = sign_up_post
    return original_implementation
```

#### 3. Main Application (app/main.py)
```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supertokens_python.framework.fastapi import get_middleware
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.framework.fastapi import verify_session
from app.auth.config import init_supertokens
from app.api import auth, users

# Initialize SuperTokens
init_supertokens()

app = FastAPI(title="PRSNL API", version="1.0.0")

# Add SuperTokens middleware
app.add_middleware(get_middleware())

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type"] + get_all_cors_headers(),
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])

# Protected endpoint example
@app.get("/api/user/profile")
async def get_user_profile(session: SessionContainer = Depends(verify_session())):
    user_id = session.get_user_id()
    user_metadata = await session.get_access_token_payload()
    
    # Fetch additional user data from your database
    user_data = await get_user_from_db(user_id)
    
    return {
        "user_id": user_id,
        "email": user_metadata.get("email"),
        "profile": user_data
    }

# Role-based access control
from supertokens_python.recipe.userroles import UserRoleClaim

@app.get("/api/admin/users")
async def list_all_users(
    session: SessionContainer = Depends(
        verify_session(
            override_global_claim_validators=lambda global_validators, session, user_context: 
            global_validators + [UserRoleClaim.validators.includes("admin")]
        )
    )
):
    # Admin-only endpoint
    return await get_all_users()
```

#### 4. User Management (app/api/users.py)
```python
from fastapi import APIRouter, Depends, HTTPException
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.framework.fastapi import verify_session
from supertokens_python.recipe.emailpassword.asyncio import get_user_by_id, update_email_or_password
from supertokens_python.recipe.userroles.asyncio import add_role_to_user, get_roles_for_user

router = APIRouter()

@router.get("/me")
async def get_current_user(session: SessionContainer = Depends(verify_session())):
    user_id = session.get_user_id()
    user = await get_user_by_id(user_id)
    roles = await get_roles_for_user(user_id)
    
    return {
        "id": user.user_id,
        "email": user.email,
        "time_joined": user.time_joined,
        "roles": roles
    }

@router.put("/update-email")
async def update_email(
    new_email: str,
    session: SessionContainer = Depends(verify_session())
):
    user_id = session.get_user_id()
    result = await update_email_or_password(user_id, email=new_email)
    
    if result.status == "OK":
        return {"message": "Email updated successfully"}
    elif result.status == "EMAIL_ALREADY_EXISTS_ERROR":
        raise HTTPException(400, "Email already exists")
    else:
        raise HTTPException(400, "Update failed")
```

### Keycloak Implementation

#### 1. Project Structure
```
backend/
├── app/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── keycloak_client.py
│   │   ├── middleware.py
│   │   └── dependencies.py
│   ├── api/
│   │   ├── auth.py
│   │   └── users.py
│   ├── models/
│   │   └── user.py
│   └── main.py
├── keycloak/
│   ├── realm-export.json
│   └── themes/
├── requirements.txt
└── docker-compose.yml
```

#### 2. Keycloak Client Setup (app/auth/keycloak_client.py)
```python
import jwt
from keycloak import KeycloakOpenID, KeycloakAdmin
from fastapi import HTTPException
from typing import Dict, Optional
import os

class KeycloakClient:
    def __init__(self):
        self.server_url = os.getenv("KEYCLOAK_SERVER_URL", "http://localhost:8080/auth/")
        self.realm_name = os.getenv("KEYCLOAK_REALM", "prsnl")
        self.client_id = os.getenv("KEYCLOAK_CLIENT_ID", "prsnl-backend")
        self.client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET")
        
        # Public client for token verification
        self.keycloak_openid = KeycloakOpenID(
            server_url=self.server_url,
            client_id=self.client_id,
            realm_name=self.realm_name,
            client_secret_key=self.client_secret
        )
        
        # Admin client for user management
        self.keycloak_admin = KeycloakAdmin(
            server_url=self.server_url,
            username=os.getenv("KEYCLOAK_ADMIN_USER"),
            password=os.getenv("KEYCLOAK_ADMIN_PASSWORD"),
            realm_name=self.realm_name,
            verify=True
        )
        
        # Cache public key
        self.public_key = None
    
    def get_public_key(self):
        if not self.public_key:
            key = self.keycloak_openid.public_key()
            self.public_key = f"-----BEGIN PUBLIC KEY-----\n{key}\n-----END PUBLIC KEY-----"
        return self.public_key
    
    def verify_token(self, token: str) -> Dict:
        try:
            # Verify token
            payload = jwt.decode(
                token,
                self.get_public_key(),
                algorithms=["RS256"],
                audience=self.client_id,
                options={"verify_exp": True}
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    def get_user_info(self, token: str) -> Dict:
        return self.keycloak_openid.userinfo(token)
    
    def introspect_token(self, token: str) -> Dict:
        return self.keycloak_openid.introspect(token)
    
    # Admin operations
    def create_user(self, user_data: Dict) -> str:
        return self.keycloak_admin.create_user(user_data)
    
    def get_user(self, user_id: str) -> Dict:
        return self.keycloak_admin.get_user(user_id)
    
    def update_user(self, user_id: str, user_data: Dict):
        return self.keycloak_admin.update_user(user_id, user_data)
    
    def assign_realm_role(self, user_id: str, role_name: str):
        role = self.keycloak_admin.get_realm_role(role_name)
        return self.keycloak_admin.assign_realm_roles(user_id, [role])
    
    def get_user_roles(self, user_id: str) -> list:
        return self.keycloak_admin.get_realm_roles_of_user(user_id)

# Global instance
keycloak_client = KeycloakClient()
```

#### 3. Authentication Dependencies (app/auth/dependencies.py)
```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
from .keycloak_client import keycloak_client

security = HTTPBearer()

class CurrentUser:
    def __init__(self, payload: dict):
        self.user_id = payload["sub"]
        self.email = payload.get("email")
        self.username = payload.get("preferred_username")
        self.roles = payload.get("realm_access", {}).get("roles", [])
        self.client_roles = payload.get("resource_access", {}).get("prsnl-backend", {}).get("roles", [])
        self.groups = payload.get("groups", [])
        self.payload = payload
    
    def has_role(self, role: str) -> bool:
        return role in self.roles
    
    def has_client_role(self, role: str) -> bool:
        return role in self.client_roles
    
    def is_admin(self) -> bool:
        return self.has_role("admin") or self.has_client_role("admin")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> CurrentUser:
    token = credentials.credentials
    payload = keycloak_client.verify_token(token)
    return CurrentUser(payload)

def require_roles(required_roles: List[str]):
    async def role_checker(current_user: CurrentUser = Depends(get_current_user)):
        if not any(current_user.has_role(role) for role in required_roles):
            raise HTTPException(
                status_code=403,
                detail=f"Required roles: {required_roles}"
            )
        return current_user
    return role_checker

def require_admin():
    async def admin_checker(current_user: CurrentUser = Depends(get_current_user)):
        if not current_user.is_admin():
            raise HTTPException(status_code=403, detail="Admin access required")
        return current_user
    return admin_checker

# Optional authentication (for public endpoints that can benefit from user context)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(HTTPBearer(auto_error=False))
) -> Optional[CurrentUser]:
    if credentials:
        try:
            token = credentials.credentials
            payload = keycloak_client.verify_token(token)
            return CurrentUser(payload)
        except HTTPException:
            return None
    return None
```

#### 4. Main Application (app/main.py)
```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.auth.dependencies import get_current_user, require_admin, CurrentUser
from app.auth.keycloak_client import keycloak_client

app = FastAPI(title="PRSNL API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Protected endpoint
@app.get("/api/user/profile")
async def get_user_profile(current_user: CurrentUser = Depends(get_current_user)):
    # Get additional user info from Keycloak
    keycloak_user = keycloak_client.get_user(current_user.user_id)
    
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "username": current_user.username,
        "roles": current_user.roles,
        "attributes": keycloak_user.get("attributes", {}),
        "groups": current_user.groups
    }

# Admin endpoint
@app.get("/api/admin/users")
async def list_all_users(current_user: CurrentUser = Depends(require_admin())):
    users = keycloak_client.keycloak_admin.get_users()
    return {"users": users}

# Role-based endpoint
@app.get("/api/premium/content")
async def get_premium_content(
    current_user: CurrentUser = Depends(require_roles(["premium", "admin"]))
):
    return {"content": "Premium content here"}
```

#### 5. Advanced User Management (app/api/users.py)
```python
from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import get_current_user, require_admin, CurrentUser
from app.auth.keycloak_client import keycloak_client
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    attributes: Optional[dict] = None

class UserCreate(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    roles: Optional[List[str]] = []

@router.get("/me")
async def get_current_user_info(current_user: CurrentUser = Depends(get_current_user)):
    user_details = keycloak_client.get_user(current_user.user_id)
    return {
        "id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "first_name": user_details.get("firstName"),
        "last_name": user_details.get("lastName"),
        "roles": current_user.roles,
        "groups": current_user.groups,
        "attributes": user_details.get("attributes", {})
    }

@router.put("/me")
async def update_current_user(
    user_update: UserUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    update_data = {}
    
    if user_update.first_name:
        update_data["firstName"] = user_update.first_name
    if user_update.last_name:
        update_data["lastName"] = user_update.last_name
    if user_update.email:
        update_data["email"] = user_update.email
    if user_update.attributes:
        update_data["attributes"] = user_update.attributes
    
    try:
        keycloak_client.update_user(current_user.user_id, update_data)
        return {"message": "User updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/", dependencies=[Depends(require_admin())])
async def create_user(user_data: UserCreate):
    keycloak_user = {
        "username": user_data.username,
        "email": user_data.email,
        "firstName": user_data.first_name,
        "lastName": user_data.last_name,
        "enabled": True,
        "credentials": [{
            "type": "password",
            "value": user_data.password,
            "temporary": False
        }]
    }
    
    try:
        user_id = keycloak_client.create_user(keycloak_user)
        
        # Assign roles
        for role in user_data.roles:
            keycloak_client.assign_realm_role(user_id, role)
        
        return {"user_id": user_id, "message": "User created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}", dependencies=[Depends(require_admin())])
async def get_user_by_id(user_id: str):
    try:
        user = keycloak_client.get_user(user_id)
        roles = keycloak_client.get_user_roles(user_id)
        
        return {
            "user": user,
            "roles": [role["name"] for role in roles]
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail="User not found")
```

## Svelte Frontend Implementation

### SuperTokens Frontend

#### 1. Authentication Store (src/lib/stores/auth.ts)
```typescript
import { writable } from 'svelte/store';
import SuperTokens from 'supertokens-web-js';
import Session from 'supertokens-web-js/recipe/session';
import EmailPassword from 'supertokens-web-js/recipe/emailpassword';

// Initialize SuperTokens
SuperTokens.init({
    appInfo: {
        appName: "PRSNL",
        apiDomain: "http://localhost:8000",
        apiBasePath: "/auth",
    },
    recipeList: [
        EmailPassword.init(),
        Session.init({
            tokenTransferMethod: "cookie",
            autoAddCredentials: true
        }),
    ],
});

interface User {
    id: string;
    email: string;
    roles?: string[];
}

export const user = writable<User | null>(null);
export const isAuthenticated = writable(false);

export const authStore = {
    async signUp(email: string, password: string, name: string) {
        try {
            const response = await EmailPassword.signUp({
                formFields: [
                    { id: "email", value: email },
                    { id: "password", value: password },
                    { id: "name", value: name }
                ]
            });
            
            if (response.status === "OK") {
                await this.checkSession();
                return { success: true };
            } else {
                return { success: false, error: response.status };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    },

    async signIn(email: string, password: string) {
        try {
            const response = await EmailPassword.signIn({
                formFields: [
                    { id: "email", value: email },
                    { id: "password", value: password }
                ]
            });
            
            if (response.status === "OK") {
                await this.checkSession();
                return { success: true };
            } else {
                return { success: false, error: response.status };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    },

    async signOut() {
        await Session.signOut();
        user.set(null);
        isAuthenticated.set(false);
    },

    async checkSession() {
        try {
            const sessionExists = await Session.doesSessionExist();
            
            if (sessionExists) {
                // Fetch user profile
                const response = await fetch('/api/user/profile');
                if (response.ok) {
                    const userData = await response.json();
                    user.set(userData);
                    isAuthenticated.set(true);
                } else {
                    await this.signOut();
                }
            } else {
                user.set(null);
                isAuthenticated.set(false);
            }
        } catch (error) {
            console.error('Session check failed:', error);
            user.set(null);
            isAuthenticated.set(false);
        }
    }
};

// Check session on app load
if (typeof window !== 'undefined') {
    authStore.checkSession();
}
```

### Keycloak Frontend

#### 1. Keycloak Store (src/lib/stores/keycloak.ts)
```typescript
import { writable } from 'svelte/store';
import Keycloak, { type KeycloakInstance } from 'keycloak-js';

interface User {
    id: string;
    username: string;
    email: string;
    firstName?: string;
    lastName?: string;
    roles: string[];
    groups: string[];
}

export const keycloak = writable<KeycloakInstance | null>(null);
export const user = writable<User | null>(null);
export const isAuthenticated = writable(false);
export const isLoading = writable(true);

class KeycloakService {
    private kc: KeycloakInstance | null = null;

    async init() {
        this.kc = new Keycloak({
            url: 'http://localhost:8080/auth',
            realm: 'prsnl',
            clientId: 'prsnl-frontend'
        });

        try {
            const authenticated = await this.kc.init({
                onLoad: 'check-sso',
                silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
                checkLoginIframe: false,
                enableLogging: process.env.NODE_ENV === 'development'
            });

            keycloak.set(this.kc);

            if (authenticated) {
                await this.loadUserProfile();
            }

            isAuthenticated.set(authenticated);
            isLoading.set(false);

            // Setup token refresh
            this.kc.onTokenExpired = () => {
                this.updateToken();
            };

            // Setup events
            this.kc.onAuthSuccess = () => {
                this.loadUserProfile();
                isAuthenticated.set(true);
            };

            this.kc.onAuthLogout = () => {
                user.set(null);
                isAuthenticated.set(false);
            };

        } catch (error) {
            console.error('Keycloak initialization failed:', error);
            isLoading.set(false);
        }
    }

    async login() {
        if (this.kc) {
            await this.kc.login({
                redirectUri: window.location.origin
            });
        }
    }

    async logout() {
        if (this.kc) {
            await this.kc.logout({
                redirectUri: window.location.origin
            });
        }
    }

    async updateToken() {
        if (this.kc) {
            try {
                const refreshed = await this.kc.updateToken(30);
                if (refreshed) {
                    console.log('Token refreshed');
                }
            } catch (error) {
                console.error('Token refresh failed:', error);
                await this.logout();
            }
        }
    }

    async loadUserProfile() {
        if (this.kc && this.kc.authenticated) {
            try {
                const profile = await this.kc.loadUserProfile();
                const token = this.kc.tokenParsed;
                
                const userData: User = {
                    id: profile.id!,
                    username: profile.username!,
                    email: profile.email!,
                    firstName: profile.firstName,
                    lastName: profile.lastName,
                    roles: token?.realm_access?.roles || [],
                    groups: token?.groups || []
                };

                user.set(userData);
            } catch (error) {
                console.error('Failed to load user profile:', error);
            }
        }
    }

    getToken(): string | undefined {
        return this.kc?.token;
    }

    hasRole(role: string): boolean {
        return this.kc?.hasRealmRole(role) || false;
    }

    hasResourceRole(resource: string, role: string): boolean {
        return this.kc?.hasResourceRole(role, resource) || false;
    }
}

export const keycloakService = new KeycloakService();

// Initialize on client side
if (typeof window !== 'undefined') {
    keycloakService.init();
}
```

#### 2. API Client with Token Management
```typescript
// src/lib/api.ts
import { keycloakService } from './stores/keycloak';

class ApiClient {
    private baseURL = 'http://localhost:8000/api';

    async request(endpoint: string, options: RequestInit = {}) {
        const token = keycloakService.getToken();
        
        const config: RequestInit = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...(token && { Authorization: `Bearer ${token}` }),
                ...options.headers,
            },
        };

        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, config);
            
            if (response.status === 401) {
                // Token expired, try to refresh
                await keycloakService.updateToken();
                
                // Retry with new token
                const newToken = keycloakService.getToken();
                if (newToken) {
                    config.headers = {
                        ...config.headers,
                        Authorization: `Bearer ${newToken}`
                    };
                    return fetch(`${this.baseURL}${endpoint}`, config);
                } else {
                    // Refresh failed, redirect to login
                    await keycloakService.logout();
                    throw new Error('Authentication required');
                }
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    async get(endpoint: string) {
        return this.request(endpoint);
    }

    async post(endpoint: string, data: any) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async put(endpoint: string, data: any) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async delete(endpoint: string) {
        return this.request(endpoint, {
            method: 'DELETE',
        });
    }
}

export const api = new ApiClient();
```

## Key Implementation Differences Summary

### SuperTokens Approach
- **Embedded**: Authentication logic runs within your application
- **Simple Setup**: Minimal configuration required
- **Direct Database**: Uses your existing PostgreSQL database
- **Framework Integration**: Deep integration with FastAPI
- **Session Management**: Built-in session handling

### Keycloak Approach
- **Separate Service**: Authentication server runs independently
- **Standard Protocols**: OAuth 2.0/OpenID Connect compliance
- **Token-Based**: JWT tokens with signature verification
- **Admin Interface**: Comprehensive web-based administration
- **Enterprise Features**: SAML, LDAP, role management

### When to Choose Each

**Choose SuperTokens if:**
- You want faster development
- You prefer embedded solutions
- You have simple authentication needs
- You want lower operational overhead

**Choose Keycloak if:**
- You need enterprise features
- You want protocol compliance
- You plan to integrate multiple applications
- You need advanced user management

Both solutions are production-ready, but they serve different architectural philosophies and use cases.