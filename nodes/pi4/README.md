# Node 3 · Raspberry Pi 4 + WM8960

**IP:** 192.168.33.103

## Hardware
| Componente | Modelo |
|---|---|
| SBC | Raspberry Pi 4 (4GB) |
| Audio HAT | WM8960 Audio HAT |
| Display | Yodoit 15.6" portable |
| Power | Anker 165W power bank |

## Software Stack
- Python 3.11
- Piper TTS (es_MX-ald-medium)
- paho-mqtt subscriber
- aplay para reproducción de audio

## MQTT
- **Topic:** `adas/tts/speak`
- **Broker:** 192.168.33.101:1883
- **Payload:**
```json
{
  "text": "Placa detectada: 290-WTC. Confianza 98 por ciento.",
  "priority": "normal"
}
```

## Modelo TTS
- **Motor:** Piper TTS
- **Idioma:** Español México (es_MX)
- **Voz:** ald-medium
- **Ruta:** `/home/Roy/piper/models/es_MX/es_MX-ald-medium.onnx`

## Entry Point
```bash
cd ~/ADAS_PI4
source venv_pi4/bin/activate
python3 mqtt_tts_listener.py
```

## Setup
> Documentación en construcción.
