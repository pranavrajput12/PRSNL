#!/bin/bash

# PRSNL Colima Services Shutdown Script  
# Gracefully stops container services and optionally Colima

set -e

echo "🛑 PRSNL Colima Services Shutdown"
echo "================================="

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

# Navigate to project directory
cd "$(dirname "$0")/.."

# Parse command line arguments
STOP_COLIMA=false
STOP_ALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --stop-colima)
            STOP_COLIMA=true
            shift
            ;;
        --all)
            STOP_ALL=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --stop-colima    Stop Colima after stopping containers"
            echo "  --all           Stop all services including optional ones"
            echo "  -h, --help      Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "1️⃣ Stopping container services..."

if [ "$STOP_ALL" = true ]; then
    echo "Stopping all services (including optional)..."
    docker-compose down
    print_status "All services stopped"
else
    echo "Stopping essential services..."
    
    # Stop individual services gracefully
    services=("keycloak" "fusionauth" "redis")
    
    for service in "${services[@]}"; do
        if docker-compose ps -q "$service" | grep -q .; then
            echo "Stopping $service..."
            docker-compose stop "$service"
            print_status "$service stopped"
        else
            print_warning "$service was not running"
        fi
    done
fi

echo ""
echo "2️⃣ Container service status:"
docker-compose ps

if [ "$STOP_COLIMA" = true ]; then
    echo ""
    echo "3️⃣ Stopping Colima..."
    if colima status &> /dev/null; then
        colima stop
        print_status "Colima stopped"
    else
        print_warning "Colima was not running"
    fi
else
    echo ""
    echo "3️⃣ Colima remains running (use --stop-colima to stop)"
    colima status
fi

echo ""
echo "✅ Shutdown complete!"
echo ""
if [ "$STOP_COLIMA" = false ]; then
    echo "Note: Colima is still running. Services can be restarted quickly with:"
    echo "  ./scripts/start-colima-services.sh"
    echo ""
    echo "To fully stop Colima: colima stop"
fi