#!/bin/bash

echo "Starting Celery workers for PRSNL..."

# Activate virtual environment
source venv/bin/activate

# Export Python path
export PYTHONPATH=/Users/pronav/Personal\ Knowledge\ Base/PRSNL/backend

# Kill any existing Celery workers
echo "Stopping any existing Celery workers..."
pkill -f "celery worker" || true

# Start Celery worker with all queues
echo "Starting Celery worker..."
celery -A app.workers.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=default,codemirror,ai_processing,media_processing,conversation_intelligence,knowledge_graph,agent_coordination \
    --hostname=worker@%h \
    --pool=prefork \
    > celery_worker.log 2>&1 &

echo "Celery worker started with PID: $!"

# Optional: Start Celery Beat for scheduled tasks
read -p "Do you want to start Celery Beat for scheduled tasks? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting Celery Beat..."
    celery -A app.workers.celery_app beat \
        --loglevel=info \
        > celery_beat.log 2>&1 &
    echo "Celery Beat started with PID: $!"
fi

echo "Done! Check celery_worker.log and celery_beat.log for output."
echo "To monitor: tail -f celery_worker.log"