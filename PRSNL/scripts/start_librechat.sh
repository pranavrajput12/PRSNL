#!/bin/bash

# PRSNL LibreChat Integration Startup Script
# ==========================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting PRSNL LibreChat Integration${NC}"
echo "================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️ .env file not found. Creating from template...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env from template${NC}"
    else
        echo -e "${RED}❌ No .env.example found. Please create .env manually.${NC}"
        exit 1
    fi
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Set default ports if not specified
export LIBRECHAT_PORT=${LIBRECHAT_PORT:-3080}
export BACKEND_PORT=${BACKEND_PORT:-8000}
export FRONTEND_PORT=${FRONTEND_PORT:-3004}

echo -e "${BLUE}📋 Configuration:${NC}"
echo "  LibreChat Port: $LIBRECHAT_PORT"
echo "  Backend Port: $BACKEND_PORT"
echo "  Frontend Port: $FRONTEND_PORT"
echo ""

# Check if Azure OpenAI API key is set
if [ -z "$AZURE_OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️ AZURE_OPENAI_API_KEY not set in .env${NC}"
    echo "LibreChat will not be able to connect to Azure OpenAI without this."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Generate secure keys for LibreChat if not provided
if ! grep -q "JWT_SECRET=" librechat.env 2>/dev/null; then
    echo -e "${YELLOW}⚠️ Generating secure JWT secrets for LibreChat...${NC}"
    JWT_SECRET=$(openssl rand -hex 32)
    JWT_REFRESH_SECRET=$(openssl rand -hex 32)
    CREDS_KEY=$(openssl rand -hex 32)
    CREDS_IV=$(openssl rand -hex 16)
    MEILI_KEY=$(openssl rand -hex 32)
    MONGO_PASSWORD=$(openssl rand -hex 16)
    
    # Update librechat.env with generated secrets
    sed -i.bak "s/your-super-secure-jwt-secret-change-this-in-production/$JWT_SECRET/g" librechat.env
    sed -i.bak "s/your-super-secure-refresh-secret-change-this-in-production/$JWT_REFRESH_SECRET/g" librechat.env
    sed -i.bak "s/your-super-secure-creds-key-change-this-in-production/$CREDS_KEY/g" librechat.env
    sed -i.bak "s/your-super-secure-creds-iv-change-this-in-production/$CREDS_IV/g" librechat.env
    sed -i.bak "s/your-meili-master-key-change-this/$MEILI_KEY/g" librechat.env
    
    # Export for docker-compose
    export LIBRECHAT_MEILI_KEY="$MEILI_KEY"
    export LIBRECHAT_MONGO_PASSWORD="$MONGO_PASSWORD"
    
    echo -e "${GREEN}✅ Generated secure keys for LibreChat${NC}"
fi

# Ensure PostgreSQL is running (local database)
echo -e "${BLUE}🔍 Checking PostgreSQL connection...${NC}"
if ! pg_isready -h localhost -p 5433 -U pronav > /dev/null 2>&1; then
    echo -e "${RED}❌ PostgreSQL is not running on localhost:5433${NC}"
    echo "Please start your local PostgreSQL instance and try again."
    echo "Expected connection: postgresql://pronav@localhost:5433/prsnl"
    exit 1
fi
echo -e "${GREEN}✅ PostgreSQL is running${NC}"

# Stop any existing LibreChat services
echo -e "${BLUE}🛑 Stopping existing LibreChat services...${NC}"
docker-compose down librechat librechat-mongo librechat-meilisearch librechat-rag 2>/dev/null || true

# Pull latest LibreChat images
echo -e "${BLUE}📦 Pulling latest LibreChat images...${NC}"
docker-compose pull librechat librechat-rag 2>/dev/null || {
    echo -e "${YELLOW}⚠️ Could not pull some images. Will use cached versions.${NC}"
}

# Start LibreChat services
echo -e "${BLUE}🚀 Starting LibreChat services...${NC}"
docker-compose up -d librechat-mongo librechat-meilisearch

# Wait for dependencies to be ready
echo -e "${BLUE}⏳ Waiting for dependencies to be ready...${NC}"
sleep 10

# Start LibreChat RAG API
echo -e "${BLUE}🧠 Starting LibreChat RAG API...${NC}"
docker-compose up -d librechat-rag

# Wait for RAG API to be ready
sleep 5

# Start main LibreChat service
echo -e "${BLUE}💬 Starting LibreChat main service...${NC}"
docker-compose up -d librechat

# Wait for services to start
echo -e "${BLUE}⏳ Waiting for LibreChat to be ready...${NC}"
sleep 15

# Health checks
echo -e "${BLUE}🏥 Running health checks...${NC}"

# Check LibreChat
if curl -f http://localhost:$LIBRECHAT_PORT/api/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ LibreChat is running on http://localhost:$LIBRECHAT_PORT${NC}"
else
    echo -e "${YELLOW}⚠️ LibreChat may still be starting up...${NC}"
fi

# Check PRSNL backend
if curl -f http://localhost:$BACKEND_PORT/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ PRSNL Backend is running on http://localhost:$BACKEND_PORT${NC}"
else
    echo -e "${YELLOW}⚠️ PRSNL Backend is not responding${NC}"
fi

# Check LibreChat bridge
if curl -f http://localhost:$BACKEND_PORT/api/ai/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ LibreChat Bridge is working${NC}"
else
    echo -e "${YELLOW}⚠️ LibreChat Bridge is not responding${NC}"
fi

echo ""
echo -e "${GREEN}🎉 LibreChat Integration Started!${NC}"
echo "================================================"
echo -e "${BLUE}Services:${NC}"
echo "  📊 PRSNL Frontend: http://localhost:$FRONTEND_PORT"
echo "  🔧 PRSNL Backend:  http://localhost:$BACKEND_PORT"
echo "  💬 LibreChat:      http://localhost:$LIBRECHAT_PORT"
echo "  🧠 Bridge API:     http://localhost:$BACKEND_PORT/api/ai"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Open LibreChat at http://localhost:$LIBRECHAT_PORT"
echo "2. Create an account or log in"
echo "3. Try the 'PRSNL Knowledge' model to test integration"
echo "4. Upload documents via RAG to test knowledge base features"
echo ""
echo -e "${YELLOW}📝 Note:${NC} First startup may take a few minutes for all services to be ready."

# Optionally show logs
read -p "Show LibreChat logs? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}📋 LibreChat Logs:${NC}"
    docker-compose logs -f librechat
fi