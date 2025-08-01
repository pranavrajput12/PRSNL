#!/bin/bash

# Cipher Memory Seeding Script for PRSNL Development
# This script seeds essential PRSNL development memories into Cipher

echo "🧠 Seeding PRSNL Development Memories into Cipher..."

# Note: You'll need to fix the Azure OpenAI configuration first
# The current setup needs adjustment for proper Azure OpenAI compatibility

# Critical Architecture Memories
echo "📐 Adding architecture memories..."
cipher "CRITICAL: PRSNL uses PostgreSQL on port 5432 (ARM64 architecture). Verify with: lsof -ti:5432. pgvector must be installed via /opt/homebrew path, NOT /usr/local"

cipher "Frontend ports: Development=3004, Production container=3003. Always use 3004 for npm run dev. Port 3003 is for production deployments only."

cipher "Azure OpenAI deployments: gpt-4.1 (main reasoning), text-embedding-ada-002 (embeddings). API version: 2025-01-01-preview"

cipher "Authentication: Keycloak (port 8080) for SSO, FusionAuth (port 9011) for user management. JWT tokens: 1-hour access, 7-day refresh"

# Development Patterns
echo "🔧 Adding development patterns..."
cipher "Use Task agents for complex work: general-purpose (search/research), debug-accelerator (500 errors), ui-ux-optimizer (component audits)"

cipher "Testing with Playwright: npm test (all browsers), npm run test:ui (interactive), npm run test:debug (debugging), npm run test:headed (visible browser)"

cipher "Key files: CLAUDE.md (project guide), DATABASE_SCHEMA.md (complete schema), CRASH_RECOVERY_GUIDE.md (recovery procedures), SYSTEM_ARCHITECTURE_REPOSITORY.md (patterns)"

# Common Issues & Solutions
echo "🚨 Adding common issues and solutions..."
cipher "Port conflicts: Use 'lsof -ti:PORT | xargs kill -9' to kill processes, then restart services. Common ports: 8000 (backend), 3004 (frontend), 5432 (PostgreSQL)"

cipher "pgvector connection issues: 1) Check PostgreSQL is ARM64 (/opt/homebrew), 2) Verify port 5432, 3) Run: SELECT * FROM pg_extension WHERE extname = 'vector'"

cipher "Authentication bypass in development: WebSocket auth disabled, frontend uses dummy tokens. See SECURITY_BYPASSES.md. MUST FIX BEFORE PRODUCTION"

cipher "Backend startup failures: Check langgraph-checkpoint-sqlite package. Install with: pip3 install langgraph-checkpoint-sqlite"

# AI Integration Patterns
echo "🤖 Adding AI integration patterns..."
cipher "LangGraph workflows: State-based processing in backend/app/services/. Use SqliteSaver for persistence. CrewAI agents in backend/app/agents/"

cipher "Azure OpenAI integration: Use prsnl-gpt-4 for complex reasoning, gpt-4.1-mini for fast responses. LangChain templates in centralized prompt management"

cipher "AI Router: ReAct agent for intelligent provider selection. Test with: curl -X POST localhost:8000/api/ai-router/test-routing"

# Development Commands
echo "⚡ Adding development commands..."
cipher "Health checks: make test-health (smoke tests), curl localhost:8000/health (API), curl localhost:8000/api/ai/health (AI services)"

cipher "Port management: make kill-ports (kill all), make check-ports (status), lsof -ti:PORT | xargs kill -9 (specific port)"

cipher "Development environment: Backend venv at backend/venv, frontend npm at frontend/. ARM64 architecture (Mac M-series)"

echo "✅ Memory seeding complete! Test with: cipher recall 'PRSNL architecture'"
echo ""
echo "🔧 IMPORTANT: You may need to fix the Azure OpenAI configuration in ~/.cipher/memAgent/cipher.yml"
echo "   The API format might need adjustment for proper Azure OpenAI compatibility."