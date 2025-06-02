# Systemd Deployment Guide for Ubuntu 22.04 (Python Mode)

## Overview

This guide covers deploying the ASR (Automatic Speech Recognition) project as a systemd service on Ubuntu 22.04 using Python directly (without Docker). The systemd integration provides automatic startup, service management, and system integration.

## Features

- ✅ **Direct Python Execution**: Runs FastAPI with uvicorn directly
- ✅ **Automatic Startup**: Service starts automatically on boot
- ✅ **Service Management**: Standard systemd commands for control
- ✅ **User Isolation**: Dedicated user account for security
- ✅ **Resource Limits**: Memory and process limits
- ✅ **Logging Integration**: Systemd journal integration
- ✅ **Health Monitoring**: Automatic restart on failure
- ✅ **Management Scripts**: Easy-to-use command shortcuts
- ✅ **Virtual Environment**: Isolated Python dependencies

## Quick Installation

### Automated Installation (Recommended)

```bash
# Clone or copy the project to your server
git clone <your-repo-url> /tmp/asr
cd /tmp/asr

# Run the installation script
sudo ./scripts/install-systemd.sh
```

### Manual Installation

If you prefer to install manually, follow the [Manual Installation](#manual-installation) section below.

## Service Management

### Using Management Scripts (Recommended)

```bash
# Start the service
asr-start

# Stop the service
asr-stop

# Restart the service
asr-restart

# Check service status and health
asr-status

# View service logs
asr-logs

# Update Python dependencies
asr-update
```

### Using Systemd Commands

```bash
# Start the service
sudo systemctl start asr

# Stop the service
sudo systemctl stop asr

# Restart the service
sudo systemctl restart asr

# Check service status
sudo systemctl status asr

# Enable auto-start on boot
sudo systemctl enable asr

# Disable auto-start on boot
sudo systemctl disable asr

# View service logs
sudo journalctl -u asr -f
```

## Service Configuration

### Service File Location
- **Service File**: `/etc/systemd/system/asr.service`
- **Application Directory**: `/opt/asr`
- **User Account**: `asr`
- **Group**: `asr`
- **Python Environment**: `/opt/asr/.venv`

### Service Properties
- **Type**: `exec` (long-running process)
- **Restart Policy**: `always` with 10-second delay
- **Timeout**: 300 seconds start, 60 seconds stop
- **Dependencies**: Requires network.target

### Environment Variables
```bash
PYTHONPATH=/opt/asr
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
KMP_DUPLICATE_LIB_OK=TRUE
```

## Directory Structure

After installation, the following structure is created:

```
/opt/asr/
├── .venv/                  # Python virtual environment
├── app/                    # Application code
├── docs/                   # Documentation
├── models/                 # AI models (persistent)
├── logs/                   # Application logs
├── scripts/                # Management scripts
├── systemd/                # Systemd service files
├── config.env              # Environment configuration
├── requirements.txt        # Python dependencies
└── run_dev.sh              # Development script
```

## Manual Installation

### Prerequisites

1. **Ubuntu 22.04 LTS**
2. **Root access** (sudo privileges)
3. **Internet connection** for downloading dependencies

### Step 1: Install System Dependencies

```bash
# Update system
sudo apt-get update

# Install Python and system dependencies
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    curl \
    ffmpeg \
    git \
    pkg-config \
    libffi-dev \
    libssl-dev
```

### Step 2: Create User and Directories

```bash
# Create ASR user and group
sudo groupadd asr
sudo useradd -r -g asr -d /opt/asr -s /bin/bash -c "ASR Service User" asr

# Create directories
sudo mkdir -p /opt/asr/{models,logs}
sudo chown -R asr:asr /opt/asr
```

### Step 3: Copy Application Files

```bash
# Copy project files to /opt/asr
sudo cp -r /path/to/your/asr/project/* /opt/asr/
sudo chown -R asr:asr /opt/asr
sudo chmod -R 755 /opt/asr
```

### Step 4: Setup Python Environment

```bash
# Create virtual environment
sudo -u asr python3 -m venv /opt/asr/.venv

# Install dependencies
sudo -u asr /opt/asr/.venv/bin/pip install --upgrade pip
sudo -u asr /opt/asr/.venv/bin/pip install -r /opt/asr/requirements.txt
```

### Step 5: Download AI Models

```bash
# Pre-download Whisper model
sudo -u asr bash -c "
    cd /opt/asr
    export KMP_DUPLICATE_LIB_OK=TRUE
    .venv/bin/python -c \"
from faster_whisper import WhisperModel
model = WhisperModel('large-v3', device='cpu', download_root='/opt/asr/models')
print('Model downloaded successfully')
\"
"
```

### Step 6: Install Systemd Service

```bash
# Copy service file
sudo cp /opt/asr/systemd/asr.service /etc/systemd/system/

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable asr
```

### Step 7: Configure Firewall

```bash
# Allow ASR service port
sudo ufw allow 8087/tcp comment "ASR Service"
```

## Service Monitoring

### Health Checks

The service includes built-in health monitoring:

```bash
# Check service health
curl http://localhost:8087/health

# Expected response
{
  "status": "healthy",
  "timestamp": "...",
  "services": {
    "whisper": {...},
    "tts": {...}
  }
}
```

### Log Monitoring

```bash
# View real-time logs
sudo journalctl -u asr -f

# View recent logs
sudo journalctl -u asr --since "1 hour ago"

# View logs with specific priority
sudo journalctl -u asr -p err
```

### Resource Monitoring

```bash
# Check resource usage
sudo systemctl status asr

# Check process details
ps aux | grep uvicorn

# Check memory usage
sudo cat /proc/$(pgrep -f "uvicorn.*asr")/status | grep VmRSS
```

## Troubleshooting

### Common Issues

#### 1. Service Fails to Start

```bash
# Check service status
sudo systemctl status asr

# Check detailed logs
sudo journalctl -u asr --no-pager

# Common causes:
# - Python dependencies missing
# - Permission issues
# - Port conflicts
# - Virtual environment issues
```

#### 2. Python Import Errors

```bash
# Check Python path
sudo -u asr /opt/asr/.venv/bin/python -c "import sys; print(sys.path)"

# Reinstall dependencies
sudo -u asr /opt/asr/.venv/bin/pip install --upgrade -r /opt/asr/requirements.txt

# Check specific imports
sudo -u asr /opt/asr/.venv/bin/python -c "from faster_whisper import WhisperModel"
```

#### 3. Port Conflicts

```bash
# Check if port 8087 is in use
sudo lsof -i :8087

# Change port in config.env if needed
sudo nano /opt/asr/config.env
```

#### 4. Model Download Issues

```bash
# Check internet connectivity
ping google.com

# Check disk space
df -h /opt/asr/

# Manually download models
sudo -u asr bash -c "
    cd /opt/asr
    export KMP_DUPLICATE_LIB_OK=TRUE
    .venv/bin/python -c \"
from faster_whisper import WhisperModel
model = WhisperModel('large-v3', device='cpu', download_root='/opt/asr/models')
\"
"
```

#### 5. OpenMP Library Conflicts

```bash
# Check if environment variable is set
sudo systemctl show asr -p Environment

# Manually set if needed
export KMP_DUPLICATE_LIB_OK=TRUE
```

### Debugging Commands

```bash
# Test application manually
sudo -u asr bash -c "
    cd /opt/asr
    export KMP_DUPLICATE_LIB_OK=TRUE
    .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8087
"

# Check virtual environment
sudo -u asr /opt/asr/.venv/bin/pip list

# Check systemd service configuration
sudo systemctl cat asr

# Check file permissions
ls -la /opt/asr/
```

## Performance Tuning

### Resource Limits

Edit `/etc/systemd/system/asr.service` to adjust limits:

```ini
[Service]
# Memory limit
MemoryMax=6G

# CPU limit (200% = 2 cores)
CPUQuota=200%

# File descriptor limit
LimitNOFILE=65536

# Process limit
LimitNPROC=4096
```

### Python Optimization

Edit `/opt/asr/config.env`:

```bash
# Increase workers for better performance
MAX_WORKERS=2

# Adjust model settings
WHISPER_MODEL=medium  # Use smaller model for speed
WHISPER_DEVICE=cpu    # Or 'cuda' if GPU available

# Performance tuning
PYTHONOPTIMIZE=1
```

### Uvicorn Configuration

Modify the ExecStart command in the service file:

```ini
ExecStart=/opt/asr/.venv/bin/python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8087 \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-log \
    --log-level info
```

## Security Considerations

### User Isolation
- Service runs as dedicated `asr` user
- No sudo privileges
- Limited shell access for debugging

### File Permissions
- Application files owned by `asr:asr`
- Virtual environment isolated
- Log files writable by service user only

### System Security
- `NoNewPrivileges=yes` prevents privilege escalation
- `PrivateTmp=yes` provides isolated /tmp
- `ProtectSystem=strict` makes system read-only
- `ProtectHome=yes` hides user home directories

### Network Security
- Service binds to all interfaces (0.0.0.0) but can be restricted
- Firewall rules limit external access
- Consider using reverse proxy for external access

## Backup and Recovery

### Configuration Backup

```bash
# Backup systemd configuration
sudo cp /etc/systemd/system/asr.service /backup/

# Backup application configuration
sudo tar czf /backup/asr-config.tar.gz -C /opt/asr config.env requirements.txt
```

### Data Backup

```bash
# Backup models and logs
sudo tar czf /backup/asr-data.tar.gz -C /opt/asr models/ logs/

# Backup virtual environment (optional)
sudo tar czf /backup/asr-venv.tar.gz -C /opt/asr .venv/
```

### Recovery Process

```bash
# Stop service
sudo systemctl stop asr

# Restore configuration
sudo tar xzf /backup/asr-config.tar.gz -C /opt/asr

# Restore data
sudo tar xzf /backup/asr-data.tar.gz -C /opt/asr

# Recreate virtual environment if needed
sudo -u asr python3 -m venv /opt/asr/.venv
sudo -u asr /opt/asr/.venv/bin/pip install -r /opt/asr/requirements.txt

# Fix permissions
sudo chown -R asr:asr /opt/asr

# Start service
sudo systemctl start asr
```

## Updates and Maintenance

### Updating Dependencies

```bash
# Use the update script
asr-update

# Or manually
sudo systemctl stop asr
sudo -u asr /opt/asr/.venv/bin/pip install --upgrade -r /opt/asr/requirements.txt
sudo systemctl start asr
```

### Updating Application Code

```bash
# Stop service
sudo systemctl stop asr

# Update code
sudo cp -r /path/to/new/code/* /opt/asr/
sudo chown -R asr:asr /opt/asr

# Update dependencies if needed
sudo -u asr /opt/asr/.venv/bin/pip install -r /opt/asr/requirements.txt

# Start service
sudo systemctl start asr
```

### Log Rotation

```bash
# Configure systemd journal rotation
sudo journalctl --vacuum-time=30d
sudo journalctl --vacuum-size=100M

# Or set up logrotate for application logs
sudo nano /etc/logrotate.d/asr
```

## Uninstallation

### Automated Uninstallation

```bash
# Run the uninstall script
sudo /opt/asr/scripts/uninstall-systemd.sh
```

### Manual Uninstallation

```bash
# Stop and disable service
sudo systemctl stop asr
sudo systemctl disable asr

# Remove service file
sudo rm /etc/systemd/system/asr.service
sudo systemctl daemon-reload

# Remove application directory
sudo rm -rf /opt/asr

# Remove user and group
sudo userdel asr
sudo groupdel asr

# Remove management scripts
sudo rm -f /usr/local/bin/asr-*

# Remove firewall rules
sudo ufw delete allow 8087/tcp
```

## Advanced Configuration

### Custom Python Version

If you need a specific Python version:

```bash
# Install Python 3.11 (example)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-dev

# Create virtual environment with specific version
sudo -u asr python3.11 -m venv /opt/asr/.venv
```

### GPU Support

For GPU acceleration:

```bash
# Install CUDA dependencies
sudo apt-get install nvidia-cuda-toolkit

# Update requirements.txt to include GPU versions
# torch>=2.0.0+cu118
# torchaudio>=2.0.0+cu118

# Update config.env
WHISPER_DEVICE=cuda
```

### Multiple Instances

To run multiple ASR instances:

1. Copy service file with different name
2. Modify working directory and ports
3. Create separate application directories
4. Enable and start additional services

## Support and Maintenance

### Regular Maintenance Tasks

```bash
# Update Python dependencies
asr-update

# Clean up Python cache
sudo find /opt/asr -name "__pycache__" -type d -exec rm -rf {} +

# Rotate logs
sudo journalctl --vacuum-time=30d

# Check disk usage
du -sh /opt/asr/
```

### Monitoring Setup

Consider setting up monitoring with:
- **System monitoring**: htop, iotop, netstat
- **Application monitoring**: Custom health checks
- **Log monitoring**: journalctl, rsyslog
- **Performance monitoring**: Python profiling tools

### Getting Help

1. Check service logs: `sudo journalctl -u asr`
2. Test manually: `sudo -u asr /opt/asr/.venv/bin/python -m uvicorn app.main:app`
3. Verify configuration: `sudo systemctl cat asr`
4. Check dependencies: `sudo -u asr /opt/asr/.venv/bin/pip list` 