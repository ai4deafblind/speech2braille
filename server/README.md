# Server

FastAPI backend for speech-to-braille translation.

## Prerequisites

### macOS
```bash
brew install liblouis
```

### Linux (Debian/Ubuntu)
```bash
sudo apt install python3-louis
```

## Setup
```bash
uv venv
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
- **liblouis**: Braille translation (C library with Python bindings)

## Troubleshooting

### liblouis not found on macOS
If you see "Failed to load liblouis":
1. Install liblouis: `brew install liblouis`
2. Verify louis package exists in `src/liblouis_bridge/louis/`
3. Check that `/opt/homebrew/lib` is accessible

### liblouis not found on Linux
If you see "liblouis Python bindings not found":
1. Install python3-louis: `sudo apt install python3-louis`
2. Re-create your venv with `uv venv --system-site-packages` if needed
