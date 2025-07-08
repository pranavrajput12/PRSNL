# PRSNL Railway Deployment Guide

## Prerequisites
- Railway account (https://railway.app)
- Railway CLI installed: `brew install railway`

## Step 1: Prepare Backend for Railway

### 1.1 Create Railway Configuration
Create `railway.toml` in backend directory:

```toml
[build]
builder = "dockerfile"
dockerfilePath = "./Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "always"
```

### 1.2 Update Backend Configuration
Update `backend/app/config.py` to use Railway environment variables:

```python
# Add these for Railway
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/prsnl")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Parse DATABASE_URL for asyncpg (Railway provides standard format)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
```

## Step 2: Deploy to Railway

### 2.1 Login and Initialize
```bash
cd PRSNL/backend
railway login
railway link  # Create new project when prompted
```

### 2.2 Add PostgreSQL Database
```bash
railway add
# Select "PostgreSQL"
# This automatically adds pgvector extension!
```

### 2.3 Add Redis
```bash
railway add
# Select "Redis"
```

### 2.4 Set Environment Variables
```bash
# Set your Azure OpenAI credentials
railway variables set AZURE_OPENAI_API_KEY=your-key-here
railway variables set AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com

# Set app configuration
railway variables set PROJECT_NAME=PRSNL
railway variables set API_V1_STR=/api
railway variables set BACKEND_CORS_ORIGINS='["*"]'  # Update for production
```

### 2.5 Deploy
```bash
railway up
# This builds and deploys your Docker container
```

### 2.6 Get Your URL
```bash
railway open
# Your backend will be at: https://your-app.railway.app
```

## Step 3: Migrate Your Data

### 3.1 Export Local Data
```bash
# On your local machine
cd PRSNL
docker-compose exec db pg_dump -U postgres prsnl > prsnl_backup.sql
```

### 3.2 Import to Railway
```bash
# Get Railway PostgreSQL URL
railway variables

# Import data
psql $DATABASE_URL < prsnl_backup.sql
```

## Step 4: Update iOS App

Update `APIConfiguration.swift`:
```swift
private let defaultBackendURL = "https://your-app.railway.app"
```

## Step 5: Test Everything

1. Test API: `curl https://your-app.railway.app/health`
2. Test WebSocket: Connect to `wss://your-app.railway.app/ws/chat/{client_id}`
3. Launch iOS app and verify connection

## Monitoring

- Railway Dashboard: https://railway.app/dashboard
- Logs: `railway logs`
- Metrics: Your app exposes Prometheus metrics at `/metrics`

## Costs Breakdown

- PostgreSQL (1GB): $5/month
- Redis (512MB): $5/month  
- App Container: ~$5/month (based on usage)
- **Total: ~$15/month**

## Notes

- Railway provides automatic SSL certificates
- Automatic deployments on git push (optional)
- Built-in metrics and logging
- Easy scaling when needed
- Persistent storage volumes available if needed