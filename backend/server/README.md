# Copiloto Server · Node 2

**IP:** 192.168.33.101  
**OS:** Ubuntu 20.04 LTS · Dell G3 3590

## Entry Points

| Script | Descripción |
|---|---|
| `dashboard_server.py` | Flask API + SocketIO · puerto 5000 |
| `main_adas.py` | ADASOrchestrator · orquestador principal |
| `vision_server.py` | LLaVA via Ollama HTTP API · puerto 11434 |
| `mqtt_listener.py` | MQTT listener activo |

## Stack
- Flask + Flask-SocketIO
- LLaVA via Ollama (llava model)
- EasyOCR + PaddleOCR
- Celery + Redis
- paho-mqtt + Mosquitto broker

## API Endpoints

| Endpoint | Método | Descripción |
|---|---|---|
| `/splash` | GET | Splash screen CAMAXTLI |
| `/dashboard` | GET | Dashboard HUD en vivo |
| `/data` | GET | Data Explorer |
| `/api/stats` | GET | Resumen total placas, confianza, sesiones |
| `/api/plates` | GET | Historial paginado ?page=1&limit=10 |
| `/api/sessions` | GET | Confianza OCR por sesión |
| `/api/images` | GET | Galería ROI paginada |
| `/api/images/<file>` | GET | Imagen ROI individual |

## Métricas validadas
- E2E Latency: 230ms
- OCR Precision: 93–96%
- Plates logged: 304+
- Sessions: 5 (Dic 2025 – Jun 2026)

## Variables de entorno (.env)
Ver `.env.example` en la raíz del repositorio.
