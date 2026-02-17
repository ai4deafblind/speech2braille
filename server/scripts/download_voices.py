"""Download piper voice models from HuggingFace.

Usage: uv run python scripts/download_voices.py
Idempotent: skips files that already exist.
"""

import sys
import urllib.request
from pathlib import Path

BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

# Voice paths relative to the base URL
VOICES = [
    "en/en_US/amy/medium/en_US-amy-medium",
    "id/id_ID/news_tts/medium/id_ID-news_tts-medium",
]


def download_voices() -> None:
    script_dir = Path(__file__).resolve().parent
    target_dir = script_dir.parent / "models" / "piper" / "voices"
    target_dir.mkdir(parents=True, exist_ok=True)

    for voice in VOICES:
        name = voice.rsplit("/", 1)[-1]

        for ext in (".onnx", ".onnx.json"):
            local_file = target_dir / f"{name}{ext}"
            remote_url = f"{BASE_URL}/{voice}{ext}"

            if local_file.exists():
                print(f"SKIP  {name}{ext} (already exists)")
                continue

            print(f"DOWNLOADING  {name}{ext} ...")
            try:
                urllib.request.urlretrieve(remote_url, local_file)
                print(f"OK    {name}{ext}")
            except Exception as e:
                print(f"FAILED  {name}{ext}: {e}", file=sys.stderr)
                if local_file.exists():
                    local_file.unlink()
                sys.exit(1)

    print(f"\nAll voice models downloaded to: {target_dir}")


if __name__ == "__main__":
    download_voices()
