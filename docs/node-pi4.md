# Node 3 · Raspberry Pi 4 + WM8960

## Hardware
- Raspberry Pi 4 (4GB RAM)
- WM8960 Audio HAT
- Yodoit 15.6 portable display
- Anker 165W power bank

## Network
- IP: 192.168.33.103
- MQTT Subscriber: adas/tts/speak

## Software Stack
- Piper TTS (es_MX-ald-medium model)
- paho-mqtt
- aplay for audio output

## Entry Point
nodes/pi4/tts_listener.py
