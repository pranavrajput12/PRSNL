#!/bin/bash

echo "🔧 Fixing FusionAuth Database Connection..."

# Stop FusionAuth
echo "Stopping FusionAuth..."
docker-compose -f docker-compose.auth.yml stop fusionauth

# Create FusionAuth database if it doesn't exist
echo "Ensuring FusionAuth database setup..."
/opt/homebrew/opt/postgresql@16/bin/psql -U pronav -p 5432 -d prsnl << EOF
-- Ensure FusionAuth schema exists
CREATE SCHEMA IF NOT EXISTS fusionauth;

-- Grant all privileges to pronav user on fusionauth schema
GRANT ALL PRIVILEGES ON SCHEMA fusionauth TO pronav;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA fusionauth TO pronav;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA fusionauth TO pronav;
ALTER DEFAULT PRIVILEGES IN SCHEMA fusionauth GRANT ALL ON TABLES TO pronav;
ALTER DEFAULT PRIVILEGES IN SCHEMA fusionauth GRANT ALL ON SEQUENCES TO pronav;

-- Set search path to include fusionauth
ALTER DATABASE prsnl SET search_path TO public, fusionauth;
EOF

# Remove FusionAuth volumes to force fresh setup
echo "Cleaning FusionAuth volumes..."
docker volume rm prsnl_fusionauth_config 2>/dev/null || true

# Start FusionAuth with a simpler configuration
echo "Starting FusionAuth with simplified config..."
docker run -d --rm \
  --name prsnl-fusionauth-temp \
  --network prsnl_prsnl-network \
  -p 9011:9011 \
  -e DATABASE_URL="jdbc:postgresql://host.docker.internal:5432/prsnl" \
  -e DATABASE_ROOT_USERNAME="pronav" \
  -e DATABASE_USERNAME="pronav" \
  -e FUSIONAUTH_APP_MEMORY="256M" \
  -e FUSIONAUTH_APP_RUNTIME_MODE="development" \
  -e SEARCH_TYPE="database" \
  fusionauth/fusionauth-app:1.50.1

echo "Waiting for FusionAuth to initialize (30 seconds)..."
sleep 30

# Check status
echo "Checking FusionAuth status..."
curl -s http://localhost:9011 > /dev/null && echo "✅ FusionAuth is running!" || echo "❌ FusionAuth failed to start"

echo "
To access FusionAuth:
- URL: http://localhost:9011
- First time setup will create admin user
"