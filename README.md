# Speech2Braille

Offline-first speech-to-braille translation for deafblind users. Runs on Raspberry Pi 5.

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- pnpm
- System package: `python3-louis`

### Server
```bash
cd server
uv venv --system-site-packages && source .venv/bin/activate
uv sync
uv run uvicorn speech2braille.main:app --reload --port 8000
```

### Client
```bash
cd client
pnpm install
pnpm dev
```

Open http://localhost:5173 and connect to the WebSocket server.

## Stack
- **Server**: FastAPI, faster-whisper, Liblouis
- **Client**: React 19, Vite, TailwindCSS, TanStack Router/Query

See [SPEC.md](SPEC.md) for architectural details.
