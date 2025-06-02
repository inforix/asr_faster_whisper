# Docker Deployment Guide

## Overview

This guide covers deploying the ASR (Automatic Speech Recognition) project using Docker Compose. The configuration supports multiple deployment scenarios from simple development to full production with monitoring.

## Quick Start

### Basic Deployment (Port 8087)

```bash
# Start the ASR service
docker-compose up -d asr-app

# Check service status
docker-compose ps

# View logs
docker-compose logs -f asr-app

# Stop the service
docker-compose down
```

The service will be available at: `http://localhost:8087`

## Deployment Profiles

### 1. Development (Default)
```bash
docker-compose up -d asr-app
```
- ASR service on port 8087
- Basic health checks
- Volume mounts for development

### 2. Production with Reverse Proxy
```bash
docker-compose --profile production up -d
```
- ASR service behind Nginx reverse proxy
- Nginx on ports 80/443
- Rate limiting and security headers
- SSL support (requires certificate setup)

### 3. Full Monitoring Stack
```bash
docker-compose --profile monitoring up -d
```
- ASR service + Prometheus + Grafana
- Prometheus on port 9090
- Grafana on port 3000 (admin/admin)
- Metrics collection and visualization

### 4. Complete Production Setup
```bash
docker-compose --profile production --profile monitoring up -d
```
- All services: ASR + Nginx + Prometheus + Grafana
- Full production-ready deployment

## Service Configuration

### ASR Application
- **Container**: `asr-service`
- **Port**: 8087
- **Health Check**: `/health` endpoint
- **Environment**: Production optimized
- **Resources**: 2-4GB RAM, 1-2 CPU cores

### Nginx Reverse Proxy (Optional)
- **Container**: `asr-nginx`
- **Ports**: 80, 443
- **Features**: Rate limiting, security headers, SSL support
- **Configuration**: `nginx/nginx.conf`

### Prometheus Monitoring (Optional)
- **Container**: `asr-prometheus`
- **Port**: 9090
- **Configuration**: `monitoring/prometheus.yml`
- **Data Persistence**: Named volume

### Grafana Visualization (Optional)
- **Container**: `asr-grafana`
- **Port**: 3000
- **Default Login**: admin/admin
- **Data Persistence**: Named volume

## Volume Mounts

### Application Volumes
```yaml
volumes:
  - ./models:/app/models          # Model persistence
  - ./logs:/app/logs              # Log files
  - ./config.env:/app/config.env  # Configuration
```

### Monitoring Volumes
```yaml
volumes:
  - prometheus_data:/prometheus   # Prometheus data
  - grafana_data:/var/lib/grafana # Grafana data
```

## Environment Variables

### Core Settings
```bash
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8087
LOG_LEVEL=INFO
KMP_DUPLICATE_LIB_OK=TRUE
```

### Model Configuration
```bash
WHISPER_MODEL=large-v3
WHISPER_DEVICE=cpu
TTS_MODEL_PATH=/app/models/tts
```

### Performance Tuning
```bash
MAX_WORKERS=1
ENABLE_METRICS=true
```

## API Endpoints

Once deployed, the following endpoints are available:

- **Health Check**: `GET http://localhost:8087/health`
- **API Documentation**: `GET http://localhost:8087/docs`
- **Speech Recognition**: `POST http://localhost:8087/api/voice/transcribe`
- **Text-to-Speech**: `POST http://localhost:8087/api/tts/synthesize`
- **Metrics**: `GET http://localhost:8087/metrics`

## Resource Requirements

### Minimum Requirements
- **RAM**: 2GB
- **CPU**: 1 core
- **Disk**: 5GB (for models and logs)

### Recommended for Production
- **RAM**: 4GB
- **CPU**: 2 cores
- **Disk**: 10GB SSD

## Monitoring and Logging

### Application Logs
```bash
# View real-time logs
docker-compose logs -f asr-app

# View specific number of lines
docker-compose logs --tail=100 asr-app
```

### Health Monitoring
```bash
# Check health status
curl http://localhost:8087/health

# Check container health
docker-compose ps
```

### Metrics (if monitoring enabled)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **Application Metrics**: http://localhost:8087/metrics

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check if port 8087 is in use
   lsof -i :8087
   
   # Change port in docker-compose.yml if needed
   ports:
     - "8088:8087"  # Use 8088 instead
   ```

2. **Model Download Issues**
   ```bash
   # Check model directory permissions
   ls -la ./models/
   
   # Recreate models volume
   docker-compose down -v
   docker-compose up -d asr-app
   ```

3. **Memory Issues**
   ```bash
   # Check container memory usage
   docker stats asr-service
   
   # Increase memory limits in docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 6G
   ```

4. **OpenMP Library Conflicts**
   - Already handled by `KMP_DUPLICATE_LIB_OK=TRUE`
   - Check logs for any remaining issues

### Debugging Commands

```bash
# Enter container shell
docker-compose exec asr-app bash

# Check container logs
docker-compose logs asr-app

# Restart specific service
docker-compose restart asr-app

# Rebuild and restart
docker-compose up -d --build asr-app

# Check service health
docker-compose exec asr-app curl http://localhost:8087/health
```

## SSL Configuration (Production)

For HTTPS support with Nginx:

1. **Place SSL certificates in `nginx/ssl/`**:
   ```
   nginx/ssl/
   ├── cert.pem
   └── key.pem
   ```

2. **Update nginx.conf** to include SSL configuration:
   ```nginx
   server {
       listen 443 ssl;
       ssl_certificate /etc/nginx/ssl/cert.pem;
       ssl_certificate_key /etc/nginx/ssl/key.pem;
       # ... rest of configuration
   }
   ```

## Scaling and Performance

### Horizontal Scaling
```yaml
# In docker-compose.yml
asr-app:
  deploy:
    replicas: 3
```

### Load Balancing
- Use Nginx upstream configuration
- Add multiple ASR service instances
- Configure health checks

### Performance Optimization
- Adjust worker processes
- Tune memory limits
- Use GPU if available (update Dockerfile)

## Backup and Recovery

### Data Backup
```bash
# Backup volumes
docker run --rm -v asr_prometheus_data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus-backup.tar.gz -C /data .
docker run --rm -v asr_grafana_data:/data -v $(pwd):/backup alpine tar czf /backup/grafana-backup.tar.gz -C /data .
```

### Configuration Backup
```bash
# Backup configuration files
tar czf asr-config-backup.tar.gz docker-compose.yml nginx/ monitoring/ config.env
``` 