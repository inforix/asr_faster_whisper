#!/bin/bash

# Development startup script for ASR project
# This script sets necessary environment variables and starts the FastAPI application

echo "🚀 Starting ASR Development Server..."

# Set OpenMP environment variable to fix library conflict on macOS
export KMP_DUPLICATE_LIB_OK=TRUE

# Activate virtual environment
source .venv/bin/activate

# Load environment variables from config file
if [ -f "config.env" ]; then
    echo "📋 Loading configuration from config.env..."
    export $(grep -v '^#' config.env | xargs)
fi

# Start the FastAPI application with uvicorn
echo "🎯 Starting FastAPI server on http://${HOST:-0.0.0.0}:${PORT:-8087}"
uvicorn app.main:app \
    --host ${HOST:-0.0.0.0} \
    --port ${PORT:-8087} \
    --reload \
    --log-level ${LOG_LEVEL:-info} 