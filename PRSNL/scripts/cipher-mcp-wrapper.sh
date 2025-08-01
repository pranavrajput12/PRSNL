#!/bin/bash
# Cipher MCP Wrapper for Claude Desktop
# This script ensures the Azure proxy is running and sets environment variables

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if proxy is running, start if not
if ! lsof -ti:8002 > /dev/null 2>&1; then
    cd "$SCRIPT_DIR"
    nohup python3 cipher-azure-proxy.py > cipher-proxy.log 2>&1 &
    sleep 2
fi

# Set environment variables for Cipher to use our proxy
export OPENAI_API_KEY="sk-cipher-azure-proxy"
export OPENAI_BASE_URL="http://localhost:8002/v1"

# Run cipher with MCP server mode
exec cipher --mode mcp