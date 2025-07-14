#!/bin/bash

# Start Celery workers for CodeMirror distributed processing

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Function to start a worker
start_worker() {
    local queue=$1
    local concurrency=$2
    local name=$3
    
    echo "Starting $name worker for queue: $queue"
    celery -A app.workers.celery_app worker \
        --loglevel=info \
        --queues=$queue \
        --concurrency=$concurrency \
        --hostname="$name@%h" \
        --pool=prefork &
}

# Start workers for different queues
start_worker "default,codemirror" 4 "codemirror"
start_worker "analysis" 2 "analysis"
start_worker "insights" 2 "insights"
start_worker "packages" 2 "packages"

# Start Celery Beat for periodic tasks
echo "Starting Celery Beat scheduler..."
celery -A app.workers.celery_app beat \
    --loglevel=info \
    --pidfile="/tmp/celerybeat.pid" &

# Start Flower for monitoring (optional)
if command -v flower &> /dev/null; then
    echo "Starting Flower monitoring on port 5555..."
    celery -A app.workers.celery_app flower \
        --port=5555 \
        --url_prefix=flower &
fi

echo "Celery workers started!"
echo "Monitor at: http://localhost:5555/flower (if Flower is installed)"

# Wait for all background processes
wait