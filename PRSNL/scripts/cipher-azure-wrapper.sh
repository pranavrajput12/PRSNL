#!/bin/bash
# Wrapper script to use Azure OpenAI with Cipher
# Since Cipher expects OpenAI API, we'll use Azure OpenAI's OpenAI-compatible endpoint

# Load Azure OpenAI credentials from backend/.env
export $(grep -E '^AZURE_OPENAI_' /Users/pronav/Personal\ Knowledge\ Base/PRSNL/backend/.env | xargs)

# Azure OpenAI can be used with OpenAI SDK by setting base URL
export OPENAI_API_KEY="${AZURE_OPENAI_API_KEY}"
export OPENAI_API_BASE="${AZURE_OPENAI_ENDPOINT}/openai/deployments/${AZURE_OPENAI_DEPLOYMENT}"
export OPENAI_API_VERSION="${AZURE_OPENAI_API_VERSION}"

echo "🧠 Cipher with Azure OpenAI"
echo "Endpoint: ${AZURE_OPENAI_ENDPOINT}"
echo "Deployment: ${AZURE_OPENAI_DEPLOYMENT}"

# Run cipher with the arguments
cipher "$@"