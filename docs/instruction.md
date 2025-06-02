# Development Instructions for ASR Project

## Environment Setup

### Prerequisites
- Python 3.11+ (Note: Python 3.13 may have compatibility issues with PyTorch)
- macOS/Linux/Windows
- Git
- Docker (optional, for containerized deployment)

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd asr
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Common Issues and Solutions

#### OpenMP Library Conflict (macOS)
If you encounter the error:
```
OMP: Error #15: Initializing libiomp5.dylib, but found libiomp5.dylib already initialized.
```

**Solution**: Set the environment variable:
```bash
export KMP_DUPLICATE_LIB_OK=TRUE
```

This is already configured in:
- `config.env` file
- `.vscode/launch.json` debug configurations
- `run_dev.sh` startup script

#### PyTorch Installation Issues
If PyTorch installation fails with Python 3.13:

**Option 1**: Use Python 3.11 or 3.12
```bash
pyenv install 3.11.9
pyenv local 3.11.9
```

**Option 2**: Install PyTorch nightly build
```bash
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cpu
```

## Development Workflow

### Running the Application

#### Method 1: Using the startup script (Recommended)
```bash
./run_dev.sh
```

#### Method 2: Manual startup
```bash
source .venv/bin/activate
export KMP_DUPLICATE_LIB_OK=TRUE
uvicorn app.main:app --host 127.0.0.1 --port 8005 --reload
```

#### Method 3: Using VS Code debugger
1. Open VS Code
2. Go to Debug panel (Ctrl+Shift+D)
3. Select "Debug FastAPI with Uvicorn"
4. Press F5

### API Endpoints

- **Health Check**: `GET /health`
- **API Documentation**: `GET /docs` (development only)
- **Voice Recognition**: `POST /api/voice/transcribe`
- **Text-to-Speech**: `POST /api/tts/synthesize`
- **Metrics**: `GET /metrics` (if enabled)

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_whisper.py

# Run with coverage
pytest --cov=app tests/
```

### Code Quality

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Type checking
mypy app/
```

## VS Code Configuration

The project includes pre-configured VS Code settings:

### Debug Configurations
- **Debug FastAPI App**: Direct Python execution
- **Debug FastAPI with Uvicorn**: Recommended for development
- **Debug Whisper Service**: For speech recognition debugging
- **Debug TTS Service**: For text-to-speech debugging
- **Debug Current File**: For debugging any Python file
- **Debug Tests**: For running and debugging tests

### Environment Variables
All debug configurations include:
- `KMP_DUPLICATE_LIB_OK=TRUE` (OpenMP fix)
- `PYTHONPATH` set to workspace folder
- Development environment settings

## Docker Development

### Build and run with Docker
```bash
docker build -t asr-app .
docker run -p 8005:8005 asr-app
```

### Docker Compose (if available)
```bash
docker-compose up --build
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure `PYTHONPATH` includes the project root
2. **Model download failures**: Check internet connection and disk space
3. **Audio processing errors**: Verify FFmpeg installation
4. **Port conflicts**: Change port in configuration if 8005 is occupied

### Logging

The application uses structured logging. Check logs for detailed error information:
- Development: Console output with DEBUG level
- Production: Structured JSON logs

### Performance Monitoring

Access metrics at `/metrics` endpoint when `ENABLE_METRICS=true` in configuration. 