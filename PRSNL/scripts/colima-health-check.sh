#!/bin/bash

# PRSNL Colima Health Check Script
# Comprehensive health check for all services

set -e

echo "🏥 PRSNL Colima Health Check"
echo "============================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Health check results
HEALTHY_SERVICES=0
TOTAL_SERVICES=0

# Function to check service health
check_service() {
    local service_name="$1"
    local check_command="$2"
    local port="$3"
    
    TOTAL_SERVICES=$((TOTAL_SERVICES + 1))
    
    echo -n "Checking $service_name... "
    
    if eval "$check_command" &> /dev/null; then
        print_status "$service_name is healthy (port $port)"
        HEALTHY_SERVICES=$((HEALTHY_SERVICES + 1))
        return 0
    else
        print_error "$service_name is unhealthy or not running (port $port)"
        return 1
    fi
}

# Navigate to project directory
cd "$(dirname "$0")/.."

echo "1️⃣ Checking Colima Status"
echo "========================"

if colima status &> /dev/null; then
    print_status "Colima is running"
    colima status
else
    print_error "Colima is not running"
    echo "Start with: colima start --cpu 4 --memory 8 --disk 100"
    exit 1
fi

echo ""
echo "2️⃣ Checking Container Services"
echo "=============================="

# Check DragonflyDB
check_service "DragonflyDB" "docker-compose exec -T redis redis-cli ping" "6379"

# Check FusionAuth
check_service "FusionAuth" "curl -f http://localhost:9011/api/status" "9011"

# Check Keycloak
check_service "Keycloak" "curl -f http://localhost:8080/health" "8080"

echo ""
echo "3️⃣ Checking Local Services"
echo "=========================="

# Check PostgreSQL
check_service "PostgreSQL" "pg_isready -h localhost -p 5432" "5432"

# Check Backend API
check_service "Backend API" "curl -f http://localhost:8000/health" "8000"

# Check Frontend
check_service "Frontend" "curl -f http://localhost:3004" "3004"

echo ""
echo "4️⃣ Optional Services Check"
echo "=========================="

# Check Neo4j (if running)
if docker-compose ps -q neo4j | grep -q .; then
    check_service "Neo4j" "curl -f http://localhost:7474" "7474"
else
    print_info "Neo4j is not running (optional service)"
fi

# Check LibreChat (if running)
if docker-compose ps -q librechat | grep -q .; then
    check_service "LibreChat" "curl -f http://localhost:3080" "3080"
else
    print_info "LibreChat is not running (optional service)"
fi

# Check Browserless (if running)
if docker-compose ps -q browserless | grep -q .; then
    check_service "Browserless" "curl -f http://localhost:3001" "3001"
else
    print_info "Browserless is not running (optional service)"
fi

echo ""
echo "5️⃣ Resource Usage"
echo "================="

echo "Colima VM Resources:"
colima status | grep -E "(cpu|memory|disk|arch|runtime)"

echo ""
echo "Docker Container Stats:"
if docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null; then
    true
else
    print_warning "Could not get container stats (containers may not be running)"
fi

echo ""
echo "6️⃣ Health Summary"
echo "================="

echo "Services Status: $HEALTHY_SERVICES/$TOTAL_SERVICES healthy"

if [ $HEALTHY_SERVICES -eq $TOTAL_SERVICES ]; then
    print_status "All services are healthy! 🎉"
    exit 0
elif [ $HEALTHY_SERVICES -gt 0 ]; then
    print_warning "Some services need attention"
    exit 1
else
    print_error "Critical: No services are healthy"
    exit 2
fi