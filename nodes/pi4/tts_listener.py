"""
tts_listener.py — Pi4 TTS node
Escucha 'adas/tts/speak' vía MQTT y sintetiza voz con Piper TTS.

Requisitos en Pi4:
  pip install paho-mqtt
  apt install piper   (o instalar binario desde github.com/rhasspy/piper)

Uso:
  python tts_listener.py [--broker 192.168.33.101] [--model es_MX-...]
"""

import argparse
import json
import subprocess
import tempfile
import os
import paho.mqtt.client as mqtt

TOPIC = "adas/tts/speak"

DEFAULT_BROKER = "192.168.33.101"   # laptop — broker Mosquitto
DEFAULT_MODEL  = "/home/pi/piper/models/es_MX-claude-medium.onnx"


def speak(text: str, model_path: str) -> None:
    """Sintetiza text con Piper y lo reproduce con aplay."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
    try:
        subprocess.run(
            ["piper", "--model", model_path, "--output_file", wav_path],
            input=text.encode(),
            check=True,
            timeout=15,
        )
        subprocess.run(["aplay", "-q", wav_path], check=True, timeout=10)
    except FileNotFoundError as e:
        print(f"[TTS] Binario no encontrado: {e}. Instala piper y aplay.")
    except subprocess.CalledProcessError as e:
        print(f"[TTS] Error en síntesis/reproducción: {e}")
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)


def on_connect(client, userdata, flags, rc):
    print(f"[TTS] Conectado al broker — suscrito a '{TOPIC}'")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        text = payload.get("text", "").strip()
        if not text:
            return
        print(f"[TTS] Reproduciendo: {text[:80]}")
        speak(text, userdata["model"])
    except Exception as e:
        print(f"[TTS] Error procesando mensaje: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", default=DEFAULT_BROKER)
    parser.add_argument("--model",  default=DEFAULT_MODEL)
    args = parser.parse_args()

    client = mqtt.Client(userdata={"model": args.model})
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[TTS] Conectando a {args.broker}:1883 ...")
    client.connect(args.broker, 1883, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
