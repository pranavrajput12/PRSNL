#!/bin/bash
# Comprehensive AI Integration Test Runner
# Tests all AI features including Guardrails-AI and whisper.cpp

set -e  # Exit on error

echo "=================================================="
echo "🧪 PRSNL AI Integration Test Suite"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if service is running
check_service() {
    local service=$1
    local port=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${GREEN}✅ $service is running on port $port${NC}"
        return 0
    else
        echo -e "${RED}❌ $service is NOT running on port $port${NC}"
        return 1
    fi
}

# Function to run a test script
run_test() {
    local test_name=$1
    local test_script=$2
    
    echo ""
    echo -e "${YELLOW}Running: $test_name${NC}"
    echo "----------------------------------------"
    
    if python3 $test_script; then
        echo -e "${GREEN}✅ $test_name passed${NC}"
        return 0
    else
        echo -e "${RED}❌ $test_name failed${NC}"
        return 1
    fi
}

# Check prerequisites
echo "📋 Checking prerequisites..."
echo ""

# Check if backend is running
if ! check_service "Backend API" 8000; then
    echo ""
    echo "Please start the backend first:"
    echo "  cd backend && make dev"
    exit 1
fi

# Check if database is running
if ! check_service "PostgreSQL" 5432; then
    echo ""
    echo "Please ensure PostgreSQL is running"
    exit 1
fi

# Check Python dependencies
echo ""
echo "📦 Checking Python dependencies..."
python3 -c "import guardrails" 2>/dev/null && echo -e "${GREEN}✅ guardrails-ai installed${NC}" || echo -e "${YELLOW}⚠️  guardrails-ai not installed${NC}"
python3 -c "import pywhispercpp" 2>/dev/null && echo -e "${GREEN}✅ pywhispercpp installed${NC}" || echo -e "${YELLOW}⚠️  pywhispercpp not installed${NC}"

# Run tests
echo ""
echo "=================================================="
echo "🚀 Starting AI Integration Tests"
echo "=================================================="

# Track test results
FAILED_TESTS=0
TOTAL_TESTS=0

# Test 1: Guardrails-AI Validation
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_test "Guardrails-AI Validation" "scripts/test_guardrails_validation.py"; then
    :
else
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 2: whisper.cpp Integration
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_test "whisper.cpp Integration" "scripts/test_whisper_cpp_integration.py"; then
    :
else
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 3: Full AI Integration via API
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_test "AI API Integration" "scripts/test_ai_integrations.py"; then
    :
else
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 4: Haystack RAG Integration
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_test "Haystack RAG Integration" "scripts/test_haystack_rag.py"; then
    :
else
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Create sample audio file if needed
if [ ! -f "samples/test_audio.wav" ]; then
    echo ""
    echo "📝 Creating sample audio file for testing..."
    mkdir -p samples
    # Use text-to-speech or download a sample
    # For now, just note that it's missing
    echo -e "${YELLOW}⚠️  No test audio file found at samples/test_audio.wav${NC}"
    echo "   Some transcription tests will be skipped"
fi

# Summary
echo ""
echo "=================================================="
echo "📊 Test Summary"
echo "=================================================="
echo ""

PASSED_TESTS=$((TOTAL_TESTS - FAILED_TESTS))
echo "Total tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed! AI integrations are working correctly.${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some tests failed. Please check the output above.${NC}"
    exit 1
fi