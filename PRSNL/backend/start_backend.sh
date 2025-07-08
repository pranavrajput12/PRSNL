#!/bin/bash
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/backend
source venv/bin/activate
echo "Starting PRSNL backend on port 8000..."
uvicorn app.main:app --reload --port 8000 --log-level debug