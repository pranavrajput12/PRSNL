#!/bin/bash

# Smoke Test Script for PRSNL
# Quick validation that all services are running correctly

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3003"

# Test results
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local url=$1
    local expected_status=$2
    local description=$3
    
    echo -e "${YELLOW}Testing: $description${NC}"
    echo "  URL: $url"
    
    # Make request and capture status code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}  ✓ PASSED (Status: $status_code)${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}  ✗ FAILED (Expected: $expected_status, Got: $status_code)${NC}"
        ((FAILED++))
        return 1
    fi
}

# Function to test JSON endpoint
test_json_endpoint() {
    local url=$1
    local json_path=$2
    local description=$3
    
    echo -e "${YELLOW}Testing: $description${NC}"
    echo "  URL: $url"
    echo "  Checking: $json_path"
    
    # Make request and check JSON path
    response=$(curl -s "$url")
    result=$(echo "$response" | jq -r "$json_path" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$result" ] && [ "$result" != "null" ]; then
        echo -e "${GREEN}  ✓ PASSED (Value: $result)${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}  ✗ FAILED (Could not get $json_path)${NC}"
        ((FAILED++))
        return 1
    fi
}

echo -e "${YELLOW}=== PRSNL Smoke Tests ===${NC}"
echo ""

# Backend Health Checks
echo -e "${YELLOW}--- Backend Health Checks ---${NC}"
test_endpoint "$BACKEND_URL/health" "200" "Basic health check"
test_json_endpoint "$BACKEND_URL/health" ".overall_status" "Health status field"
test_endpoint "$BACKEND_URL/api/health" "200" "API health check"
test_json_endpoint "$BACKEND_URL/api/health/ready" ".status" "Readiness probe"

# API Endpoints
echo ""
echo -e "${YELLOW}--- API Endpoints ---${NC}"
test_endpoint "$BACKEND_URL/api/capture/debug" "200" "Capture debug endpoint"
test_json_endpoint "$BACKEND_URL/api/debug/routes" ".total_routes" "Routes debug endpoint"
test_endpoint "$BACKEND_URL/api/timeline" "200" "Timeline endpoint"
test_endpoint "$BACKEND_URL/api/content-types" "200" "Content types endpoint"
test_endpoint "$BACKEND_URL/docs" "200" "API documentation"

# Frontend Check (if running)
echo ""
echo -e "${YELLOW}--- Frontend Check ---${NC}"
if curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" | grep -q "200\|304"; then
    echo -e "${GREEN}  ✓ Frontend is running on port 3003${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}  ⚠ Frontend not running (run 'cd frontend && npm run dev')${NC}"
fi

# Database Connection Test
echo ""
echo -e "${YELLOW}--- Database Check ---${NC}"
if test_json_endpoint "$BACKEND_URL/api/health/detailed" ".services.database.status" "Database connection"; then
    item_count=$(curl -s "$BACKEND_URL/api/health/detailed" | jq -r ".services.database.item_count")
    echo -e "  ${GREEN}Items in database: $item_count${NC}"
fi

# Summary
echo ""
echo -e "${YELLOW}=== Test Summary ===${NC}"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Check the output above.${NC}"
    exit 1
fi