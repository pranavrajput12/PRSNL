#!/bin/bash

echo "🚂 PRSNL Railway Quick Setup"
echo "==========================="
echo ""
echo "⚠️  IMPORTANT: Set your Azure OpenAI API key before running:"
echo "export AZURE_OPENAI_API_KEY='your-api-key-here'"
echo ""
echo "This script will:"
echo "1. Create a new Railway project"
echo "2. Add PostgreSQL with pgvector"
echo "3. Deploy your backend"
echo "4. Give you the URL for your iOS app"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Navigate to backend
cd backend

# Login first
echo "📱 Step 1: Login to Railway"
echo "A browser window will open. Please login."
railway login

echo ""
echo "✅ Login successful!"
echo ""

# Create new project
echo "📦 Step 2: Creating new Railway project..."
railway init

echo ""
echo "🗄️  Step 3: Adding PostgreSQL database..."
echo "When prompted, select 'PostgreSQL'"
railway add

echo ""
echo "⚙️  Step 4: Setting environment variables..."

# Set all required environment variables
railway variables set PROJECT_NAME="PRSNL" \
  API_V1_STR="/api" \
  BACKEND_CORS_ORIGINS='["*"]' \
  ENVIRONMENT="production" \
  AZURE_OPENAI_API_KEY="${AZURE_OPENAI_API_KEY}" \
  AZURE_OPENAI_ENDPOINT="https://api.openai.com" \
  AZURE_OPENAI_DEPLOYMENT="gpt-4" \
  AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-ada-002" \
  AZURE_OPENAI_WHISPER_DEPLOYMENT="whisper-1" \
  AZURE_OPENAI_API_VERSION="2025-01-01-preview"

echo "✅ Environment variables set!"

echo ""
echo "🚀 Step 5: Deploying your backend..."
railway up

echo ""
echo "⏳ Waiting for deployment to complete..."
sleep 10

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo ""
echo "📱 Your backend URL is:"
railway open
echo ""
echo "To get the exact URL, run: railway status"
echo ""
echo "📲 Update your iOS app with the new URL in:"
echo "PRSNL-iOS/Implementation/PRSNL/Core/Services/APIConfiguration.swift"
echo ""
echo "Change this line:"
echo 'private let defaultBackendURL = "https://YOUR-APP-NAME.up.railway.app"'
echo ""
echo "🔍 To view logs: railway logs"
echo "📊 To view dashboard: railway open"