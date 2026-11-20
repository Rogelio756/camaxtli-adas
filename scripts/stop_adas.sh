#!/bin/bash
set -uo pipefail

source /mnt/bigdata/ADAS/adas.env

echo "Deteniendo procesos ADAS en laptop..."
pkill -f "dashboard_server.py" 2>/dev/null && echo "  ✓ dashboard_server.py detenido" || echo "  - dashboard_server.py no estaba corriendo"
pkill -f "main_adas.py" 2>/dev/null && echo "  ✓ main_adas.py detenido" || echo "  - main_adas.py no estaba corriendo"
pkill -f "vision_server.py" 2>/dev/null && echo "  ✓ vision_server.py detenido" || echo "  - vision_server.py no estaba corriendo"

if [ -n "${PI5_IP:-}" ]; then
  ssh -o ConnectTimeout=5 -o BatchMode=yes pi@"$PI5_IP" "pkill -f detection_v2_json.py" 2>/dev/null \
    && echo "  ✓ Pi5 detección detenida" || echo "  - Pi5 no accesible o no corría detección"
fi

if [ -n "${PI4_IP:-}" ]; then
  ssh -o ConnectTimeout=5 -o BatchMode=yes pi@"$PI4_IP" "pkill -f tts_listener.py" 2>/dev/null \
    && echo "  ✓ Pi4 TTS detenido" || echo "  - Pi4 no accesible o no corría TTS"
fi

echo "Listo."
