SHELL := /bin/bash

.PHONY: dev stop reset seed logs kill-ports check-ports clean-dev test-health

# Define colors for output
GREEN=\033[0;32m
YELLOW=\033[0;33m
NC=\033[0m # No Color

# Navigate to the PRSNL directory
PRSNL_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

dev:
	@echo "$(GREEN)Starting all services...$(NC)"
	@cd $(PRSNL_DIR) && docker compose up -d --build
	@echo "$(YELLOW)Waiting for PostgreSQL to be ready...$(NC)"
	@until docker compose -f $(PRSNL_DIR)/docker compose.yml exec db pg_isready -U postgres -d prsnl > /dev/null 2>&1; do \
	  echo "$(YELLOW)PostgreSQL is unavailable - sleeping$(NC)"; \
	  sleep 2; \
	done
	@echo "$(GREEN)PostgreSQL is up and running.$(NC)"
	@echo "$(YELLOW)Applying database schema...$(NC)"
	@docker compose -f $(PRSNL_DIR)/docker compose.yml exec -T db psql -U postgres -d prsnl -f /app/db/schema.sql
	@echo "$(YELLOW)Waiting for Ollama to be ready...$(NC)"
	@until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do \
	  echo "$(YELLOW)Ollama is unavailable - sleeping$(NC)"; \
	  sleep 5; \
	done
	@echo "$(GREEN)Ollama is up and running.$(NC)"
	@echo "$(YELLOW)Downloading Ollama model: llama3...$(NC)"
	@curl -X POST http://localhost:11434/api/pull -d '{ "name": "llama3" }' > /dev/null 2>&1 || true
	@echo "$(GREEN)Development environment is ready!$(NC)"

stop:
	@echo "$(YELLOW)Stopping all services...$(NC)"
	@cd $(PRSNL_DIR) && docker compose down
	@echo "$(GREEN)All services stopped.$(NC)"

reset:
	@echo "$(YELLOW)Resetting database...$(NC)"
	@cd $(PRSNL_DIR) && docker compose down -v
	@echo "$(GREEN)Database reset. Run 'make dev' to re-initialize.$(NC)"

seed:
	@echo "$(GREEN)Seeding initial data...$(NC)"
	@cd $(PRSNL_DIR) && python3 scripts/seed_data.py
	@echo "$(GREEN)Data seeding complete.$(NC)"

logs:
	@echo "$(YELLOW)Showing all service logs (Ctrl+C to exit)...$(NC)"
	@cd $(PRSNL_DIR) && docker compose logs -f

# Process Lifecycle Management Commands

kill-ports:
	@echo "$(YELLOW)Killing processes on PRSNL ports...$(NC)"
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@lsof -ti:3003 | xargs kill -9 2>/dev/null || true
	@lsof -ti:5432 | xargs kill -9 2>/dev/null || true
	@lsof -ti:6379 | xargs kill -9 2>/dev/null || true
	@echo "$(GREEN)Ports cleared!$(NC)"

check-ports:
	@echo "$(YELLOW)Checking port usage...$(NC)"
	@echo "Port 8000 (Backend):"
	@lsof -i:8000 || echo "  ✓ Available"
	@echo "Port 3003 (Frontend):"
	@lsof -i:3003 || echo "  ✓ Available"
	@echo "Port 5432 (PostgreSQL):"
	@lsof -i:5432 || echo "  ✓ Available"
	@echo "Port 6379 (Redis):"
	@lsof -i:6379 || echo "  ✓ Available"

clean-dev: kill-ports stop
	@echo "$(YELLOW)Cleaning development environment...$(NC)"
	@rm -rf frontend/node_modules/.vite 2>/dev/null || true
	@rm -rf frontend/.svelte-kit 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Development environment cleaned!$(NC)"

test-health:
	@echo "$(YELLOW)Running smoke tests...$(NC)"
	@./scripts/smoke_test.sh

quick-test:
	@echo "$(YELLOW)Quick health check...$(NC)"
	@curl -s http://localhost:8000/health | jq . || echo "Backend not responding"
	@curl -s http://localhost:8000/api/health/ready | jq . || echo "Backend not ready"
	@curl -s http://localhost:8000/api/debug/routes | jq '.total_routes' || echo "Debug endpoint not available"
