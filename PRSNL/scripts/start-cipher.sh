#!/bin/bash
# Start Cipher with Azure OpenAI for automatic memory in Claude Code

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PRSNL_DIR="$(dirname "$SCRIPT_DIR")"

echo "🧠 Starting Cipher Memory System for PRSNL"
echo "========================================="
echo ""

# Check if proxy is already running
if lsof -ti:8002 > /dev/null 2>&1; then
    echo "✅ Cipher Azure proxy already running on port 8002"
else
    echo "🚀 Starting Azure OpenAI proxy..."
    cd "$PRSNL_DIR/backend"
    source venv/bin/activate
    
    # Install required packages if needed
    pip install -q fastapi uvicorn openai python-dotenv
    
    # Start proxy in background
    cd "$SCRIPT_DIR"
    nohup python3 cipher-azure-proxy.py > cipher-proxy.log 2>&1 &
    echo "⏳ Waiting for proxy to start..."
    sleep 3
    
    # Check if proxy started successfully
    if curl -s http://localhost:8002/ > /dev/null; then
        echo "✅ Azure proxy started successfully"
    else
        echo "❌ Failed to start proxy. Check cipher-proxy.log"
        exit 1
    fi
fi

echo ""
echo "📝 Testing Cipher memory..."
export OPENAI_API_KEY="cipher-azure-proxy"
export OPENAI_API_BASE="http://localhost:8002/v1"

# Test cipher
if cipher --version > /dev/null 2>&1; then
    echo "✅ Cipher v$(cipher --version) is ready"
    echo ""
    echo "🎉 Automatic memory is now active for Claude Code!"
    echo ""
    echo "Tips:"
    echo "- Cipher will automatically remember your development context"
    echo "- Use 'cipher recall <topic>' to search memories"
    echo "- Proxy logs: $SCRIPT_DIR/cipher-proxy.log"
    echo "- Stop proxy: lsof -ti:8002 | xargs kill -9"
else
    echo "❌ Cipher not working. Please check configuration."
    exit 1
fi