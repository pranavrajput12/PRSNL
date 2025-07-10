#!/bin/bash

# Process Lifecycle Management Script for PRSNL
# Kills processes on specific ports to resolve conflicts

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to kill process on a specific port
kill_port() {
    local port=$1
    local service=$2
    
    echo -e "${YELLOW}Checking port $port ($service)...${NC}"
    
    # Find process using the port
    local pid=$(lsof -ti:$port 2>/dev/null)
    
    if [ -z "$pid" ]; then
        echo -e "${GREEN}  ✓ Port $port is available${NC}"
    else
        # Get process info before killing
        local process_info=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
        echo -e "${RED}  ✗ Port $port is in use by process $pid ($process_info)${NC}"
        
        # Kill the process
        kill -9 $pid 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  ✓ Killed process $pid on port $port${NC}"
        else
            echo -e "${RED}  ✗ Failed to kill process $pid${NC}"
        fi
    fi
}

# Function to check if port is in use
check_port() {
    local port=$1
    local service=$2
    
    echo -e "${YELLOW}Port $port ($service):${NC}"
    
    local result=$(lsof -i:$port 2>/dev/null)
    if [ -z "$result" ]; then
        echo -e "${GREEN}  ✓ Available${NC}"
        return 0
    else
        echo -e "${RED}  ✗ In use:${NC}"
        echo "$result" | grep LISTEN | head -5
        return 1
    fi
}

# Main script
case "$1" in
    "kill")
        echo -e "${YELLOW}=== Killing processes on PRSNL ports ===${NC}"
        kill_port 8000 "Backend API"
        kill_port 3003 "Frontend"
        kill_port 5432 "PostgreSQL"
        kill_port 6379 "Redis"
        echo -e "${GREEN}=== Port cleanup complete ===${NC}"
        ;;
    
    "check")
        echo -e "${YELLOW}=== Checking PRSNL port usage ===${NC}"
        check_port 8000 "Backend API"
        check_port 3003 "Frontend"
        check_port 5432 "PostgreSQL"
        check_port 6379 "Redis"
        ;;
    
    "")
        echo "Usage: $0 {kill|check}"
        echo "  kill  - Kill processes on PRSNL ports"
        echo "  check - Check port availability"
        exit 1
        ;;
    
    *)
        echo "Invalid option: $1"
        echo "Usage: $0 {kill|check}"
        exit 1
        ;;
esac