#!/bin/bash

# Permalink System Test Runner
# This script runs all permalink system tests and generates a comprehensive report

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
RESULTS_DIR="test_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$RESULTS_DIR/permalink_test_report_$TIMESTAMP.md"

# Create results directory
mkdir -p "$RESULTS_DIR"

echo -e "${BLUE}🧪 PRSNL Permalink System Test Suite${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""

# Function to check if service is running
check_service() {
    local service_name="$1"
    local url="$2"
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}Checking if $service_name is running...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is running${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}⏳ Waiting for $service_name... (attempt $attempt/$max_attempts)${NC}"
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}❌ $service_name is not responding after $max_attempts attempts${NC}"
    return 1
}

# Function to run a test and capture results
run_test() {
    local test_name="$1"
    local test_command="$2"
    local test_dir="$3"
    local output_file="$RESULTS_DIR/${test_name// /_}_$TIMESTAMP.json"
    
    echo -e "${BLUE}🔍 Running $test_name...${NC}"
    
    cd "$test_dir" 2>/dev/null || {
        echo -e "${RED}❌ Directory $test_dir not found${NC}"
        return 1
    }
    
    # Run the test and capture output
    if eval "$test_command" > "$output_file" 2>&1; then
        echo -e "${GREEN}✅ $test_name completed successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ $test_name failed${NC}"
        return 1
    fi
}

# Initialize report
cat > "$REPORT_FILE" << EOF
# PRSNL Permalink System Test Report

**Generated:** $(date)
**Test Run ID:** $TIMESTAMP

## Overview

This report contains the results of comprehensive testing for the new permalink system implementation.

EOF

# Start the test suite
echo -e "${BLUE}Starting comprehensive permalink system testing...${NC}"
echo ""

# Check if backend is running
if ! check_service "Backend API" "http://localhost:8000/health"; then
    echo -e "${RED}❌ Backend is not running. Please start the backend first.${NC}"
    echo "Run: cd backend && python -m uvicorn app.main:app --reload"
    exit 1
fi

# Check if frontend is running (optional for some tests)
FRONTEND_RUNNING=false
if check_service "Frontend" "http://localhost:5173"; then
    FRONTEND_RUNNING=true
else
    echo -e "${YELLOW}⚠️ Frontend is not running. Some tests will be skipped.${NC}"
fi

echo ""
echo -e "${BLUE}📋 Test Execution Plan:${NC}"
echo "1. Database Migration Verification"
echo "2. Backend API Testing"
if [ "$FRONTEND_RUNNING" = true ]; then
    echo "3. Frontend Route Testing"
    echo "4. End-to-End Integration Testing"
else
    echo "3. Frontend Route Testing (SKIPPED - Frontend not running)"
    echo "4. End-to-End Integration Testing (SKIPPED - Frontend not running)"
fi
echo ""

# Test Results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# 1. Database Migration Verification
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}📊 Test 1: Database Migration Verification${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

if run_test "Migration Verification" "python test_permalink_migration.py" "$BACKEND_DIR"; then
    ((TESTS_PASSED++))
    cat >> "$REPORT_FILE" << EOF

## 1. Database Migration Verification ✅

The database migration verification test passed successfully.

\`\`\`
$(cat "$RESULTS_DIR/Migration_Verification_$TIMESTAMP.json" 2>/dev/null || echo "Results file not found")
\`\`\`

EOF
else
    ((TESTS_FAILED++))
    cat >> "$REPORT_FILE" << EOF

## 1. Database Migration Verification ❌

The database migration verification test failed.

\`\`\`
$(cat "$RESULTS_DIR/Migration_Verification_$TIMESTAMP.json" 2>/dev/null || echo "Results file not found")
\`\`\`

EOF
fi

echo ""

# 2. Backend API Testing
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}🔧 Test 2: Backend API Testing${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

if run_test "API Testing" "python test_permalink_api.py" "$BACKEND_DIR"; then
    ((TESTS_PASSED++))
    cat >> "$REPORT_FILE" << EOF

## 2. Backend API Testing ✅

All API endpoints are working correctly.

\`\`\`
$(cat "$RESULTS_DIR/API_Testing_$TIMESTAMP.json" 2>/dev/null | head -50 || echo "Results file not found")
\`\`\`

EOF
else
    ((TESTS_FAILED++))
    cat >> "$REPORT_FILE" << EOF

## 2. Backend API Testing ❌

Some API endpoints failed testing.

\`\`\`
$(cat "$RESULTS_DIR/API_Testing_$TIMESTAMP.json" 2>/dev/null | head -50 || echo "Results file not found")
\`\`\`

EOF
fi

echo ""

# 3. Frontend Route Testing
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}🌐 Test 3: Frontend Route Testing${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

if [ "$FRONTEND_RUNNING" = true ]; then
    # Check if Node.js and required packages are available
    if command -v node >/dev/null 2>&1 && [ -f "$FRONTEND_DIR/package.json" ]; then
        cd "$FRONTEND_DIR"
        
        # Install playwright if not already installed
        if ! npm list playwright >/dev/null 2>&1; then
            echo -e "${YELLOW}📦 Installing playwright for frontend testing...${NC}"
            npm install playwright @playwright/test --save-dev
            npx playwright install
        fi
        
        cd ..
        
        if run_test "Frontend Routes" "node playwright-permalink-routes.js" "$FRONTEND_DIR"; then
            ((TESTS_PASSED++))
            cat >> "$REPORT_FILE" << EOF

## 3. Frontend Route Testing ✅

All frontend routes are working correctly.

\`\`\`
$(cat "$RESULTS_DIR/Frontend_Routes_$TIMESTAMP.json" 2>/dev/null | head -50 || echo "Results file not found")
\`\`\`

EOF
        else
            ((TESTS_FAILED++))
            cat >> "$REPORT_FILE" << EOF

## 3. Frontend Route Testing ❌

Some frontend routes failed testing.

\`\`\`
$(cat "$RESULTS_DIR/Frontend_Routes_$TIMESTAMP.json" 2>/dev/null | head -50 || echo "Results file not found")
\`\`\`

EOF
        fi
    else
        ((TESTS_SKIPPED++))
        echo -e "${YELLOW}⏭️ Frontend testing skipped - Node.js or package.json not found${NC}"
        cat >> "$REPORT_FILE" << EOF

## 3. Frontend Route Testing ⏭️

Frontend testing was skipped because Node.js or package.json was not found.

EOF
    fi
else
    ((TESTS_SKIPPED++))
    echo -e "${YELLOW}⏭️ Frontend testing skipped - Frontend not running${NC}"
    cat >> "$REPORT_FILE" << EOF

## 3. Frontend Route Testing ⏭️

Frontend testing was skipped because the frontend service is not running.

EOF
fi

echo ""

# 4. Generate Admin Report
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}📈 Generating Administration Report${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

echo -e "${YELLOW}📊 Collecting migration statistics...${NC}"
cd "$BACKEND_DIR"
python admin_permalink_migration.py stats > "$RESULTS_DIR/admin_stats_$TIMESTAMP.txt" 2>&1
cd ..

cat >> "$REPORT_FILE" << EOF

## 4. Administrative Statistics

Current state of the permalink system:

\`\`\`
$(cat "$RESULTS_DIR/admin_stats_$TIMESTAMP.txt" 2>/dev/null || echo "Could not generate admin stats")
\`\`\`

EOF

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}📊 Test Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))

echo -e "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo -e "${YELLOW}Skipped: $TESTS_SKIPPED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed! The permalink system is working correctly.${NC}"
    SUCCESS_RATE="100%"
else
    echo -e "\n${RED}⚠️ Some tests failed. Please review the results.${NC}"
    SUCCESS_RATE=$(( (TESTS_PASSED * 100) / (TESTS_PASSED + TESTS_FAILED) ))"%"
fi

# Add summary to report
cat >> "$REPORT_FILE" << EOF

## Summary

- **Total Tests:** $TOTAL_TESTS
- **Passed:** $TESTS_PASSED
- **Failed:** $TESTS_FAILED  
- **Skipped:** $TESTS_SKIPPED
- **Success Rate:** $SUCCESS_RATE

EOF

if [ $TESTS_FAILED -eq 0 ]; then
    cat >> "$REPORT_FILE" << EOF
### Overall Result: ✅ SUCCESS

All executed tests passed successfully. The permalink system is working correctly.

EOF
else
    cat >> "$REPORT_FILE" << EOF
### Overall Result: ❌ ISSUES FOUND

Some tests failed. Please review the detailed results above and address the identified issues.

### Recommended Actions

1. Review failed test output for specific error messages
2. Check database connectivity and migration status
3. Verify API endpoint configurations
4. Test frontend routes manually if automated tests failed
5. Run individual test scripts for more detailed debugging

EOF
fi

# Add troubleshooting section
cat >> "$REPORT_FILE" << EOF

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify PostgreSQL is running
   - Check database credentials in environment variables
   - Ensure database has required extensions (uuid-ossp, vector)

2. **API Endpoint Failures**
   - Check if backend server is running on correct port
   - Verify FastAPI application starts without errors
   - Review server logs for detailed error information

3. **Frontend Route Issues**
   - Ensure SvelteKit development server is running
   - Check for JavaScript errors in browser console
   - Verify API connectivity from frontend

4. **Migration Problems**
   - Run migration verification script individually
   - Check for data integrity issues
   - Review migration logs for specific errors

### Manual Testing

If automated tests fail, you can manually test the system:

1. **Backend API:** Visit \`http://localhost:8000/docs\` for API documentation
2. **Content URLs:** Test \`/api/content/dev/sample-slug\` endpoints
3. **Frontend Routes:** Navigate to \`/c/dev\`, \`/p/timeline\`, etc.
4. **Legacy Redirects:** Test old URLs like \`/items/{id}\` and \`/videos/{id}\`

### Files Generated

- **Full Report:** \`$REPORT_FILE\`
- **Test Results:** \`$RESULTS_DIR/*_$TIMESTAMP.*\`

EOF

echo ""
echo -e "${BLUE}📝 Report generated: $REPORT_FILE${NC}"
echo -e "${BLUE}📁 Test results saved in: $RESULTS_DIR/${NC}"

# Return appropriate exit code
if [ $TESTS_FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi