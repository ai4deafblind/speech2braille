# Server

FastAPI backend for speech-to-braille translation.

## Setup
```bash
uv venv --system-site-packages
source .venv/bin/activate
uv sync
```

## Run
```bash
uv run uvicorn speech2braille.main:app --reload --port 8000
```

## API Docs
http://localhost:8000/docs

## Dependencies
- **faster-whisper**: ASR engine (CTranslate2-based Whisper)
- **python3-louis**: Braille translation (system package required)
