#!/bin/bash
# Cipher MCP Aggregator Mode Environment Configuration
# Source this file to enable aggregator mode for command-line Cipher usage

# Azure OpenAI Configuration (Working solution recalled by Cipher)
export AZURE_OPENAI_API_KEY="1U6RGbb4XrVh4LUqG5qrNLHd1hvHeCDqseSThAayqhclju9nUCtTJQQJ99BAACHYHv6XJ3w3AAABACOG6tdK"
export AZURE_OPENAI_ENDPOINT="https://airops.openai.azure.com"
export AZURE_OPENAI_DEPLOYMENT="gpt-4.1"
export AZURE_OPENAI_MODEL="gpt-4.1"
export AZURE_OPENAI_VERSION="2025-01-01-preview"

# Working environment variables that Cipher confirmed working yesterday
export OPENAI_API_TYPE="azure"
export OPENAI_API_BASE="https://airops.openai.azure.com/"
export OPENAI_API_KEY="${AZURE_OPENAI_API_KEY}"
export AZURE_OPENAI_DEPLOYMENT="gpt-4.1"
export AZURE_OPENAI_MODEL="gpt-4.1"
export AZURE_OPENAI_VERSION="2025-01-01-preview"

# Qdrant Cloud Configuration (Fixed URL format)
export QDRANT_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.zuZKL-Zabs8ISY5yUXgTW_fL-BoEYbLD2OZrjhp1Vt8"
export QDRANT_URL="https://86c70065-df15-459b-bd8a-ab607b43341a.us-east4-0.gcp.cloud.qdrant.io:6333"
export QDRANT_COLLECTION="prsnl_cipher_patterns"

# MCP Aggregator Mode Configuration
export MCP_SERVER_MODE="aggregator"
export AGGREGATOR_CONFLICT_RESOLUTION="prefix"
export AGGREGATOR_TIMEOUT="60000"
export CIPHER_AUTO_CONTEXT="true"

# Enhanced Cipher Configuration
export CIPHER_CONFIG_PATH="/Users/pronav/Personal Knowledge Base/memAgent/cipher.yml"
export CIPHER_VECTOR_STORE="$HOME/.cipher/vector_store"
export CIPHER_DEBUG="false"
export CIPHER_VERBOSE="false"

# Development-specific settings
export CIPHER_DEV_MODE="true"
export CIPHER_PATTERN_ANALYSIS="true"
export CIPHER_CROSS_SESSION_LEARNING="true"
export CIPHER_AGENT_INTEGRATION="true"

# Session management
export CIPHER_SESSION_ID="prsnl-dev-$(date +%Y%m%d)"
export CIPHER_CONTEXT_WINDOW="10"
export CIPHER_MEMORY_SIZE="50000"

echo "🚀 Cipher MCP Aggregator Mode Environment Configured!"
echo "📊 Session ID: $CIPHER_SESSION_ID"
echo "🔧 Mode: $MCP_SERVER_MODE"
echo "⚡ Auto Context: $CIPHER_AUTO_CONTEXT"
echo "🛠️  Available Tools: Memory, Playwright, Filesystem, Git, SQLite"
echo ""
echo "Usage:"
echo "  cipher \"Store development insight\""
echo "  cipher recall \"search pattern\""
echo "  cipher --mode mcp  # Start MCP server with aggregator mode"
echo ""
echo "To enable these settings, run: source $0"