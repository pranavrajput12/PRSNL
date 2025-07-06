SHELL := /bin/bash

.PHONY: dev stop reset seed logs

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
