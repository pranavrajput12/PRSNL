FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and switch to it
RUN adduser --system --group appuser
USER appuser
WORKDIR /app

# Copy requirements and install Python packages
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser ./app /app/app

# Add user's local bin to PATH
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["/home/appuser/.local/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
