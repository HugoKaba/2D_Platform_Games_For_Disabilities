#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install pyinstaller pygame mediapipe opencv-python SpeechRecognition

pyinstaller --noconfirm \
    --onefile \
    --windowed \
    --name "MiniMarioAR" \
    --add-data "assets:assets" \
    --add-data "save_progress.json:." \
    --collect-all mediapipe \
    main.py
