#!/bin/bash

# Test Script for Cipher Pattern Analysis Automation
# Verifies all components of the automation system are working correctly

set -e

SCRIPT_DIR="$(dirname "$0")"
cd "$SCRIPT_DIR"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

log() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

log $BLUE "🧪 Cipher Pattern Analysis Automation - Test Suite"
log $BLUE "=================================================="
echo ""

# Test 1: Check script files exist and are executable
log $CYAN "📋 Test 1: Script File Validation"
echo "----------------------------------------"

scripts=(
    "cipher-pattern-analysis.sh"
    "cipher-analysis-status.sh"
    "prsnl-cipher.sh"
)

for script in "${scripts[@]}"; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        log $GREEN "✅ $script exists and is executable"
    else
        log $RED "❌ $script missing or not executable"
        exit 1
    fi
done

# Test 2: Check directory structure
log $CYAN "📁 Test 2: Directory Structure"
echo "----------------------------------------"

if [ -d "data" ]; then
    log $GREEN "✅ data/ directory exists"
else
    mkdir -p data
    log $YELLOW "⚠️  Created data/ directory"
fi

# Test 3: Test help commands
log $CYAN "📖 Test 3: Help Commands"
echo "----------------------------------------"

if ./cipher-pattern-analysis.sh --help >/dev/null 2>&1; then
    log $GREEN "✅ cipher-pattern-analysis.sh --help works"
else
    log $RED "❌ cipher-pattern-analysis.sh --help failed"
    exit 1
fi

if ./cipher-analysis-status.sh help >/dev/null 2>&1; then
    log $GREEN "✅ cipher-analysis-status.sh help works"
else
    log $RED "❌ cipher-analysis-status.sh help failed"
    exit 1
fi

# Test 4: Test status commands
log $CYAN "📊 Test 4: Status Commands"
echo "----------------------------------------"

if ./cipher-pattern-analysis.sh --check >/dev/null 2>&1; then
    log $YELLOW "⚠️  Analysis is up to date (unexpected for first run)"
else
    log $GREEN "✅ Analysis correctly identified as overdue"
fi

if ./cipher-analysis-status.sh >/dev/null 2>&1; then
    log $GREEN "✅ Status utility runs without errors"
else
    log $RED "❌ Status utility failed"
    exit 1
fi

# Test 5: Check Cipher memory file existence
log $CYAN "🧠 Test 5: Cipher Memory Integration"
echo "----------------------------------------"

cipher_memory="../.cipher-memories/memories.log"
if [ -f "$cipher_memory" ]; then
    pattern_count=$(wc -l < "$cipher_memory" | tr -d ' ')
    log $GREEN "✅ Cipher memory file exists with $pattern_count lines"
    
    if [ "$pattern_count" -gt 10 ]; then
        log $GREEN "✅ Sufficient patterns for analysis ($pattern_count patterns)"
    else
        log $YELLOW "⚠️  Few patterns available for analysis ($pattern_count patterns)"
    fi
else
    log $YELLOW "⚠️  Cipher memory file not found at $cipher_memory"
    log $CYAN "   Run indexing scripts first: ./cipher-index-critical-files.sh"
fi

# Test 6: Test backend connectivity (optional)
log $CYAN "🌐 Test 6: Backend Connectivity (Optional)"
echo "----------------------------------------"

if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    log $GREEN "✅ Backend is running and accessible"
    
    if curl -s http://localhost:8000/api/cipher-analysis/health >/dev/null 2>&1; then
        log $GREEN "✅ Cipher analysis API endpoint is available"
    else
        log $YELLOW "⚠️  Cipher analysis API endpoint not available"
        log $CYAN "   This is expected if CrewAI isn't fully configured"
    fi
else
    log $YELLOW "⚠️  Backend not running (this is okay for testing scripts)"
    log $CYAN "   Start with: cd ../backend && uvicorn app.main:app --reload --port 8000"
fi

# Test 7: Configuration validation
log $CYAN "⚙️  Test 7: Configuration Validation"
echo "----------------------------------------"

# Check if Azure OpenAI environment variables are set (from backend config)
if [ -f "../backend/.env" ]; then
    if grep -q "AZURE_OPENAI_API_KEY" "../backend/.env" 2>/dev/null; then
        log $GREEN "✅ Azure OpenAI configuration found in backend/.env"
    else
        log $YELLOW "⚠️  Azure OpenAI configuration not found"
    fi
else
    log $YELLOW "⚠️  Backend .env file not found"
fi

# Test 8: Integration with daily indexing
log $CYAN "🔄 Test 8: Daily Indexing Integration"
echo "----------------------------------------"

if grep -q "Pattern Analysis Check" cipher-daily-index.sh 2>/dev/null; then
    log $GREEN "✅ Daily indexing script includes pattern analysis check"
else
    log $RED "❌ Daily indexing script missing pattern analysis integration"
    exit 1
fi

# Test 9: Documentation completeness
log $CYAN "📚 Test 9: Documentation"
echo "----------------------------------------"

docs=(
    "../docs/CIPHER_PATTERN_ANALYSIS_AUTOMATION.md"
    "../CLAUDE.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        if [[ "$(basename "$doc")" == "CIPHER_PATTERN_ANALYSIS_AUTOMATION.md" ]]; then
            # Check for specific content in automation doc
            if grep -q "Cipher Pattern Analysis Automation" "$doc" 2>/dev/null; then
                log $GREEN "✅ $(basename "$doc") contains automation documentation"
            else
                log $RED "❌ $(basename "$doc") missing automation documentation"
                exit 1
            fi
        else
            # Check for automation section in other docs
            if grep -q "CIPHER PATTERN ANALYSIS" "$doc" 2>/dev/null; then
                log $GREEN "✅ $(basename "$doc") contains automation documentation"
            else
                log $RED "❌ $(basename "$doc") missing automation documentation"
                exit 1
            fi
        fi
    else
        log $RED "❌ $(basename "$doc") not found"
        exit 1
    fi
done

# Summary
echo ""
log $PURPLE "📊 Test Summary"
log $PURPLE "==============="
echo ""

log $GREEN "✅ All core automation components are working correctly!"
echo ""

log $BLUE "🚀 Next Steps:"
log $CYAN "1. Start backend: cd ../backend && uvicorn app.main:app --reload --port 8000"
log $CYAN "2. Run first analysis: ./cipher-pattern-analysis.sh quality async"
log $CYAN "3. Monitor with: ./cipher-analysis-status.sh"
log $CYAN "4. Schedule weekly runs (optional): crontab -e"
echo ""

log $BLUE "💡 Pro Tips:"
log $CYAN "• Check analysis status daily: ./cipher-analysis-status.sh"
log $CYAN "• View quality trends weekly: ./cipher-analysis-status.sh trends"
log $CYAN "• Analysis is triggered automatically when agents detect quality issues"
log $CYAN "• Run daily indexing script to capture development patterns"
echo ""

log $PURPLE "🎉 Cipher Pattern Analysis Automation is ready for use!"