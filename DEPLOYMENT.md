# 🚀 PRSNL Production Deployment Guide

This guide covers deploying PRSNL to production using Docker, including SSL/TLS setup, monitoring, and best practices.

## 📋 Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Docker and Docker Compose installed
- Domain name pointed to your server
- At least 4GB RAM and 20GB storage
- Basic knowledge of Linux administration

## 🏗️ Production Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│     Nginx       │────▶│    Frontend     │────▶│    Backend      │
│  (SSL/Reverse   │     │   (SvelteKit)   │     │   (FastAPI)     │
│     Proxy)      │     │                 │     │                 │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
                                ┌─────────────────────────┴─────────┐
                                │                                   │
                         ┌──────▼────────┐              ┌──────────▼────────┐
                         │               │              │                   │
                         │  PostgreSQL   │              │     Ollama        │
                         │  (pgvector)   │              │   (Local LLM)     │
                         │               │              │                   │
                         └───────────────┘              └───────────────────┘
                                                                    
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   Prometheus    │────▶│    Grafana      │     │ Elasticsearch   │
│   (Metrics)     │     │  (Dashboards)   │     │    + Kibana     │
│                 │     │                 │     │    (Logs)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 🛠️ Step 1: Server Setup

### 1.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git nginx certbot python3-certbot-nginx
```

### 1.2 Install Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

### 1.3 Install Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 📦 Step 2: Deploy Application

### 2.1 Clone Repository
```bash
git clone <your-repository-url>
cd PRSNL
```

### 2.2 Configure Environment
```bash
# Copy production environment template
cp .env.production.example .env.production

# Edit with your settings
nano .env.production
```

Required environment variables:
```env
# Database
POSTGRES_USER=prsnl_prod
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=prsnl_production
DATABASE_URL=postgresql://prsnl_prod:<strong-password>@db:5432/prsnl_production

# Backend
SECRET_KEY=<generate-with-openssl-rand-hex-32>
ENVIRONMENT=production
CORS_ORIGINS=["https://your-domain.com"]

# Frontend
PUBLIC_API_URL=https://your-domain.com/api
PUBLIC_SITE_URL=https://your-domain.com

# Monitoring
GRAFANA_ADMIN_PASSWORD=<strong-password>

# Optional: Telegram Bot
TELEGRAM_BOT_TOKEN=<your-bot-token>
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/telegram/webhook
```

### 2.3 Build and Start Services
```bash
# Use production docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## 🔐 Step 3: SSL/TLS Setup

### 3.1 Configure Nginx
Create `/etc/nginx/sites-available/prsnl`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL will be configured by certbot
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for real-time features
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
    }
}
```

### 3.2 Enable Site and Get SSL Certificate
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/prsnl /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## 📊 Step 4: Monitoring Setup

### 4.1 Access Monitoring Services

- **Grafana**: https://your-domain.com:3001
  - Default user: admin
  - Password: Set in GRAFANA_ADMIN_PASSWORD

- **Prometheus**: http://localhost:9090 (internal only)

- **Kibana**: http://localhost:5601 (internal only)

### 4.2 Configure Grafana Dashboards

1. Log into Grafana
2. Add Prometheus data source:
   - URL: http://prometheus:9090
3. Import dashboards from `/monitoring/grafana-dashboards/`

### 4.3 Set Up Alerts

Create alert rules in Grafana for:
- High error rate (> 5% of requests)
- Slow response time (> 2s average)
- Low disk space (< 20% free)
- Database connection failures
- Video processing failures

## 🔧 Step 5: Performance Optimization

### 5.1 Database Optimization
```sql
-- Connect to database
docker exec -it prsnl_db psql -U prsnl_prod -d prsnl_production

-- Run VACUUM and ANALYZE
VACUUM ANALYZE;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan;
```

### 5.2 Configure Redis Cache (Optional)
Add to `docker-compose.prod.yml`:
```yaml
redis:
  image: redis:7-alpine
  volumes:
    - redis_data:/data
  networks:
    - prsnl_network
```

### 5.3 Enable CDN for Static Assets
Configure CloudFlare or similar CDN for:
- Frontend static files
- Video thumbnails
- User-uploaded images

## 🛡️ Step 6: Security Hardening

### 6.1 Firewall Configuration
```bash
# Install UFW
sudo apt install ufw

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 6.2 Fail2ban Setup
```bash
# Install fail2ban
sudo apt install fail2ban

# Create jail for PRSNL
sudo nano /etc/fail2ban/jail.local
```

Add:
```ini
[prsnl-api]
enabled = true
port = 80,443
filter = prsnl-api
logpath = /var/log/nginx/access.log
maxretry = 10
bantime = 3600
```

### 6.3 Regular Security Updates
```bash
# Create update script
cat > /home/ubuntu/update-prsnl.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/PRSNL
git pull
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
docker system prune -f
EOF

chmod +x /home/ubuntu/update-prsnl.sh

# Add to crontab for weekly updates
crontab -e
# Add: 0 3 * * 0 /home/ubuntu/update-prsnl.sh
```

## 📈 Step 7: Backup Strategy

### 7.1 Database Backups
```bash
# Create backup script
cat > /home/ubuntu/backup-prsnl.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
docker exec prsnl_db pg_dump -U prsnl_prod prsnl_production | gzip > $BACKUP_DIR/prsnl_db_$DATE.sql.gz

# Backup media files
tar -czf $BACKUP_DIR/prsnl_media_$DATE.tar.gz /var/lib/docker/volumes/prsnl_media_data

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
EOF

chmod +x /home/ubuntu/backup-prsnl.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /home/ubuntu/backup-prsnl.sh
```

### 7.2 Restore Procedure
```bash
# Restore database
gunzip < backup.sql.gz | docker exec -i prsnl_db psql -U prsnl_prod prsnl_production

# Restore media files
tar -xzf prsnl_media_backup.tar.gz -C /
```

## 🚨 Step 8: Monitoring & Maintenance

### 8.1 Health Checks
```bash
# Check application health
curl https://your-domain.com/health

# Check docker services
docker-compose -f docker-compose.prod.yml ps

# Check disk usage
df -h

# Check memory usage
free -h
```

### 8.2 Log Management
```bash
# View application logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Set up log rotation
cat > /etc/logrotate.d/docker-prsnl << EOF
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=10M
    missingok
    delaycompress
}
EOF
```

### 8.3 Performance Monitoring
- Set up uptime monitoring (UptimeRobot, Pingdom)
- Configure Grafana alerts
- Monitor error rates in Kibana
- Track video processing metrics

## 📝 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database logs
   docker-compose -f docker-compose.prod.yml logs db
   
   # Restart database
   docker-compose -f docker-compose.prod.yml restart db
   ```

2. **Video Processing Failures**
   ```bash
   # Check video processor logs
   docker-compose -f docker-compose.prod.yml logs backend | grep video_processor
   
   # Check disk space
   df -h /var/lib/docker/volumes/prsnl_media_data
   ```

3. **High Memory Usage**
   ```bash
   # Check container stats
   docker stats
   
   # Restart specific service
   docker-compose -f docker-compose.prod.yml restart backend
   ```

## 🎯 Production Checklist

- [ ] SSL/TLS certificate installed and auto-renewing
- [ ] Firewall configured and enabled
- [ ] Regular backups scheduled
- [ ] Monitoring dashboards configured
- [ ] Alerts set up for critical metrics
- [ ] Log rotation configured
- [ ] Security headers enabled
- [ ] Environment variables properly set
- [ ] Database indexes created
- [ ] Health checks passing

## 📞 Support

For production support:
1. Check logs: `docker-compose -f docker-compose.prod.yml logs`
2. Review monitoring dashboards
3. Check GitHub issues
4. Contact support team

---

**Last Updated**: 2025-07-06
**Version**: 1.0.0