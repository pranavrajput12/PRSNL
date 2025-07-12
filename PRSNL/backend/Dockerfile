FROM python:3.11-slim-bullseye

# Set environment variables
# Prevent Python from creating .pyc files (zero-cache reloads)
ENV PYTHONDONTWRITEBYTECODE=1
# Force Python to output everything immediately (no buffering)
ENV PYTHONUNBUFFERED=1
# Poetry version
ENV POETRY_VERSION=1.7.1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    build-essential \
    gcc \
    g++ \
    tesseract-ocr \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==$POETRY_VERSION

WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies as root
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app/app

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Command to run the application with uvloop optimization
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --loop uvloop"]