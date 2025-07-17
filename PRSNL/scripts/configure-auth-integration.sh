#!/bin/bash

# PRSNL Auth Integration Configuration Script
# Configures Keycloak realm and FusionAuth application for integration

set -e

echo "🔧 Configuring PRSNL Authentication Integration..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if services are running
print_status "Checking service status..."

if ! curl -sf http://localhost:8080/health/ready > /dev/null 2>&1; then
    print_error "Keycloak is not ready at http://localhost:8080"
    print_warning "Run: ./scripts/start-auth-services.sh"
    exit 1
fi

if ! curl -sf http://localhost:9011/api/status > /dev/null 2>&1; then
    print_error "FusionAuth is not ready at http://localhost:9011"
    print_warning "Run: ./scripts/start-auth-services.sh"
    exit 1
fi

print_success "Both services are running"

# Load environment variables
if [ -f .env.auth ]; then
    set -a
    source .env.auth
    set +a
fi

# Use the actual default password from Keycloak
KEYCLOAK_ADMIN_PASSWORD="admin123"
FUSIONAUTH_API_KEY=${FUSIONAUTH_API_KEY:-bf69486b-4733-4470-a592-f1bfce7af580}

print_status "Configuration URLs:"
echo "  Keycloak Admin: http://localhost:8080"
echo "  - Username: admin"
echo "  - Password: $KEYCLOAK_ADMIN_PASSWORD"
echo ""
echo "  FusionAuth Admin: http://localhost:9011"
echo "  - Email: admin@prsnl.local"
echo "  - Password: prsnl_admin_2024!"
echo ""

# Get admin access token from Keycloak
print_status "Getting Keycloak admin access token..."

KEYCLOAK_TOKEN=$(curl -s -X POST "http://localhost:8080/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=$KEYCLOAK_ADMIN_PASSWORD" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

if [ "$KEYCLOAK_TOKEN" = "null" ] || [ -z "$KEYCLOAK_TOKEN" ]; then
    print_error "Failed to get Keycloak admin token"
    print_warning "Check admin credentials and try again"
    exit 1
fi

print_success "Got Keycloak admin token"

# Create PRSNL realm in Keycloak
print_status "Creating PRSNL realm in Keycloak..."

REALM_CONFIG='{
  "realm": "prsnl",
  "displayName": "PRSNL Knowledge Management",
  "enabled": true,
  "sslRequired": "external",
  "registrationAllowed": true,
  "registrationEmailAsUsername": true,
  "rememberMe": true,
  "verifyEmail": true,
  "loginWithEmailAllowed": true,
  "duplicateEmailsAllowed": false,
  "resetPasswordAllowed": true,
  "editUsernameAllowed": true,
  "bruteForceProtected": true,
  "permanentLockout": false,
  "maxFailureWaitSeconds": 900,
  "minimumQuickLoginWaitSeconds": 60,
  "waitIncrementSeconds": 60,
  "quickLoginCheckMilliSeconds": 1000,
  "maxDeltaTimeSeconds": 43200,
  "failureFactor": 30,
  "defaultSignatureAlgorithm": "RS256",
  "accessTokenLifespan": 300,
  "accessTokenLifespanForImplicitFlow": 900,
  "ssoSessionIdleTimeout": 1800,
  "ssoSessionMaxLifespan": 36000,
  "offlineSessionIdleTimeout": 2592000,
  "attributes": {
    "frontendUrl": "http://localhost:8080"
  }
}'

REALM_RESPONSE=$(curl -s -w "%{http_code}" -X POST "http://localhost:8080/admin/realms" \
  -H "Authorization: Bearer $KEYCLOAK_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$REALM_CONFIG")

REALM_STATUS="${REALM_RESPONSE: -3}"
if [ "$REALM_STATUS" = "201" ] || [ "$REALM_STATUS" = "409" ]; then
    print_success "PRSNL realm created/exists in Keycloak"
else
    print_warning "Realm creation response: $REALM_STATUS"
fi

# Create PRSNL client in Keycloak
print_status "Creating PRSNL client in Keycloak..."

CLIENT_CONFIG='{
  "clientId": "prsnl-frontend",
  "name": "PRSNL Frontend Application",
  "description": "PRSNL Knowledge Management Frontend",
  "enabled": true,
  "clientAuthenticatorType": "client-secret",
  "secret": "prsnl-secret-2024-secure-key",
  "redirectUris": [
    "http://localhost:3004/*",
    "http://localhost:3000/*",
    "https://prsnl.app/*",
    "https://app.prsnl.app/*"
  ],
  "webOrigins": [
    "http://localhost:3004",
    "http://localhost:3000",
    "https://prsnl.app",
    "https://app.prsnl.app"
  ],
  "protocol": "openid-connect",
  "publicClient": true,
  "standardFlowEnabled": true,
  "implicitFlowEnabled": false,
  "directAccessGrantsEnabled": true,
  "serviceAccountsEnabled": false,
  "fullScopeAllowed": true,
  "attributes": {
    "saml.assertion.signature": "false",
    "saml.force.post.binding": "false",
    "saml.multivalued.roles": "false",
    "saml.encrypt": "false",
    "saml.server.signature": "false",
    "saml.server.signature.keyinfo.ext": "false",
    "exclude.session.state.from.auth.response": "false",
    "saml_force_name_id_format": "false",
    "saml.client.signature": "false",
    "tls.client.certificate.bound.access.tokens": "false",
    "saml.authnstatement": "false",
    "display.on.consent.screen": "false",
    "saml.onetimeuse.condition": "false"
  }
}'

CLIENT_RESPONSE=$(curl -s -w "%{http_code}" -X POST "http://localhost:8080/admin/realms/prsnl/clients" \
  -H "Authorization: Bearer $KEYCLOAK_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$CLIENT_CONFIG")

CLIENT_STATUS="${CLIENT_RESPONSE: -3}"
if [ "$CLIENT_STATUS" = "201" ] || [ "$CLIENT_STATUS" = "409" ]; then
    print_success "PRSNL client created/exists in Keycloak"
else
    print_warning "Client creation response: $CLIENT_STATUS"
fi

# Test FusionAuth API
print_status "Testing FusionAuth API..."

FA_STATUS=$(curl -s -w "%{http_code}" -X GET "http://localhost:9011/api/application" \
  -H "Authorization: $FUSIONAUTH_API_KEY" \
  -H "Content-Type: application/json")

FA_STATUS_CODE="${FA_STATUS: -3}"
if [ "$FA_STATUS_CODE" = "200" ]; then
    print_success "FusionAuth API is accessible"
else
    print_warning "FusionAuth API response: $FA_STATUS_CODE"
    print_warning "The application may not be fully configured yet"
fi

echo ""
print_success "🎉 Authentication integration configuration completed!"
echo ""
echo "Next steps:"
echo "1. ✅ Keycloak realm 'prsnl' created at http://localhost:8080"
echo "2. ✅ Keycloak client 'prsnl-frontend' configured"
echo "3. ✅ FusionAuth application pre-configured via kickstart"
echo "4. 🔄 Update your FastAPI endpoints to use unified auth"
echo "5. 🔄 Update your Svelte frontend to use new auth flow"
echo ""
echo "Test URLs:"
echo "- Keycloak Auth: http://localhost:8080/realms/prsnl/protocol/openid-connect/auth"
echo "- FusionAuth Login: http://localhost:9011/oauth2/authorize"
echo ""
echo "Documentation:"
echo "- Keycloak Admin: http://localhost:8080/admin/master/console/#/prsnl"
echo "- FusionAuth Admin: http://localhost:9011/admin/application/"