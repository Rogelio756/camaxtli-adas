#!/bin/bash
# Setup Node 3 — RPi4 + WM8960 TTS
# Run once on a fresh Raspberry Pi 4

set -e

echo "[1/4] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y python3-pip alsa-utils espeak-ng

echo "[2/4] Installing Piper TTS (es_MX-ald-medium)..."
pip3 install piper-tts==1.2.0

# Download the Spanish MX voice model
mkdir -p ~/piper_models
cd ~/piper_models
wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/ald/medium/es_MX-ald-medium.onnx
wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/ald/medium/es_MX-ald-medium.onnx.json
echo "  Voice model downloaded to ~/piper_models/"

echo "[3/4] Installing Python dependencies..."
pip3 install paho-mqtt==1.6.1

echo "[4/4] Verifying WM8960 audio HAT..."
aplay -l | grep -i "wm8960" && echo "  WM8960 detected OK" || echo "  WARNING: WM8960 not found — check HAT connection"

echo ""
echo "Setup complete. Run with:"
echo "  python3 tts_listener.py"
echo ""
echo "MQTT broker expected at: 192.168.33.101:1883"
echo "Subscribe topic: adas/tts/speak"
