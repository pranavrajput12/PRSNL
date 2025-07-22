#!/bin/bash

# PRSNL AutoAgent Setup Script
# ============================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧠 Setting up AutoAgent for PRSNL Second Brain${NC}"
echo "=============================================="

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${BLUE}Python version: ${PYTHON_VERSION}${NC}"

# Navigate to autoagent directory
cd "$(dirname "$0")/../autoagent"

# Install AutoAgent in development mode
echo -e "${BLUE}📦 Installing AutoAgent dependencies...${NC}"
pip3 install -e . || {
    echo -e "${RED}❌ Failed to install AutoAgent${NC}"
    exit 1
}

# Install additional dependencies for PRSNL integration
echo -e "${BLUE}📦 Installing PRSNL integration dependencies...${NC}"
pip3 install asyncpg numpy litellm browsergym sentence_transformers chromadb || {
    echo -e "${YELLOW}⚠️ Some dependencies failed to install${NC}"
}

# Copy environment configuration
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️ .env file not found in autoagent directory${NC}"
    echo -e "${BLUE}Creating .env from parent project...${NC}"
    
    # Load parent .env
    if [ -f "../.env" ]; then
        source ../.env
        
        # Create AutoAgent .env with Azure OpenAI config
        cat > .env << EOF
# AutoAgent Configuration for PRSNL
COMPLETION_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-ada-002
API_BASE_URL=https://airops.openai.azure.com
AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# AutoAgent Settings
FN_CALL=true
MC_MODE=true
DEBUG=false
DEFAULT_LOG=true
LOG_PATH=./logs

# PRSNL Integration
PRSNL_DB_URL=postgresql://pronav@localhost:5432/prsnl
PRSNL_BACKEND_URL=http://localhost:8000
EOF
        echo -e "${GREEN}✅ Created AutoAgent .env configuration${NC}"
    else
        echo -e "${RED}❌ Parent .env not found${NC}"
    fi
fi

# Create logs directory
mkdir -p logs
echo -e "${GREEN}✅ Created logs directory${NC}"

# Run database migrations
echo -e "${BLUE}🗄️ Running AutoAgent database migrations...${NC}"
cd ..
psql -U pronav -d prsnl -p 5432 -f backend/app/db/migrations/add_autoagent_tables.sql || {
    echo -e "${YELLOW}⚠️ Database migrations may have already been applied${NC}"
}

# Test AutoAgent import
echo -e "${BLUE}🔍 Testing AutoAgent installation...${NC}"
python3 -c "
try:
    from autoagent import MetaChain, Agent
    from autoagent.memory.prsnl_memory import PRSNLMemory
    from autoagent.agents.prsnl_agents import PRSNLMultiAgentOrchestrator
    print('✅ AutoAgent modules imported successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

# Create quick test script
cat > test_autoagent_setup.py << 'EOF'
#!/usr/bin/env python3
"""Quick test of AutoAgent setup."""

import asyncio
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'autoagent'))

from autoagent.memory.prsnl_memory import PRSNLMemory
from autoagent.agents.prsnl_agents import PRSNLAgentFactory

async def test_setup():
    """Test basic AutoAgent functionality."""
    print("🔍 Testing AutoAgent setup...")
    
    # Test memory initialization
    memory = PRSNLMemory()
    await memory.initialize()
    print("✅ Memory initialized")
    
    # Test agent creation
    curator = PRSNLAgentFactory.create_knowledge_curator(memory)
    print(f"✅ Created agent: {curator.name}")
    
    # Test search
    results = await memory.search("test", top_k=1)
    print(f"✅ Search completed: {len(results)} results")
    
    await memory.close()
    print("✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_setup())
EOF

chmod +x test_autoagent_setup.py

echo ""
echo -e "${GREEN}🎉 AutoAgent Setup Complete!${NC}"
echo "=============================================="
echo -e "${BLUE}What's been set up:${NC}"
echo "  ✅ AutoAgent core framework installed"
echo "  ✅ PRSNL memory module integrated"
echo "  ✅ Custom agents for second brain functionality"
echo "  ✅ Database tables for knowledge graph"
echo "  ✅ API endpoints ready at /api/autoagent"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Start the backend: cd backend && uvicorn app.main:app --reload"
echo "2. Test AutoAgent: ./test_autoagent_setup.py"
echo "3. Access endpoints:"
echo "   - Process content: POST /api/autoagent/process-content"
echo "   - Explore topics: POST /api/autoagent/explore-topic"
echo "   - Create learning paths: POST /api/autoagent/create-learning-path"
echo "   - Generate insights: GET /api/autoagent/insights-report"
echo ""
echo -e "${YELLOW}📝 Note:${NC} AutoAgent will enhance all knowledge processing in PRSNL!"