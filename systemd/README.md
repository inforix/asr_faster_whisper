# ASR Systemd Service (Python Mode)

This directory contains the systemd service configuration for the ASR (Automatic Speech Recognition) project running with Python directly (without Docker).

## Files

- `asr.service` - Systemd service unit file
- `README.md` - This file

## Quick Setup

### Automated Installation (Recommended)

```bash
# Run the installation script from the project root
sudo ./scripts/install-systemd.sh
```

### Manual Installation

```bash
# Copy service file
sudo cp asr.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable asr
sudo systemctl start asr
```

## Service Management

```bash
# Start service
sudo systemctl start asr

# Stop service
sudo systemctl stop asr

# Restart service
sudo systemctl restart asr

# Check status
sudo systemctl status asr

# View logs
sudo journalctl -u asr -f
```

## Service Configuration

- **Service Name**: `asr`
- **Working Directory**: `/opt/asr`
- **User**: `asr`
- **Group**: `asr`
- **Port**: `8087`
- **Python Environment**: `/opt/asr/.venv`
- **Dependencies**: `network.target`

## Requirements

- Ubuntu 22.04 LTS
- Python 3.8+ with venv support
- System dependencies (ffmpeg, build tools)
- Dedicated `asr` user account
- Application files in `/opt/asr`
- Python virtual environment in `/opt/asr/.venv`

## Environment Variables

The service automatically sets:
- `PYTHONPATH=/opt/asr`
- `PYTHONUNBUFFERED=1`
- `PYTHONDONTWRITEBYTECODE=1`
- `KMP_DUPLICATE_LIB_OK=TRUE`

Additional variables can be set in `/opt/asr/config.env`.

## Management Scripts

After installation, these commands are available:

- `asr-start` - Start the service
- `asr-stop` - Stop the service
- `asr-restart` - Restart the service
- `asr-status` - Show status and health check
- `asr-logs` - Show real-time logs
- `asr-update` - Update Python dependencies

## Documentation

For complete installation and configuration instructions, see:
- [Systemd Deployment Guide](../docs/systemd-deployment.md)

## Troubleshooting

```bash
# Check service status
sudo systemctl status asr

# View detailed logs
sudo journalctl -u asr --no-pager

# Test Python environment
sudo -u asr /opt/asr/.venv/bin/python -c "import app.main"

# Check port availability
sudo lsof -i :8087

# Test manual startup
sudo -u asr bash -c "
    cd /opt/asr
    export KMP_DUPLICATE_LIB_OK=TRUE
    .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8087
"
```

## Performance Notes

- Service runs with single worker by default
- Memory limit set to 4GB
- Automatic restart on failure
- OpenMP conflicts resolved automatically
- Models downloaded to `/opt/asr/models` for persistence 