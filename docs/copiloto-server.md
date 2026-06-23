# Node 2 · Copiloto Server

## Hardware
- Dell G3 3590
- Ubuntu 20.04 LTS

## Network
- IP: 192.168.33.101
- MQTT Broker: Mosquitto (port 1883)
- Dashboard: Flask (port 5000)

## Software Stack
- Flask + Flask-SocketIO
- LLaVA via Ollama (port 11434)
- EasyOCR + PaddleOCR
- Celery + Redis
- paho-mqtt

## Key Metrics
- E2E Latency: 230ms
- OCR Precision: 93-96%

## Entry Points
- dashboard_server.py — Flask API + SocketIO
- main_adas.py — ADASOrchestrator
- vision_server.py — LLaVA HTTP API
