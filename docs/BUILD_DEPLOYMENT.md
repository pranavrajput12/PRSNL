# BUILD_DEPLOYMENT.md

## PRSNL Build and Deployment Guide

### Overview
PRSNL's multi-component architecture requires coordinated build and deployment processes for frontend (SvelteKit), backend (FastAPI), browser extension (Chrome), and desktop overlay (Electron). This guide covers development builds, production builds, containerization, and deployment strategies.

## Build System Architecture

### Component Build Dependencies
```mermaid
graph TD
    A[Source Code] --> B[Frontend Build]
    A --> C[Backend Build]
    A --> D[Extension Build]
    A --> E[Overlay Build]
    
    B --> F[Docker Image]
    C --> F
    
    D --> G[Extension Package]
    E --> H[Desktop App]
    
    F --> I[Container Registry]
    G --> J[Chrome Web Store]
    H --> K[App Distribution]
```

### Build Environment Requirements
- **Node.js**: v18.0.0+ (for frontend and overlay)
- **Python**: 3.8+ (for backend)
- **Docker**: 20.10+ (for containerization)
- **Docker Compose**: v2.0+ (for orchestration)
- **Chrome**: Latest (for extension testing)

## Frontend Build Process (SvelteKit)

### 1. Development Build
```bash
cd frontend

# Install dependencies
npm install

# Start development server with hot reload
npm run dev

# Alternative: Start with network access
npm run dev -- --host 0.0.0.0 --port 3000

# Type checking in watch mode
npm run check:watch
```

### 2. Production Build
```bash
cd frontend

# Clean previous builds
rm -rf build .svelte-kit

# Install production dependencies only
npm ci --production

# Build for production
npm run build

# Preview production build locally
npm run preview

# Verify build output
ls -la build/
```

### 3. Build Configuration (vite.config.ts)
```typescript
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  
  build: {
    target: 'es2020',
    minify: 'esbuild',
    sourcemap: true,
    
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['svelte', '@sveltejs/kit'],
          utils: ['./src/lib/utils/index.js']
        }
      }
    }
  },
  
  optimizeDeps: {
    include: ['uuid']
  },
  
  server: {
    port: 3000,
    host: '0.0.0.0'
  },
  
  preview: {
    port: 4173,
    host: '0.0.0.0'
  }
});
```

### 4. Environment-Specific Builds
```bash
# Development build
VITE_ENVIRONMENT=development npm run build

# Staging build
VITE_ENVIRONMENT=staging npm run build

# Production build
VITE_ENVIRONMENT=production npm run build
```

### 5. Frontend Build Output
```
build/
├── _app/                    # Application chunks
│   ├── version.json         # Build version info
│   ├── immutable/           # Versioned assets
│   │   ├── chunks/          # Code-split chunks
│   │   ├── assets/          # CSS and other assets
│   │   └── entry/           # Entry points
│   └── app.html             # HTML template
├── favicon.png              # Static assets
├── index.html               # Main page
└── robots.txt               # SEO files
```

## Backend Build Process (FastAPI)

### 1. Development Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative: Use development script
python -m app.main
```

### 2. Production Build (Local)
```bash
cd backend

# Install production dependencies
pip install -r requirements.txt

# Run database migrations
python app/db/init_db.py

# Start production server
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### 3. Backend Dockerfile
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /venv

# Set work directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

### 4. Multi-stage Production Dockerfile
```dockerfile
# Multi-stage Dockerfile for optimized production builds
FROM python:3.11-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Production stage
FROM python:3.11-slim as production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /venv /venv

# Create application directory
WORKDIR /app

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000"]
```

## Chrome Extension Build Process

### 1. Development Build
```bash
cd extension

# No build step required for development
# Extension uses vanilla JavaScript

# Load unpacked extension in Chrome:
# 1. Open chrome://extensions/
# 2. Enable "Developer mode"
# 3. Click "Load unpacked"
# 4. Select the extension directory
```

### 2. Production Package
```bash
cd extension

# Create production package
npm run build  # If build script exists

# Or manual packaging:
zip -r prsnl-extension-v1.0.0.zip \
  manifest.json \
  background.js \
  content.js \
  popup.html \
  popup.js \
  options.html \
  options.js \
  styles.css \
  options.css \
  content.css \
  icons/

# Verify package contents
unzip -l prsnl-extension-v1.0.0.zip
```

### 3. Extension Build Script
```bash
#!/bin/bash
# scripts/build-extension.sh

set -e

echo "Building Chrome Extension..."

cd extension

# Version from manifest.json
VERSION=$(node -p "require('./manifest.json').version")
BUILD_DIR="build"
PACKAGE_NAME="prsnl-extension-v${VERSION}.zip"

# Clean build directory
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

# Copy extension files
cp manifest.json $BUILD_DIR/
cp background.js $BUILD_DIR/
cp content.js $BUILD_DIR/
cp popup.html $BUILD_DIR/
cp popup.js $BUILD_DIR/
cp options.html $BUILD_DIR/
cp options.js $BUILD_DIR/
cp styles.css $BUILD_DIR/
cp options.css $BUILD_DIR/
cp content.css $BUILD_DIR/
cp -r icons/ $BUILD_DIR/

# Create package
cd $BUILD_DIR
zip -r ../$PACKAGE_NAME .
cd ..

echo "Extension packaged: $PACKAGE_NAME"
echo "Size: $(du -h $PACKAGE_NAME | cut -f1)"

# Validate package
echo "Validating package..."
unzip -t $PACKAGE_NAME

echo "Build complete!"
```

### 4. Extension Manifest (Production)
```json
{
  "manifest_version": 3,
  "name": "PRSNL - Personal Knowledge Capture",
  "version": "1.0.0",
  "description": "Capture web content to your local PRSNL knowledge base",
  
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  
  "background": {
    "service_worker": "background.js"
  },
  
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["content.js"],
    "css": ["content.css"],
    "run_at": "document_end"
  }],
  
  "options_page": "options.html",
  
  "permissions": [
    "activeTab",
    "scripting",
    "storage",
    "tabs",
    "notifications",
    "contextMenus"
  ],
  
  "host_permissions": [
    "http://localhost:8000/*",
    "https://your-domain.com/*"
  ],
  
  "commands": {
    "capture-page": {
      "suggested_key": {
        "default": "Ctrl+Shift+S",
        "mac": "Command+Shift+S"
      },
      "description": "Capture current page"
    },
    "capture-selection": {
      "suggested_key": {
        "default": "Ctrl+Shift+E",
        "mac": "Command+Shift+E"
      },
      "description": "Capture selected text"
    }
  },
  
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  }
}
```

## Desktop Overlay Build Process (Electron)

### 1. Development Build
```bash
cd overlay

# Install dependencies
npm install

# Start development mode
npm run dev

# Or start with debugging
npm run dev:debug
```

### 2. Production Build
```bash
cd overlay

# Build for current platform
npm run build

# Build for all platforms
npm run build:all

# Build for specific platforms
npm run build:mac
npm run build:win
npm run build:linux
```

### 3. Electron Build Configuration (package.json)
```json
{
  "name": "prsnl-overlay",
  "version": "1.0.0",
  "main": "main.js",
  
  "scripts": {
    "dev": "electron .",
    "dev:debug": "electron . --debug",
    "build": "electron-builder",
    "build:all": "electron-builder -mwl",
    "build:mac": "electron-builder --mac",
    "build:win": "electron-builder --win",
    "build:linux": "electron-builder --linux"
  },
  
  "build": {
    "appId": "com.prsnl.overlay",
    "productName": "PRSNL Quick Search",
    "directories": {
      "output": "dist"
    },
    "files": [
      "main.js",
      "renderer.js",
      "preload.js",
      "index.html",
      "styles.css",
      "package.json"
    ],
    "mac": {
      "category": "public.app-category.productivity",
      "icon": "icons/icon.icns",
      "target": [
        {
          "target": "dmg",
          "arch": ["x64", "arm64"]
        }
      ]
    },
    "win": {
      "icon": "icons/icon.ico",
      "target": [
        {
          "target": "nsis",
          "arch": ["x64", "ia32"]
        }
      ]
    },
    "linux": {
      "icon": "icons/icon.png",
      "target": [
        {
          "target": "AppImage",
          "arch": ["x64"]
        }
      ]
    }
  }
}
```

## Container Orchestration

### 1. Docker Compose (Development)
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: prsnl
      POSTGRES_USER: prsnl
      POSTGRES_PASSWORD: prsnl
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/db/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U prsnl"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://prsnl:prsnl@postgres:5432/prsnl
      REDIS_URL: redis://redis:6379
      ENVIRONMENT: development
      DEBUG: "true"
    volumes:
      - ./backend:/app
      - backend_data:/app/data
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      VITE_API_URL: http://localhost:8000
      VITE_ENVIRONMENT: development
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - frontend_dist:/var/www/html
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  backend_data:
  frontend_dist:
```

### 2. Docker Compose (Production)
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - prsnl-network

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - prsnl-network

  backend:
    image: prsnl/backend:latest
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_URL: redis://redis:6379
      ENVIRONMENT: production
      DEBUG: "false"
      SECRET_KEY: ${SECRET_KEY}
    volumes:
      - backend_data:/app/data
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - prsnl-network

  frontend:
    image: prsnl/frontend:latest
    environment:
      VITE_API_URL: ${API_URL}
      VITE_ENVIRONMENT: production
    restart: unless-stopped
    networks:
      - prsnl-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/prod.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - frontend_dist:/var/www/html
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
    networks:
      - prsnl-network

volumes:
  postgres_data:
  redis_data:
  backend_data:
  frontend_dist:

networks:
  prsnl-network:
    driver: bridge
```

## CI/CD Pipeline

### 1. GitHub Actions Workflow
```yaml
# .github/workflows/build-and-deploy.yml
name: Build and Deploy PRSNL

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: 'frontend/package-lock.json'
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        cache: 'pip'
        cache-dependency-path: 'backend/requirements.txt'
    
    - name: Install Frontend Dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Install Backend Dependencies
      run: |
        cd backend
        pip install -r requirements-dev.txt
    
    - name: Run Frontend Tests
      run: |
        cd frontend
        npm run test
        npm run lint
        npm run type-check
    
    - name: Run Backend Tests
      run: |
        cd backend
        pytest
        black --check .
        ruff check .

  build-frontend:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: 'frontend/package-lock.json'
    
    - name: Install Dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Build Frontend
      run: |
        cd frontend
        npm run build
    
    - name: Upload Frontend Artifacts
      uses: actions/upload-artifact@v3
      with:
        name: frontend-build
        path: frontend/build/

  build-backend:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/backend
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: ./backend
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  build-extension:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Build Extension Package
      run: |
        cd extension
        chmod +x ../scripts/build-extension.sh
        ../scripts/build-extension.sh
    
    - name: Upload Extension Artifacts
      uses: actions/upload-artifact@v3
      with:
        name: extension-package
        path: extension/*.zip

  build-desktop:
    needs: test
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    
    runs-on: ${{ matrix.os }}
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: 'overlay/package-lock.json'
    
    - name: Install Dependencies
      run: |
        cd overlay
        npm ci
    
    - name: Build Desktop App
      run: |
        cd overlay
        npm run build
    
    - name: Upload Desktop Artifacts
      uses: actions/upload-artifact@v3
      with:
        name: desktop-${{ matrix.os }}
        path: overlay/dist/

  deploy:
    if: github.ref == 'refs/heads/main'
    needs: [build-frontend, build-backend, build-extension, build-desktop]
    runs-on: ubuntu-latest
    environment: production
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Download Frontend Artifacts
      uses: actions/download-artifact@v3
      with:
        name: frontend-build
        path: ./frontend/build/
    
    - name: Deploy to Production
      run: |
        # Add deployment script here
        echo "Deploying to production..."
        # ./scripts/deploy.sh production
```

## Deployment Strategies

### 1. Local Deployment
```bash
#!/bin/bash
# scripts/deploy-local.sh

set -e

echo "🚀 Deploying PRSNL locally..."

# Build all components
echo "📦 Building frontend..."
cd frontend && npm run build && cd ..

echo "🐍 Building backend..."
cd backend && python -m pip install -r requirements.txt && cd ..

echo "🔧 Building extension..."
cd extension && ../scripts/build-extension.sh && cd ..

echo "💻 Building desktop app..."
cd overlay && npm run build && cd ..

# Start services
echo "🐳 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services..."
sleep 30

# Health checks
echo "🔍 Running health checks..."
curl -f http://localhost:8000/health || exit 1
curl -f http://localhost:3000 || exit 1

echo "✅ Deployment complete!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
```

### 2. Cloud Deployment (AWS)
```bash
#!/bin/bash
# scripts/deploy-aws.sh

set -e

AWS_REGION=${AWS_REGION:-us-east-1}
ECR_REPOSITORY=${ECR_REPOSITORY:-prsnl}
CLUSTER_NAME=${CLUSTER_NAME:-prsnl-cluster}

echo "🚀 Deploying PRSNL to AWS..."

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push backend image
echo "📦 Building and pushing backend..."
cd backend
docker build -t $ECR_REPOSITORY/backend:latest .
docker tag $ECR_REPOSITORY/backend:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY/backend:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY/backend:latest
cd ..

# Build and push frontend image
echo "📦 Building and pushing frontend..."
cd frontend
docker build -t $ECR_REPOSITORY/frontend:latest .
docker tag $ECR_REPOSITORY/frontend:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY/frontend:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY/frontend:latest
cd ..

# Deploy to ECS
echo "🚀 Deploying to ECS..."
ecs-cli compose \
  --project-name prsnl \
  --file docker-compose.aws.yml \
  service up \
  --cluster $CLUSTER_NAME \
  --launch-type FARGATE

echo "✅ AWS deployment complete!"
```

### 3. Self-Hosted Deployment
```bash
#!/bin/bash
# scripts/deploy-self-hosted.sh

set -e

SERVER_HOST=${SERVER_HOST:-your-server.com}
SERVER_USER=${SERVER_USER:-prsnl}
DEPLOY_PATH=${DEPLOY_PATH:-/opt/prsnl}

echo "🚀 Deploying PRSNL to self-hosted server..."

# Build locally
echo "📦 Building all components..."
./scripts/build-all.sh

# Create deployment package
echo "📦 Creating deployment package..."
tar -czf prsnl-deployment.tar.gz \
  docker-compose.prod.yml \
  nginx/ \
  scripts/ \
  .env.example

# Upload to server
echo "📤 Uploading to server..."
scp prsnl-deployment.tar.gz $SERVER_USER@$SERVER_HOST:~/

# Deploy on server
echo "🚀 Deploying on server..."
ssh $SERVER_USER@$SERVER_HOST << 'EOF'
  cd ~
  tar -xzf prsnl-deployment.tar.gz
  sudo mv prsnl-deployment/* /opt/prsnl/
  cd /opt/prsnl
  
  # Pull latest images
  docker-compose -f docker-compose.prod.yml pull
  
  # Start services
  docker-compose -f docker-compose.prod.yml up -d
  
  # Clean up
  docker system prune -f
EOF

echo "✅ Self-hosted deployment complete!"
```

## Production Configuration

### 1. Environment Variables (.env.production)
```bash
# Database
DB_NAME=prsnl_prod
DB_USER=prsnl_user
DB_PASSWORD=secure_password_here
DATABASE_URL=postgresql://prsnl_user:secure_password_here@postgres:5432/prsnl_prod

# Redis
REDIS_URL=redis://redis:6379

# Application
SECRET_KEY=your_secret_key_here
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# API Configuration
API_URL=https://api.your-domain.com
ALLOWED_ORIGINS=https://your-domain.com,https://app.your-domain.com

# SSL/TLS
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/private.key

# Monitoring
SENTRY_DSN=your_sentry_dsn_here
MONITORING_ENABLED=true

# Backup
BACKUP_ENABLED=true
BACKUP_S3_BUCKET=prsnl-backups
BACKUP_RETENTION_DAYS=30
```

### 2. Nginx Configuration (Production)
```nginx
# nginx/prod.conf
user nginx;
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;
    
    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 20M;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Frontend
    server {
        listen 80;
        listen 443 ssl http2;
        server_name your-domain.com;
        
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/private.key;
        
        # Redirect HTTP to HTTPS
        if ($scheme != "https") {
            return 301 https://$server_name$request_uri;
        }
        
        root /var/www/html;
        index index.html;
        
        # Frontend routing
        location / {
            try_files $uri $uri/ /index.html;
        }
        
        # Static assets caching
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API Backend
    server {
        listen 443 ssl http2;
        server_name api.your-domain.com;
        
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/private.key;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
        
        location / {
            proxy_pass http://backend:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
        
        # Health check
        location /health {
            proxy_pass http://backend:8000/health;
            access_log off;
        }
    }
}
```

## Monitoring and Health Checks

### 1. Health Check Endpoints
```python
# app/api/health.py
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
import redis
import httpx

router = APIRouter()

@router.get("/health")
async def health_check():
    """Comprehensive health check"""
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database check
    try:
        async with database.transaction():
            await database.execute(text("SELECT 1"))
        checks["checks"]["database"] = "healthy"
    except Exception as e:
        checks["checks"]["database"] = f"unhealthy: {str(e)}"
        checks["status"] = "unhealthy"
    
    # Redis check
    try:
        r = redis.Redis.from_url(settings.redis_url)
        r.ping()
        checks["checks"]["redis"] = "healthy"
    except Exception as e:
        checks["checks"]["redis"] = f"unhealthy: {str(e)}"
        checks["status"] = "unhealthy"
    
    # Ollama check
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            response.raise_for_status()
        checks["checks"]["ollama"] = "healthy"
    except Exception as e:
        checks["checks"]["ollama"] = f"unhealthy: {str(e)}"
        # Ollama is optional, don't mark as unhealthy
    
    if checks["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=checks)
    
    return checks
```

### 2. Monitoring Scripts
```bash
#!/bin/bash
# scripts/monitor.sh

set -e

ENDPOINTS=(
    "http://localhost:3000"
    "http://localhost:8000/health"
    "http://localhost:8000/docs"
)

DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL:-""}

check_endpoint() {
    local url=$1
    local response
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    
    if [ "$response" = "200" ]; then
        echo "✅ $url - OK"
        return 0
    else
        echo "❌ $url - FAILED (HTTP $response)"
        return 1
    fi
}

send_alert() {
    local message=$1
    
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        curl -H "Content-Type: application/json" \
             -X POST \
             -d "{\"content\": \"🚨 PRSNL Alert: $message\"}" \
             "$DISCORD_WEBHOOK_URL"
    fi
    
    echo "ALERT: $message"
}

main() {
    local failed_endpoints=()
    
    echo "🔍 Checking PRSNL health..."
    
    for endpoint in "${ENDPOINTS[@]}"; do
        if ! check_endpoint "$endpoint"; then
            failed_endpoints+=("$endpoint")
        fi
    done
    
    if [ ${#failed_endpoints[@]} -gt 0 ]; then
        local message="Failed endpoints: ${failed_endpoints[*]}"
        send_alert "$message"
        exit 1
    fi
    
    echo "✅ All endpoints healthy"
}

main "$@"
```

This comprehensive build and deployment guide covers all aspects of building, packaging, and deploying PRSNL's multi-component architecture across different environments and platforms.