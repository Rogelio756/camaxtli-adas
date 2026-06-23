# Configuración

## settings.py
Variables globales cargadas desde `.env` via python-dotenv.
No contiene valores hardcodeados.

## Variables principales
- `MQTT_BROKER` — IP del broker Mosquitto
- `PI5_IP` — IP del nodo de detección
- `PI4_IP` — IP del nodo TTS
- `PLATE_MODEL_PATH` — Ruta al modelo ONNX de placas
- `OCR_PYTHON` — Python del venv OCR
