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
echo "🎯 Starting FastAPI server on http://${HOST:-127.0.0.1}:${PORT:-8005}"
uvicorn app.main:app \
    --host ${HOST:-127.0.0.1} \
    --port ${PORT:-8005} \
    --reload \
    --log-level ${LOG_LEVEL:-info} 