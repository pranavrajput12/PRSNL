#!/bin/bash
# Production startup script for PRSNL backend

cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/backend
source venv/bin/activate

# Set production environment
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export ENABLE_QUERY_LOGGING=false
export ENABLE_VERBOSE_LOGGING=false
export DEBUG_ROUTES=false

echo "Starting PRSNL backend in PRODUCTION mode..."
echo "Environment: $ENVIRONMENT"
echo "Log Level: $LOG_LEVEL"
echo "Query Logging: $ENABLE_QUERY_LOGGING"
echo "Verbose Logging: $ENABLE_VERBOSE_LOGGING"

# Start with production settings
uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info --no-access-log