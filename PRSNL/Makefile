# PRSNL Development Makefile

.PHONY: help install install-backend install-frontend install-hooks format lint test clean

help:
	@echo "Available commands:"
	@echo "  make install         - Install all dependencies"
	@echo "  make install-backend - Install Python dependencies"
	@echo "  make install-frontend - Install Node.js dependencies"
	@echo "  make install-hooks   - Install pre-commit hooks"
	@echo "  make format          - Format all code"
	@echo "  make lint            - Run all linters"
	@echo "  make test            - Run all tests"
	@echo "  make clean           - Clean up generated files"

install: install-backend install-frontend install-hooks

install-backend:
	cd backend && python -m venv venv
	cd backend && ./venv/bin/pip install -r requirements-dev.txt

install-frontend:
	cd frontend && npm install

install-hooks:
	pre-commit install
	@echo "✅ Pre-commit hooks installed!"

format:
	# Python formatting
	cd backend && black .
	cd backend && isort .
	# JavaScript/TypeScript formatting
	cd frontend && npm run format
	@echo "✅ Code formatted!"

lint:
	# Python linting
	cd backend && flake8
	cd backend && mypy app
	# JavaScript/TypeScript linting
	cd frontend && npm run lint
	@echo "✅ Linting complete!"

test:
	# Run backend tests
	cd backend && pytest
	# Run frontend tests (when added)
	# cd frontend && npm test
	@echo "✅ Tests complete!"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	@echo "✅ Cleaned up!"