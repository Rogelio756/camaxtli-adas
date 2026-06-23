import os
import json
import time
import subprocess
from datetime import datetime
import paho.mqtt.client as mqtt

from app.tasks_lp_proxy import process_plate_event_async

# ----------------------------------------
# CONFIG GENERAL
# ----------------------------------------
BROKER = "192.168.100.139"
TOPIC = "perception/vehicles/detections"
CLIENT_ID = "server_firetest"

DATASET_DIR = "dataset_placas"
os.makedirs(DATASET_DIR, exist_ok=True)

# ----------------------------------------
# DETECTAR CÁMARA
# ----------------------------------------
def detectar_camara():
    dispositivos = os.popen("v4l2-ctl --list-devices").read().splitlines()
    camaras = [l.strip() for l in dispositivos if l.strip().startswith("/dev/video")]
    for cam in camaras:
        if "video2" in cam:
            return "/dev/video2"
    return camaras[0] if camaras else None

# ----------------------------------------
# CONFIGURAR CÁMARA
# ----------------------------------------
def configurar_camara(dev):
    print(f"🧩 Configurando parámetros para {dev}...")
    cmds = [
        f"v4l2-ctl -d {dev} --set-ctrl=focus_auto=1",
        f"v4l2-ctl -d {dev} --set-ctrl=exposure_auto=1",
        f"v4l2-ctl -d {dev} --set-ctrl=brightness=130",
    ]
    for c in cmds:
        subprocess.run(c, shell=True,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)

# ----------------------------------------
# CAPTURAR IMAGEN
# ----------------------------------------
def capturar_imagen(dev):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    capture_path = os.path.join(DATASET_DIR, f"captura_{timestamp}.jpg")

    print(f"📷 Preparando cámara {dev} (espera 2s para enfoque)...")
    time.sleep(2)

    cmd = [
        "ffmpeg", "-f", "v4l2",
        "-input_format", "mjpeg",
        "-analyzeduration", "0",
        "-probesize", "32",
        "-framerate", "30",
        "-video_size", "1280x720",
        "-i", dev,
        "-frames:v", "1",
        capture_path,
        "-y",
        "-hide_banner",
        "-loglevel", "fatal"
    ]
    subprocess.run(cmd)
    return capture_path

# ----------------------------------------
# MQTT CALLBACKS
# ----------------------------------------
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"🔗 Conectado al broker ({BROKER}) - Razón: {reason_code}")
    client.subscribe(TOPIC)
    print(f"📡 Suscrito a: {TOPIC}")


def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    detections = data.get("detections", [])
    if not detections:
        print("⏸ No se detectaron vehículos.")
        return

    print(f"🚘 {len(detections)} vehículo(s) detectado(s).")
    user = input("¿Deseas procesar placas? [y/n]: ").strip().lower()
    if user != "y":
        print("❌ Detección ignorada.")
        return

    det = detections[0]       # solo usamos la primera detección
    bbox = det.get("bbox", [0,0,0,0])

    dev = detectar_camara()
    if not dev:
        print("❌ No se encontró ninguna cámara.")
        return

    configurar_camara(dev)
    capture_path = capturar_imagen(dev)

    if not os.path.exists(capture_path):
        print("❌ Error al capturar imagen.")
        return

    print(f"📸 Imagen capturada: {capture_path}")

    # -----------------------------------
    # CONSTRUIR EVENTO COMPLETO PARA CELERY
    # -----------------------------------
    timestamp_actual = datetime.now().isoformat()

    event = {
        "image_path": os.path.abspath(capture_path),
        "bbox": bbox,
        "camera_id": "server_cam",
        "vehicle_id": det.get("vehicle_id", "veh_from_mqtt"),
        "vehicle_type": det.get("class", "unknown"),
        "vehicle_conf": det.get("confidence", 0.0),
        "timestamp": timestamp_actual
    }

    print("🧠 Enviando procesamiento de placa al worker Celery...")
    result = process_plate_event_async(event)
    print(f"📨 Task enviada. ID: {result.id}")


# ----------------------------------------
# MAIN
# ----------------------------------------
def main():
    client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv5)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, 1883, 60)
    print(f"🚀 Esperando publicaciones desde {BROKER} en {TOPIC}...")
    client.loop_forever()


if __name__ == "__main__":
    main()
