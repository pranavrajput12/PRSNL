#!/bin/bash

# Cipher Pattern Analysis Automation Script
# Automatically analyzes Cipher patterns using CrewAI for continuous improvement
# Usage: ./cipher-pattern-analysis.sh [analysis_type] [mode]
# Examples:
#   ./cipher-pattern-analysis.sh                    # Full analysis, sync mode
#   ./cipher-pattern-analysis.sh quality async     # Quality analysis, async mode
#   ./cipher-pattern-analysis.sh full sync         # Full analysis, sync mode

set -e  # Exit on any error

# Script configuration
SCRIPT_DIR="$(dirname "$0")"
LOG_FILE="$SCRIPT_DIR/data/cipher-analysis-runs.log"
ERROR_LOG="$SCRIPT_DIR/cipher-analysis-errors.log"
BACKEND_URL="http://localhost:8000"  # Configurable backend URL
ANALYSIS_TIMEOUT=300  # 5 minutes timeout

# Ensure log directory exists
mkdir -p "$SCRIPT_DIR/data"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to log with color
log() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Function to log errors
log_error() {
    local message="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $message" >> "$ERROR_LOG"
    log $RED "❌ ERROR: $message"
}

# Function to log to run history
log_run() {
    local status="$1"
    local duration="$2"
    local pattern_count="$3"
    local quality_score="$4"
    local message="$5"
    
    # Create header if log file doesn't exist
    if [ ! -f "$LOG_FILE" ]; then
        echo "timestamp,status,duration_seconds,pattern_count,quality_score,message" > "$LOG_FILE"
    fi
    
    echo "$(date '+%Y-%m-%d %H:%M:%S'),$status,$duration,$pattern_count,$quality_score,\"$message\"" >> "$LOG_FILE"
}

# Function to store results in Cipher memory
store_in_cipher() {
    local pattern="$1"
    if [ -f "$SCRIPT_DIR/prsnl-cipher.sh" ]; then
        "$SCRIPT_DIR/prsnl-cipher.sh" store "$pattern" 2>/dev/null || true
    fi
}

# Function to check if backend is running
check_backend() {
    log $BLUE "🔍 Checking backend availability..."
    
    if ! curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
        log_error "Backend not available at $BACKEND_URL"
        log $RED "   Please start the backend server:"
        log $RED "   cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000"
        return 1
    fi
    
    # Check if cipher analysis endpoint is available
    if ! curl -s "$BACKEND_URL/api/cipher-analysis/health" > /dev/null 2>&1; then
        log_error "Cipher analysis endpoint not available"
        return 1
    fi
    
    log $GREEN "✅ Backend is available"
    return 0
}

# Function to get current pattern statistics
get_pattern_stats() {
    local stats_response
    stats_response=$(curl -s "$BACKEND_URL/api/cipher-analysis/stats" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ ! -z "$stats_response" ]; then
        echo "$stats_response"
        return 0
    else
        return 1
    fi
}

# Function to check if analysis is overdue
is_analysis_overdue() {
    if [ ! -f "$LOG_FILE" ]; then
        return 0  # No previous runs, analysis is overdue
    fi
    
    local last_success=$(tail -n +2 "$LOG_FILE" | grep ",success," | tail -1 | cut -d',' -f1)
    
    if [ -z "$last_success" ]; then
        return 0  # No successful runs, analysis is overdue
    fi
    
    # Check if last successful run was more than 7 days ago
    local last_timestamp=$(date -d "$last_success" +%s 2>/dev/null || echo 0)
    local current_timestamp=$(date +%s)
    local week_in_seconds=604800  # 7 days
    
    if [ $((current_timestamp - last_timestamp)) -gt $week_in_seconds ]; then
        return 0  # Analysis is overdue
    else
        return 1  # Analysis is not overdue
    fi
}

# Function to run pattern analysis
run_analysis() {
    local analysis_type="${1:-full}"
    local mode="${2:-sync}"
    local start_time=$(date +%s)
    
    log $PURPLE "🚀 Starting Cipher Pattern Analysis"
    log $CYAN "   Analysis Type: $analysis_type"
    log $CYAN "   Mode: $mode"
    log $CYAN "   Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # Get initial pattern statistics
    local initial_stats
    initial_stats=$(get_pattern_stats)
    
    if [ $? -ne 0 ]; then
        log_error "Could not retrieve initial pattern statistics"
        log_run "error" "0" "0" "0" "Failed to get initial stats"
        return 1
    fi
    
    local pattern_count=$(echo "$initial_stats" | grep -o '"total_patterns":[0-9]*' | cut -d':' -f2)
    local initial_quality=$(echo "$initial_stats" | grep -o '"quality_score":[0-9.]*' | cut -d':' -f2)
    
    log $BLUE "📊 Initial Statistics:"
    log $CYAN "   Total Patterns: $pattern_count"
    log $CYAN "   Quality Score: $initial_quality%"
    echo ""
    
    # Prepare analysis request
    local async_flag="false"
    if [ "$mode" = "async" ]; then
        async_flag="true"
    fi
    
    local request_body="{
        \"analysis_type\": \"$analysis_type\",
        \"improvement_focus\": \"all\",
        \"async_mode\": $async_flag
    }"
    
    log $BLUE "🔬 Triggering Pattern Analysis..."
    
    # Call analysis API
    local analysis_response
    analysis_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$request_body" \
        "$BACKEND_URL/api/cipher-analysis/analyze" \
        --max-time $ANALYSIS_TIMEOUT)
    
    if [ $? -ne 0 ]; then
        local duration=$(($(date +%s) - start_time))
        log_error "Analysis API call failed (timeout or connection error)"
        log_run "error" "$duration" "$pattern_count" "$initial_quality" "API call failed"
        return 1
    fi
    
    # Parse response
    local status=$(echo "$analysis_response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    local analysis_id=$(echo "$analysis_response" | grep -o '"analysis_id":"[^"]*"' | cut -d'"' -f4)
    
    if [ "$status" = "started" ] && [ "$mode" = "async" ]; then
        log $YELLOW "⏳ Analysis started in background mode"
        log $CYAN "   Analysis ID: $analysis_id"
        log $CYAN "   Check status with: curl $BACKEND_URL/api/cipher-analysis/status/$analysis_id"
        
        local duration=$(($(date +%s) - start_time))
        log_run "started" "$duration" "$pattern_count" "$initial_quality" "Async analysis started: $analysis_id"
        
        store_in_cipher "PATTERN ANALYSIS: Started async analysis $analysis_id at $(date '+%Y-%m-%d %H:%M')"
        
        return 0
        
    elif [ "$status" = "completed" ]; then
        log $GREEN "✅ Analysis completed successfully!"
        
        # Extract recommendations and next steps
        local recommendations=$(echo "$analysis_response" | grep -o '"recommendations":\[[^]]*\]' | sed 's/"recommendations"://g' | tr -d '[]"' | tr ',' '\n')
        local next_steps=$(echo "$analysis_response" | grep -o '"next_steps":\[[^]]*\]' | sed 's/"next_steps"://g' | tr -d '[]"' | tr ',' '\n')
        
        # Get final statistics
        sleep 2  # Brief delay for any updates to propagate
        local final_stats=$(get_pattern_stats)
        local final_quality=$(echo "$final_stats" | grep -o '"quality_score":[0-9.]*' | cut -d':' -f2)
        
        local duration=$(($(date +%s) - start_time))
        
        log $GREEN "📈 Analysis Results:"
        log $CYAN "   Duration: ${duration}s"
        log $CYAN "   Final Quality Score: $final_quality%"
        
        if [ ! -z "$recommendations" ]; then
            log $BLUE "💡 Key Recommendations:"
            echo "$recommendations" | head -3 | while read -r rec; do
                [ ! -z "$rec" ] && log $CYAN "   • $rec"
            done
        fi
        
        if [ ! -z "$next_steps" ]; then
            log $BLUE "🎯 Next Steps:"
            echo "$next_steps" | head -3 | while read -r step; do
                [ ! -z "$step" ] && log $CYAN "   • $step"
            done
        fi
        
        # Log success
        log_run "success" "$duration" "$pattern_count" "$final_quality" "Analysis completed successfully"
        
        # Store in Cipher memory
        store_in_cipher "PATTERN ANALYSIS: Completed at $(date '+%Y-%m-%d %H:%M') - Quality: $final_quality%, Duration: ${duration}s"
        
        if [ ! -z "$recommendations" ]; then
            echo "$recommendations" | head -5 | while read -r rec; do
                [ ! -z "$rec" ] && store_in_cipher "ANALYSIS INSIGHT: $rec"
            done
        fi
        
        return 0
        
    else
        local duration=$(($(date +%s) - start_time))
        log_error "Analysis failed with status: $status"
        log_run "error" "$duration" "$pattern_count" "$initial_quality" "Analysis failed: $status"
        return 1
    fi
}

# Function to show usage
show_usage() {
    log $BLUE "Cipher Pattern Analysis Automation"
    log $BLUE "=================================="
    echo ""
    log $CYAN "Usage: $0 [analysis_type] [mode]"
    echo ""
    log $YELLOW "Analysis Types:"
    log $CYAN "  full          Comprehensive analysis (default)"
    log $CYAN "  quality       Focus on pattern quality issues"
    log $CYAN "  relationships Focus on pattern relationships"
    log $CYAN "  gaps          Focus on knowledge gaps"
    log $CYAN "  optimization  Focus on format optimization"
    echo ""
    log $YELLOW "Modes:"
    log $CYAN "  sync          Synchronous analysis (default)"
    log $CYAN "  async         Asynchronous analysis"
    echo ""
    log $YELLOW "Examples:"
    log $CYAN "  $0                        # Full sync analysis"
    log $CYAN "  $0 quality async          # Quality analysis in background"
    log $CYAN "  $0 relationships sync     # Relationship analysis, wait for completion"
    echo ""
    log $YELLOW "Status Commands:"
    log $CYAN "  $0 --status               # Show last run status"
    log $CYAN "  $0 --check                # Check if analysis is overdue"
    echo ""
}

# Function to show status
show_status() {
    log $BLUE "📊 Cipher Pattern Analysis Status"
    log $BLUE "================================="
    echo ""
    
    if [ ! -f "$LOG_FILE" ]; then
        log $YELLOW "⚠️  No analysis runs recorded yet"
        log $CYAN "   Run: $0 to start first analysis"
        return 0
    fi
    
    # Show last few runs
    log $PURPLE "📈 Recent Analysis Runs:"
    echo ""
    
    tail -n 6 "$LOG_FILE" | head -1  # Header
    tail -n 5 "$LOG_FILE" | while IFS=',' read -r timestamp status duration pattern_count quality_score message; do
        case "$status" in
            "success")
                log $GREEN "✅ $timestamp | Duration: ${duration}s | Quality: $quality_score% | Patterns: $pattern_count"
                ;;
            "error")
                log $RED "❌ $timestamp | $message"
                ;;
            "started")
                log $YELLOW "⏳ $timestamp | Background analysis started"
                ;;
        esac
    done
    
    echo ""
    
    # Check if analysis is overdue
    if is_analysis_overdue; then
        log $YELLOW "⏰ Analysis is overdue (>7 days since last successful run)"
        log $CYAN "   Run: $0 to perform analysis"
    else
        log $GREEN "✅ Analysis is up to date"
    fi
    
    # Show current pattern stats if backend is available
    if check_backend >/dev/null 2>&1; then
        local current_stats=$(get_pattern_stats)
        if [ $? -eq 0 ]; then
            local pattern_count=$(echo "$current_stats" | grep -o '"total_patterns":[0-9]*' | cut -d':' -f2)
            local quality_score=$(echo "$current_stats" | grep -o '"quality_score":[0-9.]*' | cut -d':' -f2)
            
            echo ""
            log $BLUE "📊 Current Pattern Statistics:"
            log $CYAN "   Total Patterns: $pattern_count"
            log $CYAN "   Quality Score: $quality_score%"
        fi
    fi
}

# Main script logic
main() {
    local analysis_type="${1:-full}"
    local mode="${2:-sync}"
    
    # Handle special commands
    case "$analysis_type" in
        "--help"|"-h")
            show_usage
            exit 0
            ;;
        "--status"|"-s")
            show_status
            exit 0
            ;;
        "--check"|"-c")
            if is_analysis_overdue; then
                log $YELLOW "⏰ Analysis is overdue"
                exit 1
            else
                log $GREEN "✅ Analysis is up to date"
                exit 0
            fi
            ;;
    esac
    
    # Validate analysis type
    case "$analysis_type" in
        "full"|"quality"|"relationships"|"gaps"|"optimization")
            ;;
        *)
            log_error "Invalid analysis type: $analysis_type"
            show_usage
            exit 1
            ;;
    esac
    
    # Validate mode
    case "$mode" in
        "sync"|"async")
            ;;
        *)
            log_error "Invalid mode: $mode"
            show_usage
            exit 1
            ;;
    esac
    
    # Check backend availability
    if ! check_backend; then
        exit 1
    fi
    
    # Run the analysis
    if run_analysis "$analysis_type" "$mode"; then
        log $GREEN "🎉 Analysis completed successfully!"
        echo ""
        log $CYAN "💡 Pro Tips:"
        log $CYAN "   • View results: $0 --status"
        log $CYAN "   • Check for insights: ./prsnl-cipher.sh recall \"PATTERN ANALYSIS\""
        log $CYAN "   • Schedule weekly runs for continuous improvement"
        exit 0
    else
        log $RED "❌ Analysis failed. Check logs for details."
        exit 1
    fi
}

# Run main function with all arguments
main "$@"