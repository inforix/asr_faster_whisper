#!/bin/bash

# ASR Project Systemd Installation Script for Ubuntu 22.04
# This script installs the ASR project as a systemd service using Python

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ASR_USER="asr"
ASR_GROUP="asr"
ASR_HOME="/home/jwc/develop/faster_whisper"
SERVICE_NAME="asr"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_VERSION="3.11"

# Functions
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

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_ubuntu() {
    if ! grep -q "Ubuntu 22" /etc/os-release; then
        log_warning "This script is designed for Ubuntu 22.04. Proceeding anyway..."
    fi
}

install_dependencies() {
    log_info "Installing required dependencies..."
    
    # Update package list
    apt-get update
    
    # Install Python and system dependencies
    apt-get install -y \
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
    
    log_success "System dependencies installed successfully"
}

create_user() {
    log_info "Creating ASR user and group..."
    
    # Create group if it doesn't exist
    if ! getent group $ASR_GROUP > /dev/null 2>&1; then
        groupadd $ASR_GROUP
        log_success "Created group: $ASR_GROUP"
    else
        log_info "Group $ASR_GROUP already exists"
    fi
    
    # Create user if it doesn't exist
    if ! getent passwd $ASR_USER > /dev/null 2>&1; then
        useradd -r -g $ASR_GROUP -d $ASR_HOME -s /bin/bash -c "ASR Service User" $ASR_USER
        log_success "Created user: $ASR_USER"
    else
        log_info "User $ASR_USER already exists"
    fi
}

setup_directories() {
    log_info "Setting up directories..."
    
    # Create ASR home directory
    mkdir -p $ASR_HOME
    mkdir -p $ASR_HOME/models
    mkdir -p $ASR_HOME/logs
    
    # Copy project files
    log_info "Copying project files..."
    cp -r $CURRENT_DIR/* $ASR_HOME/
    
    # Set ownership
    chown -R $ASR_USER:$ASR_GROUP $ASR_HOME
    chmod -R 755 $ASR_HOME
    
    # Make scripts executable
    if [ -d "$ASR_HOME/scripts" ]; then
        chmod +x $ASR_HOME/scripts/*.sh
    fi
    
    log_success "Directories set up successfully"
}

setup_python_environment() {
    log_info "Setting up Python virtual environment..."
    
    # Create virtual environment as ASR user
    sudo -u $ASR_USER python3 -m venv $ASR_HOME/.venv
    
    # Upgrade pip
    sudo -u $ASR_USER $ASR_HOME/.venv/bin/pip install --upgrade pip
    
    # Install Python dependencies
    log_info "Installing Python dependencies..."
    sudo -u $ASR_USER $ASR_HOME/.venv/bin/pip install -r $ASR_HOME/requirements.txt
    
    log_success "Python environment set up successfully"
}

download_models() {
    log_info "Pre-downloading AI models..."
    
    # Download Whisper model
    sudo -u $ASR_USER bash -c "
        cd $ASR_HOME
        export KMP_DUPLICATE_LIB_OK=TRUE
        .venv/bin/python -c \"
from faster_whisper import WhisperModel
import os
print('Downloading Whisper model...')
model = WhisperModel('large-v3', device='cpu', download_root='$ASR_HOME/models')
print('Whisper model downloaded successfully')
\"
    " || log_warning "Failed to download Whisper model (will download on first use)"
    
    log_success "Model download completed"
}

install_service() {
    log_info "Installing systemd service..."
    
    # Copy service file
    cp $CURRENT_DIR/systemd/asr.service /etc/systemd/system/
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service
    systemctl enable $SERVICE_NAME
    
    log_success "Systemd service installed and enabled"
}

create_management_scripts() {
    log_info "Creating management scripts..."
    
    # Create start script
    cat > /usr/local/bin/asr-start << 'EOF'
#!/bin/bash
systemctl start asr
EOF
    
    # Create stop script
    cat > /usr/local/bin/asr-stop << 'EOF'
#!/bin/bash
systemctl stop asr
EOF
    
    # Create restart script
    cat > /usr/local/bin/asr-restart << 'EOF'
#!/bin/bash
systemctl restart asr
EOF
    
    # Create status script
    cat > /usr/local/bin/asr-status << 'EOF'
#!/bin/bash
systemctl status asr
echo ""
echo "Service health check:"
curl -s http://localhost:8087/health | python3 -m json.tool 2>/dev/null || echo "Service not responding"
EOF
    
    # Create logs script
    cat > /usr/local/bin/asr-logs << 'EOF'
#!/bin/bash
journalctl -u asr -f
EOF
    
    # Create update script
    cat > /usr/local/bin/asr-update << 'EOF'
#!/bin/bash
echo "Stopping ASR service..."
systemctl stop asr

echo "Updating Python dependencies..."
cd /home/jwc/develop/faster_whisper
sudo -u asr .venv/bin/pip install --upgrade -r requirements.txt

echo "Starting ASR service..."
systemctl start asr

echo "Update completed!"
EOF
    
    # Make scripts executable
    chmod +x /usr/local/bin/asr-*
    
    log_success "Management scripts created"
}

configure_firewall() {
    log_info "Configuring firewall..."
    
    if command -v ufw &> /dev/null; then
        # Allow ASR service port
        ufw allow 8087/tcp comment "ASR Service"
        
        log_success "Firewall configured"
    else
        log_warning "UFW not found, skipping firewall configuration"
    fi
}

print_usage() {
    log_success "Installation completed successfully!"
    echo ""
    echo "Management commands:"
    echo "  asr-start    - Start the ASR service"
    echo "  asr-stop     - Stop the ASR service"
    echo "  asr-restart  - Restart the ASR service"
    echo "  asr-status   - Show service status and health"
    echo "  asr-logs     - Show service logs"
    echo "  asr-update   - Update Python dependencies"
    echo ""
    echo "Systemd commands:"
    echo "  sudo systemctl start asr     - Start service"
    echo "  sudo systemctl stop asr      - Stop service"
    echo "  sudo systemctl restart asr   - Restart service"
    echo "  sudo systemctl status asr    - Show status"
    echo "  sudo systemctl enable asr    - Enable auto-start"
    echo "  sudo systemctl disable asr   - Disable auto-start"
    echo ""
    echo "Service will be available at: http://localhost:8087"
    echo "Health check: curl http://localhost:8087/health"
    echo "API documentation: http://localhost:8087/docs"
    echo ""
    echo "Application directory: $ASR_HOME"
    echo "To start the service now, run: sudo systemctl start asr"
}

# Main installation process
main() {
    log_info "Starting ASR systemd installation (Python mode)..."
    
    check_root
    check_ubuntu
    install_dependencies
    create_user
    setup_directories
    setup_python_environment
    download_models
    install_service
    create_management_scripts
    configure_firewall
    
    print_usage
}

# Run main function
main "$@" 