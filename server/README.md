# Server

FastAPI backend for speech-to-braille translation with offline-first design.

## Prerequisites

### macOS

```bash
brew install liblouis espeak-ng
```

### Ubuntu / Debian

```bash
sudo apt install liblouis-dev liblouis-data espeak-ng
```

### Windows

1. **liblouis**: Download the latest release from [liblouis/releases](https://github.com/liblouis/liblouis/releases) and extract it. Set the `LIBLOUIS_DIR` environment variable to the extracted path.
   - Alternative: install via MSYS2 — `pacman -S mingw-w64-x86_64-liblouis`

2. **espeak-ng**: Download from [espeak-ng/releases](https://github.com/espeak-ng/espeak-ng/releases) and add to PATH.
   - Alternative: install via MSYS2 — `pacman -S mingw-w64-x86_64-espeak-ng`

## Quick Start

```bash
# Check prerequisites
uv run python scripts/setup.py

# Install Python dependencies
uv sync

# Download voice models (for TTS)
uv run python scripts/download_voices.py

# Start the server
uv run uvicorn speech2braille.main:app --port 8000
```

## Configuration

Copy `.env.example` to `.env` and modify as needed. Key settings:

- `S2B_BRAILLE_DEFAULT_TABLE` — Default braille translation table (default: `en-ueb-g2.ctb`)
- `LIBLOUIS_DIR` — Path to liblouis installation (Windows only, for DLL loading)
- `LOUIS_TABLEPATH` — Custom braille table search paths (`:` separated on Unix, `;` on Windows)

See `.env.example` for all available options.

## Troubleshooting

### liblouis not found

**macOS**: Ensure Homebrew's liblouis is installed (`brew install liblouis`) and `/opt/homebrew/lib` (Apple Silicon) or `/usr/local/lib` (Intel) is accessible.

**Linux**: Install the C library and data: `sudo apt install liblouis-dev liblouis-data`. The old `python3-louis` package is no longer needed.

**Windows**: Set `LIBLOUIS_DIR` to the directory containing `liblouis.dll`. Common locations: `C:\Program Files\liblouis\bin` or `C:\msys64\mingw64\bin`.

### Voice models not found

Run `uv run python scripts/download_voices.py` to download piper voice models.

## Development

### Syncing liblouis bindings

The louis Python ctypes bindings are bundled in `src/liblouis_bridge/louis/`. To update them from your system's liblouis installation:

```bash
uv run python scripts/sync_louis.py
```

### Linting

```bash
uv run ruff check src/
uv run ruff format --check src/
```

## API Docs

Start the server, then visit: http://localhost:8000/docs
