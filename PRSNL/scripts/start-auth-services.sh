#!/bin/bash

# PRSNL Authentication Services Startup Script
# This script starts Keycloak and FusionAuth services

set -e

echo "🚀 Starting PRSNL Authentication Services..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if PostgreSQL is running on port 5432
if ! nc -z localhost 5432 2>/dev/null; then
    print_error "PostgreSQL is not running on port 5432."
    print_warning "Please start your PostgreSQL service first:"
    echo "  /opt/homebrew/bin/brew services start postgresql@16"
    exit 1
fi

print_success "PostgreSQL is running on port 5432"

# Load environment variables (safely handle values with special characters)
if [ -f .env ]; then
    print_status "Loading environment variables from .env"
    set -a
    source .env
    set +a
fi

if [ -f .env.auth ]; then
    print_status "Loading auth environment variables from .env.auth"
    set -a
    source .env.auth
    set +a
fi

# Check if auth services are already running
if docker ps | grep -q "prsnl-keycloak"; then
    print_warning "Keycloak is already running"
else
    print_status "Starting Keycloak..."
fi

if docker ps | grep -q "prsnl-fusionauth"; then
    print_warning "FusionAuth is already running"  
else
    print_status "Starting FusionAuth..."
fi

# Start the auth services
print_status "Launching authentication services with docker-compose..."
docker-compose -f docker-compose.auth.yml up -d

# Wait for services to be ready
print_status "Waiting for services to start..."

# Wait for Keycloak
print_status "Waiting for Keycloak to be ready..."
timeout=300  # 5 minutes
counter=0
while ! curl -sf http://localhost:8080/health/ready > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        print_error "Keycloak failed to start within 5 minutes"
        docker-compose -f docker-compose.auth.yml logs keycloak
        exit 1
    fi
    sleep 5
    counter=$((counter + 5))
    echo -n "."
done
echo ""
print_success "Keycloak is ready! 🎉"

# Wait for FusionAuth
print_status "Waiting for FusionAuth to be ready..."
counter=0
while ! curl -sf http://localhost:9011/api/status > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        print_error "FusionAuth failed to start within 5 minutes"
        docker-compose -f docker-compose.auth.yml logs fusionauth
        exit 1
    fi
    sleep 5
    counter=$((counter + 5))
    echo -n "."
done
echo ""
print_success "FusionAuth is ready! 🎉"

# Display service information
echo ""
echo "🎯 Authentication Services Status:"
echo "=================================="
echo ""
echo -e "${PURPLE}Keycloak Admin Console:${NC}"
echo "  URL: http://localhost:8080"
echo "  Username: admin"
echo "  Password: ${KEYCLOAK_ADMIN_PASSWORD:-admin123}"
echo ""
echo -e "${PURPLE}FusionAuth Admin Console:${NC}"
echo "  URL: http://localhost:9011"
echo "  Email: admin@prsnl.local"
echo "  Password: prsnl_admin_2024!"
echo ""
echo -e "${PURPLE}Service Health Checks:${NC}"
echo "  Keycloak: http://localhost:8080/health/ready"
echo "  FusionAuth: http://localhost:9011/api/status"
echo ""

# Check service status
print_status "Checking service health..."

# Keycloak health check
if curl -sf http://localhost:8080/health/ready > /dev/null 2>&1; then
    print_success "✅ Keycloak is healthy"
else
    print_error "❌ Keycloak health check failed"
fi

# FusionAuth health check
if curl -sf http://localhost:9011/api/status > /dev/null 2>&1; then
    print_success "✅ FusionAuth is healthy"
else
    print_error "❌ FusionAuth health check failed"
fi

echo ""
print_success "🚀 All authentication services are running!"
echo ""
echo "Next steps:"
echo "1. Configure Keycloak realm at http://localhost:8080"
echo "2. Set up FusionAuth application at http://localhost:9011"
echo "3. Run: ./scripts/configure-auth-integration.sh"
echo ""

# Display logs command
print_status "To view logs, run:"
echo "  docker-compose -f docker-compose.auth.yml logs -f"
echo ""
print_status "To stop services, run:"
echo "  docker-compose -f docker-compose.auth.yml down"