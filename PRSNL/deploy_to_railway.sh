#!/bin/bash

echo "🚂 PRSNL Railway Deployment Script"
echo "================================="

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first:"
    echo "brew install railway"
    exit 1
fi

echo "✅ Railway CLI found"

# Navigate to backend directory
cd backend

echo ""
echo "📝 Steps to deploy:"
echo "1. Login to Railway (browser will open)"
railway login

echo ""
echo "2. Create a new project or link existing"
echo "Choose 'Create New Project' when prompted"
railway link

echo ""
echo "3. Adding PostgreSQL database with pgvector..."
railway add
echo "✅ Select 'PostgreSQL' from the list"

echo ""
echo "4. Setting environment variables..."
# Set required env vars
railway variables set PROJECT_NAME=PRSNL
railway variables set API_V1_STR=/api
railway variables set BACKEND_CORS_ORIGINS='["*"]'
railway variables set ENVIRONMENT=production

echo ""
echo "⚠️  IMPORTANT: Set your Azure OpenAI credentials:"
echo "railway variables set AZURE_OPENAI_API_KEY=your-key-here"
echo "railway variables set AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com"

echo ""
echo "5. Deploy the application..."
railway up

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "📱 Next steps:"
echo "1. Get your app URL: railway open"
echo "2. Update iOS app with the new URL"
echo "3. Test the connection"
echo ""
echo "📊 Monitor your app:"
echo "- Logs: railway logs"
echo "- Dashboard: railway open"