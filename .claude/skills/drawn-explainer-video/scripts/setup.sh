#!/usr/bin/env bash
# One-time setup: Python deps, fonts and a Piper voice into ../assets
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
A="$DIR/assets"
mkdir -p "$A/fonts" "$A/voices"

command -v ffmpeg >/dev/null || { echo "ffmpeg is required (apt-get install -y ffmpeg)"; exit 1; }
python3 -c "import skia" 2>/dev/null || {
  pip install -q skia-python numpy
  python3 -c "import skia" 2>/dev/null || { apt-get install -y -q libegl1 >/dev/null 2>&1 || true; }
}
python3 -c "import piper" 2>/dev/null || pip install -q piper-tts
python3 -c "import whisper" 2>/dev/null || pip install -q openai-whisper || echo "whisper unavailable: captions will use proportional timing (--no-whisper)"

GF=https://raw.githubusercontent.com/google/fonts/main
fetch() { [ -s "$A/fonts/$2" ] || curl -fsSL -o "$A/fonts/$2" "$1"; }
fetch "$GF/ofl/architectsdaughter/ArchitectsDaughter-Regular.ttf" ArchitectsDaughter-Regular.ttf
fetch "$GF/apache/permanentmarker/PermanentMarker-Regular.ttf" PermanentMarker-Regular.ttf
fetch "$GF/ofl/kalam/Kalam-Bold.ttf" Kalam-Bold.ttf
fetch "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-Bold.ttf" Montserrat-Bold.ttf

VOICE="${1:-en/en_US/lessac/high/en_US-lessac-high}"
N="$(basename "$VOICE")"
HF=https://huggingface.co/rhasspy/piper-voices/resolve/main
[ -s "$A/voices/$N.onnx" ] || curl -fsSL -o "$A/voices/$N.onnx" "$HF/$VOICE.onnx"
[ -s "$A/voices/$N.onnx.json" ] || curl -fsSL -o "$A/voices/$N.onnx.json" "$HF/$VOICE.onnx.json"
echo "ready: fonts + voice $N in $A"
