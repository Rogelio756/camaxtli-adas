#!/bin/bash
set -uo pipefail

# ── Load environment ──
source /mnt/bigdata/ADAS/adas.env

ADAS_ROOT=/mnt/bigdata/ADAS
COPILOTO="$ADAS_ROOT/copiloto_server"
VENV="$COPILOTO/venv_server"

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

# ── Limpieza: matar instancias previas para evitar choques de puerto ──
echo "[0/6] Deteniendo instancias previas..."
pkill -f "dashboard_server.py" 2>/dev/null || true
pkill -f "main_adas.py" 2>/dev/null || true
pkill -f "vision_server.py" 2>/dev/null || true
sleep 1

# ── Mosquitto (ya corre como systemd; no relanzar si está activo) ──
echo "[1/6] Verificando Mosquitto MQTT broker..."
if systemctl is-active --quiet mosquitto; then
  STATUS+=("✓ Mosquitto (systemd, ya activo)")
else
  mosquitto -d 2>/dev/null && STATUS+=("✓ Mosquitto (lanzado)") || STATUS+=("✗ Mosquitto — no se pudo iniciar")
fi

# ── Redis (requerido para SocketIO message_queue entre procesos) ──
echo "[2/6] Verificando Redis..."
if redis-cli ping >/dev/null 2>&1; then
  STATUS+=("✓ Redis")
else
  STATUS+=("✗ Redis — no responde, dashboard_server/main_adas no podrán sincronizar eventos")
fi

source "$VENV/bin/activate"

# ── Dashboard Server (Flask + SocketIO) ──
echo "[3/6] Iniciando dashboard_server.py..."
nohup python3 "$COPILOTO/dashboard_server.py" > /tmp/dashboard_server.log 2>&1 &
DASH_PID=$!
sleep 2
if kill -0 "$DASH_PID" 2>/dev/null; then
  STATUS+=("✓ Dashboard server (PID $DASH_PID) · puerto 5000")
else
  STATUS+=("✗ Dashboard server — revisa /tmp/dashboard_server.log")
fi

# ── Orquestador principal (MQTT + cámara + YOLO + OCR + LLM) ──
echo "[4/6] Iniciando main_adas.py..."
cd "$COPILOTO"
nohup python3 "$COPILOTO/main_adas.py" > /tmp/main_adas.log 2>&1 &
MAIN_PID=$!
sleep 2
if kill -0 "$MAIN_PID" 2>/dev/null; then
  STATUS+=("✓ main_adas orquestador (PID $MAIN_PID)")
else
  STATUS+=("✗ main_adas — revisa /tmp/main_adas.log")
fi

# ── Vision server (LLaVA vía Ollama) ──
echo "[5/6] Iniciando vision_server.py..."
nohup python3 "$COPILOTO/vision_server.py" > /tmp/vision_server.log 2>&1 &
VISION_PID=$!
sleep 2
if kill -0 "$VISION_PID" 2>/dev/null; then
  STATUS+=("✓ Vision server LLaVA (PID $VISION_PID) · puerto 8001")
else
  STATUS+=("✗ Vision server — revisa /tmp/vision_server.log")
fi

deactivate

# ── Abrir navegador ──
echo "[6/6] Abriendo dashboard en navegador..."
sleep 2
xdg-open http://localhost:5000/splash 2>/dev/null &

# ── Remote Pi5 ──
echo ""
echo "Conectando a nodos remotos..."
if [ -n "${PI5_IP:-}" ]; then
  if ssh -o ConnectTimeout=5 -o BatchMode=yes pi@"$PI5_IP" \
    "cd ~/adas && source venv/bin/activate && nohup python3 detection_v2_json.py > /tmp/detect.log 2>&1 & disown" \
    >/tmp/ssh_pi5.log 2>&1; then
    STATUS+=("✓ Pi5 · Hailo-8 (${PI5_IP})")
  else
    STATUS+=("✗ Pi5 · SSH falló (${PI5_IP}) — ver /tmp/ssh_pi5.log, iniciar detección manualmente")
  fi
else
  STATUS+=("✗ Pi5 · PI5_IP no definida en adas.env")
fi

# ── Remote Pi4 ──
if [ -n "${PI4_IP:-}" ]; then
  if ssh -o ConnectTimeout=5 -o BatchMode=yes pi@"$PI4_IP" \
    "cd ~/adas && source venv/bin/activate && nohup python3 tts_listener.py > /tmp/tts.log 2>&1 & disown" \
    >/tmp/ssh_pi4.log 2>&1; then
    STATUS+=("✓ Pi4 · TTS (${PI4_IP})")
  else
    STATUS+=("✗ Pi4 · SSH falló (${PI4_IP}) — ver /tmp/ssh_pi4.log, iniciar TTS manualmente")
  fi
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
echo "             /tmp/main_adas.log"
echo "             /tmp/vision_server.log"
echo ""
