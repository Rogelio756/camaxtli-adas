# Node 1 · Raspberry Pi 5 + Hailo-8 NPU

**IP:** 192.168.33.100

## Hardware
| Componente | Modelo |
|---|---|
| SBC | Raspberry Pi 5 (8GB) |
| AI Accelerator | Hailo-8 AI HAT+ (26 TOPS) |
| Camera | USB Camera |

## Software Stack
- Python 3.11
- Hailo TAPPAS Runtime
- YOLOv8n compilado a HEF (19MB · −88% vs original 158MB)
- paho-mqtt publisher

## Modelo
- **Arquitectura:** YOLOv8n
- **Dataset:** BDD100K (vehicle detection)
- **Formato:** HEF (Hailo Executable Format)
- **mAP₅₀:** 0.986
- **FPS:** 30–58 en tiempo real

## MQTT
- **Topic:** `perception/vehicles/detections`
- **Broker:** 192.168.33.101:1883
- **Payload:**
```json
{
  "timestamp": "1234567",
  "detections": [
    {"label": "car", "confidence": 0.89, "bbox": [x1,y1,x2,y2]}
  ]
}
```

## Entry Point
```bash
cd ~/ADAS
source venv/bin/activate
python detection_v2_json.py
```

## Stream MJPEG
Disponible en `http://192.168.33.100:8080/video_feed`
