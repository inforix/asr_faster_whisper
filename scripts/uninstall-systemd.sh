#!/bin/bash

# ASR Project Systemd Uninstallation Script for Ubuntu 22.04
# This script removes the ASR project systemd service (Python mode)

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

confirm_uninstall() {
    echo -e "${YELLOW}WARNING: This will completely remove the ASR service and all its data!${NC}"
    echo "This includes:"
    echo "  - Systemd service"
    echo "  - User account ($ASR_USER)"
    echo "  - Application directory ($ASR_HOME)"
    echo "  - Python virtual environment"
    echo "  - Downloaded AI models"
    echo "  - Management scripts"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Uninstallation cancelled"
        exit 0
    fi
}

stop_and_disable_service() {
    log_info "Stopping and disabling ASR service..."
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        systemctl stop $SERVICE_NAME
        log_success "Service stopped"
    fi
    
    if systemctl is-enabled --quiet $SERVICE_NAME; then
        systemctl disable $SERVICE_NAME
        log_success "Service disabled"
    fi
}

remove_python_environment() {
    log_info "Removing Python virtual environment..."
    
    if [ -d "$ASR_HOME/.venv" ]; then
        rm -rf $ASR_HOME/.venv
        log_success "Python virtual environment removed"
    fi
    
    # Clean up any Python cache files
    if [ -d "$ASR_HOME" ]; then
        find $ASR_HOME -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
        find $ASR_HOME -name "*.pyc" -type f -delete 2>/dev/null || true
        log_success "Python cache files cleaned"
    fi
}

remove_service_file() {
    log_info "Removing systemd service file..."
    
    if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
        rm -f /etc/systemd/system/$SERVICE_NAME.service
        systemctl daemon-reload
        log_success "Service file removed"
    fi
}

remove_management_scripts() {
    log_info "Removing management scripts..."
    
    rm -f /usr/local/bin/asr-*
    log_success "Management scripts removed"
}

remove_user_and_directories() {
    log_info "Removing user and directories..."
    
    # Ask before removing the directory since it's in user's home
    read -p "Remove application directory $ASR_HOME? (y/n): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -d "$ASR_HOME" ]; then
            rm -rf $ASR_HOME
            log_success "Application directory removed"
        fi
    else
        log_info "Keeping application directory"
    fi
    
    # Remove user
    if getent passwd $ASR_USER > /dev/null 2>&1; then
        userdel $ASR_USER 2>/dev/null || true
        log_success "User removed"
    fi
    
    # Remove group if no other users are in it
    if getent group $ASR_GROUP > /dev/null 2>&1; then
        if [ $(getent group $ASR_GROUP | cut -d: -f4 | wc -w) -eq 0 ]; then
            groupdel $ASR_GROUP 2>/dev/null || true
            log_success "Group removed"
        else
            log_warning "Group $ASR_GROUP not removed (other users exist)"
        fi
    fi
}

remove_firewall_rules() {
    log_info "Removing firewall rules..."
    
    if command -v ufw &> /dev/null; then
        ufw delete allow 8087/tcp 2>/dev/null || true
        log_success "Firewall rules removed"
    fi
}

cleanup_system_packages() {
    log_info "Cleaning up system packages..."
    
    read -p "Remove Python development packages? (y/n): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        apt-get autoremove -y python3-dev build-essential pkg-config libffi-dev libssl-dev 2>/dev/null || true
        log_success "Development packages removed"
    else
        log_info "Keeping development packages"
    fi
}

print_completion() {
    log_success "ASR service uninstallation completed!"
    echo ""
    echo "The following have been removed:"
    echo "  ✓ Systemd service"
    echo "  ✓ User account and group"
    echo "  ✓ Management scripts"
    echo "  ✓ Firewall rules"
    echo ""
    if [ -d "$ASR_HOME" ]; then
        echo "Note: Application directory $ASR_HOME was preserved"
    else
        echo "  ✓ Application directory"
        echo "  ✓ Python virtual environment"
    fi
    echo ""
    echo "Note: System Python and core packages were not removed."
    echo "The following packages remain installed:"
    echo "  - python3, python3-pip, python3-venv"
    echo "  - ffmpeg, curl, git"
    echo ""
    echo "If you want to remove them as well, run:"
    echo "  sudo apt-get remove python3-pip python3-venv ffmpeg"
    echo "  sudo apt-get autoremove"
}

# Main uninstallation process
main() {
    log_info "Starting ASR systemd uninstallation (Python mode)..."
    
    check_root
    confirm_uninstall
    stop_and_disable_service
    remove_python_environment
    remove_service_file
    remove_management_scripts
    remove_user_and_directories
    remove_firewall_rules
    cleanup_system_packages
    
    print_completion
}

# Run main function
main "$@" 