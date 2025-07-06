#!/bin/bash

set -e

echo "Setting up PRSNL development environment..."

# 1. Check for Docker and docker-compose
if ! command -v docker &> /dev/null
then
    echo "Docker is not installed. Please install Docker Desktop: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null
then
    echo "docker-compose is not installed. Please install it or ensure Docker Desktop is running."
    exit 1
fi

# Navigate to the PRSNL directory
cd $(dirname "$0")/..

# 2. Create .env file from .env.example if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env from .env.example"
    cp .env.example .env
else
    echo ".env file already exists. Skipping creation."
fi

# 3. Run docker-compose up -d
echo "Starting Docker services..."
docker-compose up -d

# 4. Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until docker-compose exec db pg_isready -U postgres -d prsnl
do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "PostgreSQL is up and running."

# 5. Run database migrations (apply schema.sql)
echo "Applying database schema..."
docker-compose exec -T db psql -U postgres -d prsnl -f /app/db/schema.sql

# 6. Install Ollama and download llama3 model
echo "Checking Ollama service..."
until curl -s http://localhost:11434/api/tags > /dev/null
do
  echo "Ollama is not ready - sleeping"
  sleep 5
done
echo "Ollama is up and running."

echo "Downloading Ollama model: llama3..."
curl -X POST http://localhost:11434/api/pull -d '{ "name": "llama3" }'

# 7. Seed initial data
echo "Seeding initial data..."
python3 scripts/seed_data.py

# 8. Start the backend server (assuming it's part of docker-compose or run separately)
echo "Development environment setup complete. You can now start the backend server (e.g., 'make dev' or 'uvicorn app.main:app --reload' in backend/app)."
