# PRSNL Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Local Deployment](#local-deployment)
4. [Production Deployment](#production-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Configuration](#configuration)
7. [Security](#security)
8. [Monitoring](#monitoring)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

## Overview

PRSNL can be deployed in various environments:
- **Local Development**: Docker Compose for quick setup
- **Self-Hosted**: On-premise servers or VPS
- **Cloud Platforms**: AWS, GCP, Azure, DigitalOcean
- **Container Platforms**: Kubernetes, Docker Swarm

## Prerequisites

### System Requirements
- **CPU**: 2+ cores (4+ recommended)
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 50GB+ (depends on media storage needs)
- **OS**: Linux (Ubuntu 20.04+ recommended), macOS, Windows with WSL2

### Software Requirements
- Docker 20.10+
- Docker Compose 2.0+
- Git
- SSL certificate (for production)
- Domain name (for production)

## Local Deployment

### Quick Start with Docker Compose

```bash
# Clone repository
git clone <repository-url>
cd PRSNL

# Create environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit environment files with your configuration
# Important: Change all default passwords and secrets!

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Access services
# Frontend: http://localhost:3002
# Backend API: http://localhost:8000
# Ollama: http://localhost:11434
```

### Development Mode

```bash
# Start with hot-reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# Run database migrations
docker-compose exec backend alembic upgrade head
```

## Production Deployment

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | bash

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create deployment user
sudo useradd -m -s /bin/bash prsnl
sudo usermod -aG docker prsnl
sudo su - prsnl
```

### 2. SSL/TLS Setup with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### 3. Nginx Configuration

```nginx
# /etc/nginx/sites-available/prsnl
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Frontend
    location / {
        proxy_pass http://localhost:3002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Media files
    location /media {
        alias /var/lib/prsnl/media;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 4. Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    image: prsnl-backend:latest
    restart: always
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://prsnl:${DB_PASSWORD}@db:5432/prsnl
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./media:/app/media
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: prsnl-frontend:latest
    restart: always
    environment:
      - PUBLIC_API_URL=https://your-domain.com/api
      - PUBLIC_WS_URL=wss://your-domain.com/ws
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15-alpine
    restart: always
    environment:
      - POSTGRES_USER=prsnl
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=prsnl
    volumes:
      - postgres_data:/var/lib/postgresql/data
    command: 
      - "postgres"
      - "-c"
      - "max_connections=200"
      - "-c"
      - "shared_buffers=256MB"

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 5. Deployment Script

```bash
#!/bin/bash
# deploy.sh

set -e

echo "Starting deployment..."

# Pull latest code
git pull origin main

# Build images
docker-compose -f docker-compose.prod.yml build

# Run database migrations
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Clean up
docker system prune -f

echo "Deployment complete!"
```

## Cloud Deployment

### AWS EC2 Deployment

```bash
# 1. Launch EC2 instance (Ubuntu 20.04)
# 2. Configure security groups:
#    - SSH (22)
#    - HTTP (80)
#    - HTTPS (443)

# 3. Connect to instance
ssh -i your-key.pem ubuntu@your-instance-ip

# 4. Follow production deployment steps above

# 5. Configure AWS services:
# - RDS for PostgreSQL (optional)
# - S3 for media storage (optional)
# - CloudFront for CDN (optional)
```

### Google Cloud Platform

```bash
# Using Google Compute Engine
gcloud compute instances create prsnl-server \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --machine-type=e2-standard-2 \
    --zone=us-central1-a

# Using Google Kubernetes Engine
gcloud container clusters create prsnl-cluster \
    --num-nodes=3 \
    --machine-type=e2-standard-2
```

### Docker Swarm Deployment

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml prsnl

# Scale services
docker service scale prsnl_backend=3

# Update service
docker service update --image prsnl-backend:v2 prsnl_backend
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prsnl-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: prsnl-backend
  template:
    metadata:
      labels:
        app: prsnl-backend
    spec:
      containers:
      - name: backend
        image: prsnl-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: prsnl-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

## Configuration

### Environment Variables

#### Backend Configuration
```bash
# .env.production
# Database
DATABASE_URL=postgresql://prsnl:secure-password@db:5432/prsnl
REDIS_URL=redis://redis:6379

# Security
SECRET_KEY=your-very-secure-secret-key
CORS_ORIGINS=["https://your-domain.com"]

# AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...
OLLAMA_BASE_URL=http://ollama:11434

# Storage
MEDIA_ROOT=/app/media
MAX_VIDEO_SIZE_MB=500

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
```

#### Frontend Configuration
```bash
# .env.production
PUBLIC_API_URL=https://your-domain.com/api
PUBLIC_WS_URL=wss://your-domain.com/ws
PUBLIC_ANALYTICS_ID=G-XXXXXXXXXX
```

### Performance Tuning

#### PostgreSQL Optimization
```sql
-- postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
huge_pages = off
min_wal_size = 1GB
max_wal_size = 4GB
```

#### Redis Configuration
```conf
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
```

## Security

### Security Checklist

- [ ] Change all default passwords
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Disable unnecessary services
- [ ] Regular security updates
- [ ] Enable fail2ban
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Enable database SSL
- [ ] Regular backups
- [ ] Monitor access logs

### Firewall Configuration

```bash
# UFW setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### Fail2ban Configuration

```ini
# /etc/fail2ban/jail.local
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
```

## Monitoring

### Health Monitoring

```bash
# Simple health check script
#!/bin/bash
# health-check.sh

BACKEND_HEALTH=$(curl -s http://localhost:8000/health | jq -r .overall_status)
if [ "$BACKEND_HEALTH" != "UP" ]; then
    echo "Backend is down!"
    # Send alert
fi
```

### Prometheus + Grafana Setup

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus_data:
  grafana_data:
```

### Logging

```bash
# Centralized logging with ELK stack
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  elasticsearch:8.11.0

docker run -d \
  --name kibana \
  -p 5601:5601 \
  --link elasticsearch \
  kibana:8.11.0
```

## Backup & Recovery

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/prsnl"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T db pg_dump -U prsnl prsnl | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/lib/prsnl/media

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz .env docker-compose.yml

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

# Upload to S3 (optional)
aws s3 sync $BACKUP_DIR s3://your-backup-bucket/prsnl/
```

### Restore Procedure

```bash
# Restore database
gunzip < backup/db_20240106_120000.sql.gz | docker-compose exec -T db psql -U prsnl

# Restore media files
tar -xzf backup/media_20240106_120000.tar.gz -C /

# Restore configuration
tar -xzf backup/config_20240106_120000.tar.gz
```

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker-compose logs backend

# Check container status
docker ps -a

# Inspect container
docker inspect prsnl_backend_1
```

#### Database Connection Issues
```bash
# Test connection
docker-compose exec backend python -c "
from app.db.database import get_db_pool
import asyncio
asyncio.run(get_db_pool())
"

# Check PostgreSQL logs
docker-compose logs db
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Check disk space
df -h

# Check memory
free -m

# Check CPU
top
```

#### SSL Certificate Issues
```bash
# Test certificate
openssl s_client -connect your-domain.com:443

# Renew certificate
sudo certbot renew --dry-run
sudo certbot renew
```

### Debug Mode

```yaml
# Enable debug logging
services:
  backend:
    environment:
      - LOG_LEVEL=DEBUG
      - DEBUG=true
```

## Maintenance

### Regular Tasks

#### Daily
- Monitor health endpoints
- Check error logs
- Verify backups

#### Weekly
- Review resource usage
- Check for security updates
- Clean up old logs

#### Monthly
- Update dependencies
- Performance analysis
- Security audit
- Database optimization

### Update Procedure

```bash
# 1. Backup current state
./backup.sh

# 2. Pull latest changes
git pull origin main

# 3. Build new images
docker-compose build

# 4. Run migrations
docker-compose run --rm backend alembic upgrade head

# 5. Deploy with zero downtime
docker-compose up -d --no-deps --scale backend=2 backend
# Wait for new container to be healthy
docker-compose up -d --no-deps backend

# 6. Verify deployment
curl https://your-domain.com/health
```

## Support

### Getting Help
- Check logs first
- Review this documentation
- Search GitHub issues
- Contact support team

### Useful Commands Reference
```bash
# View all logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f backend

# Execute command in container
docker-compose exec backend bash

# Database shell
docker-compose exec db psql -U prsnl

# Redis CLI
docker-compose exec redis redis-cli

# Clean up everything
docker-compose down -v
docker system prune -a
```