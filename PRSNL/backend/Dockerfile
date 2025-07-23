FROM python:3.11-slim-bullseye AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .

# Install dependencies in chunks to avoid memory issues
# First install lighter dependencies
RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    uvloop==0.21.0 \
    python-dotenv==1.0.0 \
    pydantic-settings==2.1.0 \
    slowapi==0.1.9 \
    asyncpg==0.29.0 \
    sqlalchemy==2.0.25 \
    pgvector==0.2.0 \
    redis==5.0.1 \
    beautifulsoup4==4.12.3 \
    httpx==0.26.0 \
    aiohttp==3.9.3

# Then install ML dependencies separately
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir open-clip-torch transformers sentence-transformers

# Finally install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    tesseract-ocr \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY ./app /app/app

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Set production environment variables
ENV ENVIRONMENT=production
ENV LOG_LEVEL=INFO
ENV ENABLE_QUERY_LOGGING=false
ENV ENABLE_VERBOSE_LOGGING=false
ENV DEBUG_ROUTES=false

# Command to run the application with production settings and uvloop optimization
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info --no-access-log --loop uvloop"]