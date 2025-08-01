#!/bin/bash

# Cipher Pattern Analysis Status Utility
# Quick status check and management for Cipher Pattern Analysis automation
# Usage: ./cipher-analysis-status.sh [command]

set -e

# Script configuration
SCRIPT_DIR="$(dirname "$0")"
MAIN_SCRIPT="$SCRIPT_DIR/cipher-pattern-analysis.sh"
LOG_FILE="$SCRIPT_DIR/data/cipher-analysis-runs.log"
ERROR_LOG="$SCRIPT_DIR/cipher-analysis-errors.log"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Function to log with color
log() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Function to get last run info
get_last_run() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "none"
        return 1
    fi
    
    tail -n 1 "$LOG_FILE"
}

# Function to count runs by status
count_runs_by_status() {
    local status="$1"
    if [ ! -f "$LOG_FILE" ]; then
        echo "0"
        return
    fi
    
    grep ",$status," "$LOG_FILE" 2>/dev/null | wc -l | tr -d ' '
}

# Function to get average quality score
get_average_quality() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "N/A"
        return
    fi
    
    local total=0
    local count=0
    
    tail -n +2 "$LOG_FILE" | grep ",success," | while IFS=',' read -r timestamp status duration pattern_count quality_score message; do
        if [[ "$quality_score" =~ ^[0-9.]+$ ]]; then
            total=$(echo "$total + $quality_score" | bc -l 2>/dev/null || echo "$total")
            count=$((count + 1))
        fi
    done 2>/dev/null
    
    if [ $count -gt 0 ]; then
        echo "scale=1; $total / $count" | bc -l 2>/dev/null | sed 's/^\./0./'
    else
        echo "N/A"
    fi
}

# Function to show quick status
show_quick_status() {
    log $BLUE "🔍 Cipher Pattern Analysis - Quick Status"
    log $BLUE "========================================"
    echo ""
    
    # Last run info
    local last_run=$(get_last_run)
    
    if [ "$last_run" = "none" ]; then
        log $YELLOW "⚠️  No analysis runs recorded"
        log $CYAN "   Run: $MAIN_SCRIPT to start first analysis"
        return 0
    fi
    
    # Parse last run
    IFS=',' read -r timestamp status duration pattern_count quality_score message <<< "$last_run"
    
    # Clean up quoted fields
    timestamp=$(echo "$timestamp" | tr -d '"')
    status=$(echo "$status" | tr -d '"')
    message=$(echo "$message" | tr -d '"')
    
    log $PURPLE "📅 Last Run: $timestamp"
    
    case "$status" in
        "success")
            log $GREEN "✅ Status: Success"
            log $CYAN "   Duration: ${duration}s"
            log $CYAN "   Patterns: $pattern_count"
            log $CYAN "   Quality: $quality_score%"
            ;;
        "error")
            log $RED "❌ Status: Error"
            log $CYAN "   Message: $message"
            ;;
        "started")
            log $YELLOW "⏳ Status: Running (Async)"
            log $CYAN "   Message: $message"
            ;;
    esac
    
    echo ""
    
    # Run statistics
    local total_runs=$(tail -n +2 "$LOG_FILE" 2>/dev/null | wc -l | tr -d ' ')
    local success_runs=$(count_runs_by_status "success")
    local error_runs=$(count_runs_by_status "error")
    local avg_quality=$(get_average_quality)
    
    log $BLUE "📊 Statistics:"
    log $CYAN "   Total Runs: $total_runs"
    log $CYAN "   Successful: $success_runs"
    log $CYAN "   Errors: $error_runs"
    log $CYAN "   Avg Quality: $avg_quality%"
    
    # Check if overdue
    echo ""
    if "$MAIN_SCRIPT" --check >/dev/null 2>&1; then
        log $GREEN "✅ Analysis is up to date"
    else
        log $YELLOW "⏰ Analysis is overdue (>7 days)"
        log $CYAN "   Recommend running: $MAIN_SCRIPT"
    fi
}

# Function to show detailed history
show_history() {
    log $BLUE "📈 Analysis Run History"
    log $BLUE "======================"
    echo ""
    
    if [ ! -f "$LOG_FILE" ]; then
        log $YELLOW "⚠️  No analysis history available"
        return 0
    fi
    
    local count=0
    
    # Show header
    printf "%-20s %-10s %-8s %-8s %-8s %s\n" "Timestamp" "Status" "Duration" "Patterns" "Quality" "Message"
    printf "%-20s %-10s %-8s %-8s %-8s %s\n" "--------------------" "----------" "--------" "--------" "--------" "-------"
    
    # Show last 10 runs
    tail -n +2 "$LOG_FILE" | tail -10 | while IFS=',' read -r timestamp status duration pattern_count quality_score message; do
        # Clean up quoted fields
        timestamp=$(echo "$timestamp" | tr -d '"' | cut -d' ' -f1)  # Just date
        status=$(echo "$status" | tr -d '"')
        message=$(echo "$message" | tr -d '"' | cut -c1-30)  # Truncate message
        
        case "$status" in
            "success")
                color=$GREEN
                status_icon="✅"
                ;;
            "error")
                color=$RED
                status_icon="❌"
                ;;
            "started")
                color=$YELLOW
                status_icon="⏳"
                ;;
            *)
                color=$NC
                status_icon="❓"
                ;;
        esac
        
        printf "${color}%-20s %-10s %-8s %-8s %-8s %s${NC}\n" \
            "$timestamp" "$status_icon $status" "${duration}s" "$pattern_count" "$quality_score%" "$message"
    done
}

# Function to show trends
show_trends() {
    log $BLUE "📈 Quality Trends"
    log $BLUE "================"
    echo ""
    
    if [ ! -f "$LOG_FILE" ]; then
        log $YELLOW "⚠️  No trend data available"
        return 0
    fi
    
    local last_5_success=$(tail -n +2 "$LOG_FILE" | grep ",success," | tail -5)
    
    if [ -z "$last_5_success" ]; then
        log $YELLOW "⚠️  No successful runs for trend analysis"
        return 0
    fi
    
    log $PURPLE "📊 Last 5 Successful Runs:"
    echo ""
    
    echo "$last_5_success" | while IFS=',' read -r timestamp status duration pattern_count quality_score message; do
        timestamp=$(echo "$timestamp" | tr -d '"' | cut -d' ' -f1)
        quality_score=$(echo "$quality_score" | tr -d '"')
        
        # Create simple bar chart
        local bar_length=$(echo "scale=0; $quality_score / 5" | bc -l 2>/dev/null || echo "10")
        local bar=""
        for i in $(seq 1 $bar_length); do
            bar="$bar▓"
        done
        
        printf "%-12s %5s%% %s\n" "$timestamp" "$quality_score" "$bar"
    done
    
    echo ""
    
    # Calculate trend
    local first_quality=$(echo "$last_5_success" | head -1 | cut -d',' -f5 | tr -d '"')
    local last_quality=$(echo "$last_5_success" | tail -1 | cut -d',' -f5 | tr -d '"')
    
    if [[ "$first_quality" =~ ^[0-9.]+$ ]] && [[ "$last_quality" =~ ^[0-9.]+$ ]]; then
        local trend=$(echo "scale=1; $last_quality - $first_quality" | bc -l 2>/dev/null || echo "0")
        
        if (( $(echo "$trend > 0" | bc -l 2>/dev/null || echo "0") )); then
            log $GREEN "📈 Trending UP: +$trend%"
        elif (( $(echo "$trend < 0" | bc -l 2>/dev/null || echo "0") )); then
            log $RED "📉 Trending DOWN: $trend%"
        else
            log $BLUE "➡️  Stable quality"
        fi
    fi
}

# Function to clean old logs
clean_logs() {
    log $BLUE "🧹 Cleaning Analysis Logs"
    log $BLUE "========================="
    echo ""
    
    if [ ! -f "$LOG_FILE" ]; then
        log $YELLOW "⚠️  No logs to clean"
        return 0
    fi
    
    local total_lines=$(wc -l < "$LOG_FILE")
    local keep_lines=31  # Header + 30 runs
    
    if [ $total_lines -le $keep_lines ]; then
        log $GREEN "✅ Logs are already clean ($((total_lines-1)) runs)"
        return 0
    fi
    
    # Backup current log
    cp "$LOG_FILE" "$LOG_FILE.backup"
    
    # Keep header + last 30 runs
    head -1 "$LOG_FILE" > "$LOG_FILE.tmp"
    tail -n +2 "$LOG_FILE" | tail -30 >> "$LOG_FILE.tmp"
    mv "$LOG_FILE.tmp" "$LOG_FILE"
    
    local removed=$((total_lines - keep_lines))
    
    log $GREEN "✅ Cleaned $removed old entries"
    log $CYAN "   Backup saved: $LOG_FILE.backup"
    log $CYAN "   Keeping: 30 most recent runs"
}

# Function to show next scheduled analysis
show_schedule() {
    log $BLUE "📅 Analysis Schedule"
    log $BLUE "==================="
    echo ""
    
    if [ ! -f "$LOG_FILE" ]; then
        log $YELLOW "⚠️  No previous runs to base schedule on"
        log $CYAN "   Recommended: Run analysis weekly"
        return 0
    fi
    
    local last_success=$(tail -n +2 "$LOG_FILE" | grep ",success," | tail -1 | cut -d',' -f1 | tr -d '"')
    
    if [ -z "$last_success" ]; then
        log $YELLOW "⚠️  No successful runs found"
        log $CYAN "   Recommended: Run analysis immediately"
        return 0
    fi
    
    # Calculate next recommended run (7 days after last success)
    local last_timestamp=$(date -d "$last_success" +%s 2>/dev/null || echo 0)
    local next_timestamp=$((last_timestamp + 604800))  # +7 days
    local next_date=$(date -d "@$next_timestamp" '+%Y-%m-%d %H:%M' 2>/dev/null || echo "Unknown")
    local current_timestamp=$(date +%s)
    
    log $PURPLE "📅 Last Successful Run: $last_success"
    log $CYAN "📅 Next Recommended Run: $next_date"
    
    if [ $current_timestamp -gt $next_timestamp ]; then
        log $YELLOW "⏰ Analysis is overdue!"
        log $CYAN "   Run: $MAIN_SCRIPT"
    else
        local days_until=$(( (next_timestamp - current_timestamp) / 86400 ))
        log $GREEN "✅ Analysis is up to date ($days_until days remaining)"
    fi
    
    echo ""
    log $BLUE "💡 Automation Tips:"
    log $CYAN "   • Add to crontab for weekly automation:"
    log $CYAN "     0 2 * * 0 $MAIN_SCRIPT quality async"
    log $CYAN "   • Check status daily with: $0"
    log $CYAN "   • Run on-demand with: $MAIN_SCRIPT"
}

# Function to show usage
show_usage() {
    log $BLUE "Cipher Pattern Analysis Status Utility"
    log $BLUE "======================================"
    echo ""
    log $CYAN "Usage: $0 [command]"
    echo ""
    log $YELLOW "Commands:"
    log $CYAN "  status      Show quick status (default)"
    log $CYAN "  history     Show detailed run history"
    log $CYAN "  trends      Show quality trends and analysis"
    log $CYAN "  schedule    Show next scheduled analysis time"
    log $CYAN "  clean       Clean old log entries (keep last 30)"
    log $CYAN "  summary     Show comprehensive summary"
    echo ""
    log $YELLOW "Examples:"
    log $CYAN "  $0              # Quick status"
    log $CYAN "  $0 history      # Show run history"
    log $CYAN "  $0 trends       # Show quality trends"
    log $CYAN "  $0 clean        # Clean old logs"
    echo ""
}

# Main function
main() {
    local command="${1:-status}"
    
    case "$command" in
        "status"|"--status"|"-s")
            show_quick_status
            ;;
        "history"|"--history"|"-h")
            show_history
            ;;
        "trends"|"--trends"|"-t")
            show_trends
            ;;
        "schedule"|"--schedule"|"-c")
            show_schedule
            ;;
        "clean"|"--clean")
            clean_logs
            ;;
        "summary"|"--summary")
            show_quick_status
            echo ""
            show_trends
            echo ""
            show_schedule
            ;;
        "help"|"--help")
            show_usage
            ;;
        *)
            log $RED "❌ Unknown command: $command"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"