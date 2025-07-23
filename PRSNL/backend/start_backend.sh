#!/bin/bash
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/backend
source venv/bin/activate

# Check environment and start accordingly
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Starting PRSNL backend in PRODUCTION mode on port 8000..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
else
    echo "Starting PRSNL backend in DEVELOPMENT mode on port 8000..."
    uvicorn app.main:app --reload --port 8000 --log-level debug
fi