#!/bin/bash

# PRSNL Colima Services Startup Script
# Starts essential container services in the correct order

set -e

echo "🚀 PRSNL Colima Services Startup"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Colima is installed
if ! command -v colima &> /dev/null; then
    print_error "Colima is not installed. Install with: brew install colima"
    exit 1
fi

# Start Colima if not running
echo "1️⃣ Checking Colima status..."
if ! colima status &> /dev/null; then
    print_warning "Colima is not running. Starting with optimal settings..."
    colima start --cpu 4 --memory 8 --disk 100
    print_status "Colima started successfully"
else
    print_status "Colima is already running"
fi

# Navigate to project directory
cd "$(dirname "$0")/.."

# Start essential container services
echo ""
echo "2️⃣ Starting essential container services..."

# Start DragonflyDB (Redis replacement)
echo "Starting DragonflyDB cache..."
if docker-compose up -d redis; then
    print_status "DragonflyDB started"
else
    print_error "Failed to start DragonflyDB"
    exit 1
fi

# Start FusionAuth (Primary auth service)
echo "Starting FusionAuth..."
if docker-compose up -d fusionauth; then
    print_status "FusionAuth started"
else
    print_warning "FusionAuth failed to start (continuing...)"
fi

# Start Keycloak (Alternative auth service)
echo "Starting Keycloak..."
if docker-compose up -d keycloak; then
    print_status "Keycloak started"
else
    print_warning "Keycloak failed to start (continuing...)"
fi

# Wait for services to be healthy
echo ""
echo "3️⃣ Waiting for services to be healthy..."

# Wait for DragonflyDB
echo "Waiting for DragonflyDB..."
timeout=30
counter=0
while ! docker-compose exec redis redis-cli ping > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        print_error "DragonflyDB health check timeout"
        break
    fi
    sleep 1
    counter=$((counter + 1))
done

if [ $counter -lt $timeout ]; then
    print_status "DragonflyDB is healthy"
fi

# Check service status
echo ""
echo "4️⃣ Service Status Summary"
echo "========================="

# Show container status
docker-compose ps

echo ""
echo "5️⃣ Connection Information"
echo "========================"
echo "🔗 DragonflyDB:  redis://localhost:6379"
echo "🔑 FusionAuth:   http://localhost:9011"  
echo "🔑 Keycloak:     http://localhost:8080"

echo ""
echo "✅ Colima container services are ready!"
echo ""
echo "Next steps:"
echo "  • Start PostgreSQL: brew services start postgresql@16"
echo "  • Start backend:     cd backend && uvicorn app.main:app --reload --port 8000"
echo "  • Start frontend:    cd frontend && npm run dev -- --port 3004"
echo ""
echo "For optional services, run:"
echo "  • Neo4j:       docker-compose up -d neo4j"
echo "  • LibreChat:   docker-compose up -d librechat librechat-mongo"
echo "  • Browserless: docker-compose up -d browserless"