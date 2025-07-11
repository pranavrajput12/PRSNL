# PRSNL Monitoring & Observability Deployment Guide

This guide covers deploying the complete observability stack for PRSNL with Grafana, Loki, Prometheus, and OpenTelemetry.

## **📋 Prerequisites**

- Rancher Desktop (NOT Docker Desktop)
- PRSNL backend running on port 8000
- 8GB+ RAM for monitoring stack
- Available ports: 3000 (Grafana), 3100 (Loki), 9090 (Prometheus)

## **🚀 Quick Start - Monitoring Stack**

### **1. Start Monitoring Services**

```bash
# From PRSNL root directory
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL

# Start monitoring stack with Rancher Desktop
docker-compose -f docker-compose.monitoring.yml up -d

# Verify services are running
docker ps | grep prsnl-
```

### **2. Access Monitoring Dashboards**

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin/admin |
| **Prometheus** | http://localhost:9090 | - |
| **Loki** | http://localhost:3100 | - |

### **3. Verify PRSNL Integration**

```bash
# Check if PRSNL is exposing metrics
curl http://localhost:8000/metrics

# Should see OpenTelemetry + Prometheus metrics
```

## **🔧 Configuration Details**

### **OpenTelemetry Auto-Instrumentation**

Your PRSNL backend now automatically instruments:

```python
# This is already added to your main.py
from app.core.observability import instrument_fastapi_app
instrument_fastapi_app(app)  # Two-line drop-in setup!
```

**What's Instrumented:**
- ✅ All FastAPI endpoints (request/response times, status codes)
- ✅ Database queries (AsyncPG connections, query performance)
- ✅ HTTP client requests (aiohttp, httpx calls)
- ✅ Custom business metrics (content processing, search queries)

### **Environment Variables**

Add to your `.env` file:

```env
# Observability Configuration
OTLP_TRACES_ENDPOINT=http://localhost:4317
OTLP_METRICS_ENDPOINT=http://localhost:4317
PROMETHEUS_PORT=8001
ENVIRONMENT=development

# Enable detailed metrics
ENABLE_METRICS=true
```

## **📊 Available Dashboards**

### **1. Application Performance Monitoring (APM)**

**Metrics Available:**
- Request latency by endpoint
- Error rates and status code distributions
- Database query performance
- AI processing times (transcription, summarization)
- Content processing throughput

### **2. Infrastructure Monitoring**

**System Metrics:**
- CPU and memory usage
- Disk I/O and network traffic
- Container resource utilization
- Database connection pools

### **3. Business Metrics**

**PRSNL-Specific:**
- Content items processed per hour
- Search query performance
- Knowledge graph relationship creation
- User engagement patterns

## **🔍 Key Monitoring Queries**

### **Prometheus Queries**

```promql
# API Response Time (95th percentile)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error Rate by Endpoint
rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m])

# Database Query Performance
rate(prsnl_database_query_duration_seconds_sum[5m]) / rate(prsnl_database_query_duration_seconds_count[5m])

# Content Processing Rate
rate(prsnl_content_processed_total[5m])
```

### **LogQL Queries (Loki)**

```logql
# Error Logs from PRSNL
{job="prsnl-backend"} |= "ERROR"

# API Endpoint Performance
{job="prsnl-backend"} | json | duration > 1s

# AI Processing Logs
{job="prsnl-backend"} |= "openai" or "transcription"
```

## **🎯 Alerting Rules**

### **Critical Alerts**

```yaml
# prometheus/prsnl_rules.yml
groups:
  - name: prsnl_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          
      - alert: SlowDatabaseQueries
        expr: histogram_quantile(0.95, rate(prsnl_database_query_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database queries are slow"
```

## **📈 Performance Optimization**

### **Monitoring Resource Usage**

```bash
# Monitor container resources
docker stats prsnl-grafana prsnl-loki prsnl-prometheus

# Check disk usage for logs/metrics
docker exec prsnl-prometheus df -h /prometheus
docker exec prsnl-loki df -h /loki
```

### **Optimizing for Production**

1. **Resource Limits**:
   ```yaml
   # In docker-compose.monitoring.yml
   services:
     loki:
       deploy:
         resources:
           limits:
             memory: 1G
             cpus: '0.5'
   ```

2. **Data Retention**:
   ```yaml
   # Prometheus: 30 days retention
   command: ['--storage.tsdb.retention.time=30d']
   
   # Loki: 7 days retention
   table_manager:
     retention_deletes_enabled: true
     retention_period: 168h
   ```

## **🔧 Troubleshooting**

### **Common Issues**

**1. Metrics Not Appearing**
```bash
# Check if PRSNL is running and exposing metrics
curl http://localhost:8000/metrics
curl http://localhost:8000/health

# Verify Prometheus can scrape
docker logs prsnl-prometheus | grep "prsnl-backend"
```

**2. Loki Not Receiving Logs**
```bash
# Check Promtail logs
docker logs prsnl-promtail

# Verify log file paths
docker exec prsnl-promtail ls -la /app/logs/
```

**3. High Memory Usage**
```bash
# Restart services if memory usage too high
docker-compose -f docker-compose.monitoring.yml restart

# Check Grafana memory usage
docker exec prsnl-grafana free -h
```

### **Log Locations**

```bash
# Container logs
docker logs prsnl-grafana
docker logs prsnl-loki
docker logs prsnl-prometheus

# Application logs (mounted from PRSNL)
tail -f backend/logs/prsnl.log
tail -f backend/logs/error.log
```

## **🔒 Security Considerations**

### **Production Security**

1. **Change Default Passwords**:
   ```env
   GF_SECURITY_ADMIN_PASSWORD=your_secure_password
   ```

2. **Enable TLS**:
   ```yaml
   # For production deployment
   grafana:
     environment:
       - GF_SERVER_PROTOCOL=https
       - GF_SERVER_CERT_FILE=/etc/ssl/certs/grafana.crt
       - GF_SERVER_CERT_KEY=/etc/ssl/private/grafana.key
   ```

3. **Network Security**:
   ```yaml
   # Restrict external access
   networks:
     monitoring:
       driver: bridge
       internal: true  # No external internet access
   ```

## **📚 Next Steps**

### **Immediate Actions**

1. **Start monitoring stack**: `docker-compose -f docker-compose.monitoring.yml up -d`
2. **Access Grafana**: http://localhost:3000 (admin/admin)
3. **Verify metrics**: http://localhost:8000/metrics
4. **Check logs**: Navigate to Loki in Grafana

### **Advanced Configuration**

1. **Create custom dashboards** for PRSNL business metrics
2. **Set up alerting** for critical system failures
3. **Configure log retention** based on storage capacity
4. **Add custom metrics** for specific PRSNL features

### **Integration with Development Workflow**

1. **Use pre-commit hooks** to ensure code quality
2. **Monitor performance** during development
3. **Set up alerts** for regression detection
4. **Track feature usage** through custom metrics

---

**🎉 Your PRSNL knowledge management system now has enterprise-grade observability!**

Monitor performance, track user behavior, and maintain system health with comprehensive metrics, logs, and traces.