#!/bin/bash
set -euo pipefail

# ── Load environment ──
source /mnt/bigdata/ADAS/adas.env

# ── ASCII banner ──
echo ""
echo "   ██████╗ █████╗ ███╗   ███╗ █████╗ ██╗  ██╗████████╗██╗     ██╗"
echo "  ██╔════╝██╔══██╗████╗ ████║██╔══██╗╚██╗██╔╝╚══██╔══╝██║     ██║"
echo "  ██║     ███████║██╔████╔██║███████║ ╚███╔╝    ██║   ██║     ██║"
echo "  ██║     ██╔══██║██║╚██╔╝██║██╔══██║ ██╔██╗    ██║   ██║     ██║"
echo "  ╚██████╗██║  ██║██║ ╚═╝ ██║██║  ██║██╔╝ ██╗   ██║   ███████╗██║"
echo "   ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝"
echo ""
echo "   ADVANCED DRIVER ASSISTANCE SYSTEM · MCPR 2026"
echo "   Tlaxcala · Ciudad de México"
echo ""

STATUS=()

# ── Mosquitto ──
echo "[1/5] Iniciando Mosquitto MQTT broker..."
mosquitto -d 2>/dev/null && STATUS+=("✓ Mosquitto") || STATUS+=("✗ Mosquitto")
sleep 2

# ── Copiloto Server (Flask + SocketIO) ──
echo "[2/5] Iniciando copiloto_server (dashboard_server.py)..."
source /mnt/bigdata/ADAS/venv_server/bin/activate
nohup python3 /mnt/bigdata/ADAS/copiloto_server/dashboard_server.py \
  > /tmp/dashboard_server.log 2>&1 &
DASH_PID=$!
deactivate
STATUS+=("✓ Dashboard server (PID $DASH_PID)")

# ── Celery worker ──
echo "[3/5] Iniciando Celery worker..."
source /mnt/bigdata/ADAS/venv_server/bin/activate
nohup celery -A /mnt/bigdata/ADAS/copiloto_server/celery_app worker \
  --loglevel=info > /tmp/celery_worker.log 2>&1 &
CELERY_PID=$!
deactivate
STATUS+=("✓ Celery worker (PID $CELERY_PID)")

# ── Open browser ──
echo "[4/5] Abriendo dashboard en navegador..."
sleep 3
xdg-open http://localhost:5000/splash 2>/dev/null &

# ── Remote Pi5 ──
echo "[5a/5] Iniciando detección en Pi5 (${PI5_IP:-PI5_IP_NOT_SET})..."
if [ -n "${PI5_IP:-}" ]; then
  ssh -o ConnectTimeout=5 pi@"$PI5_IP" \
    "cd ~/adas && source venv/bin/activate && nohup python3 detection_v2_json.py > /tmp/detect.log 2>&1 &" \
    2>/dev/null &
  STATUS+=("✓ Pi5 · Hailo-8 (${PI5_IP})")
else
  STATUS+=("✗ Pi5 · PI5_IP no definida en adas.env")
fi

# ── Remote Pi4 ──
echo "[5b/5] Iniciando TTS listener en Pi4 (${PI4_IP:-PI4_IP_NOT_SET})..."
if [ -n "${PI4_IP:-}" ]; then
  ssh -o ConnectTimeout=5 pi@"$PI4_IP" \
    "cd ~/adas && source venv/bin/activate && nohup python3 tts_listener.py > /tmp/tts.log 2>&1 &" \
    2>/dev/null &
  STATUS+=("✓ Pi4 · TTS (${PI4_IP})")
else
  STATUS+=("✗ Pi4 · PI4_IP no definida en adas.env")
fi

# ── Status report ──
echo ""
echo "══════════════════════════════════════════"
echo "  CAMAXTLI ADAS · Estado de nodos"
echo "══════════════════════════════════════════"
for s in "${STATUS[@]}"; do
  echo "  $s"
done
echo "══════════════════════════════════════════"
echo ""
echo "  Dashboard: http://localhost:5000/splash"
echo "  Logs:      /tmp/dashboard_server.log"
echo "             /tmp/celery_worker.log"
echo ""
