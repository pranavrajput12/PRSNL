#!/bin/bash

# Cipher Memory Storage Script for PRSNL
# This script stores important project memories using Cipher CLI

# Set environment variables for Azure OpenAI
export OPENAI_API_KEY="sk-dummy-key-for-cli-validation"
export AZURE_OPENAI_API_KEY="1U6RGbb4XrVh4LUqG5qrNLHd1hvHeCDqseSThAayqhclju9nUCtTJQQJ99BAACHYHv6XJ3w3AAABACOG6tdK"
export AZURE_OPENAI_ENDPOINT="https://airops.openai.azure.com/"

echo "🧠 Storing PRSNL Project Memories in Cipher..."
echo "============================================"

# Project Context
echo "📁 Storing project context..."
cipher "PRSNL Project Context: Personal Knowledge Management system with FastAPI backend (port 8000), SvelteKit frontend (port 3004), PostgreSQL ARM64 (port 5432), DragonflyDB (port 6379). Uses Azure OpenAI for AI features."

# Architecture Details
echo "🏗️ Storing architecture details..."
cipher "PRSNL Architecture: ARM64 Mac Mini M4, local PostgreSQL (NOT Docker), pgvector from /opt/homebrew. Frontend dev port 3004, production 3003. Rancher Desktop for containers."

# Key Files
echo "📄 Storing key file locations..."
cipher "PRSNL Key Files: CLAUDE.md (project config), TASK_HISTORY.md (task tracking), DATABASE_SCHEMA.md (DB structure), CURRENT_SESSION_STATE.md (active work), CRASH_RECOVERY_GUIDE.md (recovery procedures)"

# Common Commands
echo "⌨️ Storing common commands..."
cipher "PRSNL Daily Startup: cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL && git pull && cd backend && source venv/bin/activate && cd .. && make check-ports"
cipher "PRSNL Kill Ports: lsof -ti:8000 | xargs kill -9 && lsof -ti:3004 | xargs kill -9"
cipher "PRSNL Backend Start: cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000"
cipher "PRSNL Frontend Start: cd frontend && npm run dev -- --port 3004"

# Error Solutions
echo "🔧 Storing error solutions..."
cipher "PRSNL pgvector fix: Always use ARM64 PostgreSQL from /opt/homebrew/opt/postgresql@16"
cipher "PRSNL port conflict fix: Run 'make kill-ports' or manually kill with lsof commands"
cipher "PRSNL 500 error fix: Check missing database columns, especially content_type and enable_summarization"

# Testing Commands
echo "🧪 Storing testing commands..."
cipher "PRSNL API Health: curl http://localhost:8000/health"
cipher "PRSNL Dreamscape Test: curl http://localhost:8000/api/persona/health"
cipher "PRSNL AI Test: curl -X POST http://localhost:8000/api/ai/health"
cipher "PRSNL Capture Test: Test with auto content type and AI summarization enabled"

# Recent Fixes
echo "🔨 Storing recent fixes..."
cipher "Cipher Azure Fix: Use provider:azure not azure_openai in cipher.yml. Set dummy OPENAI_API_KEY='sk-dummy-key-for-cli-validation' to bypass CLI validation bug. Use absolute paths in MCP config."
cipher "PRSNL Chrome Extension Fix: Remove CDN scripts causing CSP violations. See CIPHER_AZURE_INTEGRATION_GUIDE.md for details."

# Development Patterns
echo "💡 Storing development patterns..."
cipher "PRSNL SvelteKit Pattern: Use +page.server.ts for SSR, handle errors with proper status codes, use data-testid for Playwright tests"
cipher "PRSNL FastAPI Pattern: Use dependency injection, async/await everywhere, HTTPException for errors, Pydantic for validation"
cipher "PRSNL Testing Pattern: Playwright for e2e tests, test error cases, use comprehensive test matrices"

echo ""
echo "✅ PRSNL memories stored successfully!"
echo ""
echo "💡 Quick recall examples:"
echo "   cipher recall 'PRSNL ports'"
echo "   cipher recall 'pgvector fix'"
echo "   cipher recall 'daily startup'"