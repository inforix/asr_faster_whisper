#!/bin/bash

# Script to restart ASR service with updated configuration
# This fixes the "invalid host header" error

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

log_info "Restarting ASR service with updated configuration..."

# Stop the service
log_info "Stopping ASR service..."
systemctl stop asr || log_warning "Service was not running"

# Reload systemd daemon to pick up any service file changes
log_info "Reloading systemd daemon..."
systemctl daemon-reload

# Start the service
log_info "Starting ASR service..."
systemctl start asr

# Check status
log_info "Checking service status..."
if systemctl is-active --quiet asr; then
    log_success "ASR service is running successfully!"
    
    # Wait a moment for the service to fully start
    sleep 3
    
    # Test the health endpoint
    log_info "Testing service health..."
    if curl -s http://localhost:8087/health > /dev/null; then
        log_success "Service is responding to health checks!"
        echo ""
        echo "Service is now available at:"
        echo "  - Health check: http://localhost:8087/health"
        echo "  - API docs: http://localhost:8087/docs"
        echo "  - Main endpoint: http://localhost:8087/"
        echo ""
        echo "The 'invalid host header' error should now be resolved."
    else
        log_warning "Service is running but not responding to health checks yet"
        log_info "This is normal during startup. Try again in a few seconds."
    fi
else
    log_error "Failed to start ASR service!"
    echo ""
    echo "Check the service logs with:"
    echo "  sudo journalctl -u asr -f"
    exit 1
fi

echo ""
log_info "You can monitor the service with:"
echo "  sudo systemctl status asr"
echo "  sudo journalctl -u asr -f" 