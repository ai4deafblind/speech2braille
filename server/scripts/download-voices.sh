#!/usr/bin/env bash
# Download piper voice models from HuggingFace.
# Usage: bash server/scripts/download-voices.sh
# Idempotent: skips files that already exist.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${SCRIPT_DIR}/../models/piper/voices"
BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main"

# Voice paths relative to the base URL
VOICES=(
    "en/en_US/amy/medium/en_US-amy-medium"
    "id/id_ID/news_tts/medium/id_ID-news_tts-medium"
)

mkdir -p "${TARGET_DIR}"

for voice in "${VOICES[@]}"; do
    name="${voice##*/}"
    onnx_file="${TARGET_DIR}/${name}.onnx"
    json_file="${TARGET_DIR}/${name}.onnx.json"

    for ext in ".onnx" ".onnx.json"; do
        local_file="${TARGET_DIR}/${name}${ext}"
        remote_url="${BASE_URL}/${voice}${ext}"

        if [[ -f "${local_file}" ]]; then
            echo "SKIP  ${name}${ext} (already exists)"
        else
            echo "DOWNLOADING  ${name}${ext} ..."
            curl -L --fail --progress-bar -o "${local_file}" "${remote_url}"
            echo "OK    ${name}${ext}"
        fi
    done
done

echo ""
echo "All voice models downloaded to: ${TARGET_DIR}"
