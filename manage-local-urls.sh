#!/bin/bash

# Local URL Manager Script
# Manages local development URLs and ngrok tunnels

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}Port $port is already in use${NC}"
        return 1
    else
        echo -e "${GREEN}Port $port is available${NC}"
        return 0
    fi
}

# Function to list all active services
list_services() {
    echo -e "${BLUE}=== Active Local Services ===${NC}"
    echo ""
    
    # Check common ports
    for port in 3000 3001 3002 3003 4000 5173 8000 8001 8080 5432 6379; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
            service=$(lsof -i :$port | grep LISTEN | awk '{print $1}' | head -1)
            echo -e "${GREEN}Port $port:${NC} $service"
        fi
    done
    echo ""
}

# Function to start ngrok tunnel
start_ngrok() {
    local port=$1
    local name=$2
    
    if ! command -v ngrok &> /dev/null; then
        echo -e "${RED}ngrok is not installed. Installing...${NC}"
        brew install ngrok
    fi
    
    echo -e "${BLUE}Starting ngrok tunnel for $name on port $port...${NC}"
    ngrok http $port
}

# Function to kill service on port
kill_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}Killing process on port $port...${NC}"
        kill -9 $(lsof -ti :$port)
        echo -e "${GREEN}Process killed${NC}"
    else
        echo -e "${BLUE}No process running on port $port${NC}"
    fi
}

# Function to start PRSNL project
start_prsnl() {
    echo -e "${BLUE}Starting PRSNL project...${NC}"
    
    # Check if backend is running (Docker)
    if ! docker ps | grep prsnl_backend > /dev/null; then
        echo -e "${BLUE}Starting backend...${NC}"
        cd ~/Personal\ Knowledge\ Base/PRSNL
        docker-compose up -d
    else
        echo -e "${GREEN}Backend already running${NC}"
    fi
    
    # Start frontend
    if check_port 3002; then
        echo -e "${BLUE}Starting frontend...${NC}"
        cd ~/Personal\ Knowledge\ Base/PRSNL/frontend
        npm run dev &
    else
        echo -e "${RED}Frontend port 3002 already in use${NC}"
    fi
}

# Main menu
case "$1" in
    list)
        list_services
        ;;
    check)
        check_port $2
        ;;
    ngrok)
        start_ngrok $2 $3
        ;;
    kill)
        kill_port $2
        ;;
    start-prsnl)
        start_prsnl
        ;;
    *)
        echo "Local URL Manager"
        echo ""
        echo "Usage: $0 {list|check|ngrok|kill|start-prsnl}"
        echo ""
        echo "Commands:"
        echo "  list                - List all active services"
        echo "  check <port>        - Check if port is available"
        echo "  ngrok <port> <name> - Start ngrok tunnel"
        echo "  kill <port>         - Kill process on port"
        echo "  start-prsnl         - Start PRSNL project"
        echo ""
        echo "Examples:"
        echo "  $0 list"
        echo "  $0 check 3000"
        echo "  $0 ngrok 3002 prsnl-frontend"
        echo "  $0 kill 3000"
        ;;
esac