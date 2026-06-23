# Node 1 · Raspberry Pi 5 + Hailo-8

## Hardware
- Raspberry Pi 5 (8GB RAM)
- Hailo-8 AI HAT+ (26 TOPS)
- USB Camera

## Network
- IP: 192.168.33.100
- MQTT Publisher: perception/vehicles/detections

## Software Stack
- YOLOv8n compiled to HEF format (19MB, -88% size)
- Hailo Runtime + TAPPAS
- Python 3.11 + paho-mqtt

## Key Metrics
- 30-58 FPS real-time detection
- mAP50: 0.986
- Model: BDD100K dataset (vehicle detection)

## Entry Point
detection_v2_json.py
