import csv
import time
import json
import argparse
import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

CSV_PATH = Path("app/data/vehicle_events.csv")
TOPIC = "perception/vehicles/cam-front"

def read_csv():
    """Lee el CSV actual y devuelve lista de timestamps"""
    if not CSV_PATH.exists():
        return []
    with open(CSV_PATH, newline='') as f:
        reader = csv.DictReader(f)
        return [row for row in reader]

def on_connect(client, userdata, flags, rc):
    print(f"[🚀] Conectado al broker MQTT con código {rc}")

def main(broker="localhost", count=10, interval=0.5):
    print(f"\n[⚙️] Iniciando prueba con {count} mensajes...")

    # --- Estado inicial del CSV ---
    before = read_csv()
    base_len = len(before)

    # --- Cliente MQTT ---
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(broker, 1883, 60)
    client.loop_start()

    # --- Publicación de mensajes ---
    timestamps_sent = {}
    for i in range(count):
        payload = {
            "camera_id": "sim_pi5",
            "timestamp_ms": int(time.time() * 1000),
            "detections": [{"cls": "car", "score": 0.9, "x1": 0.1, "y1": 0.2, "x2": 0.4, "y2": 0.5}],
        }
        client.publish(TOPIC, json.dumps(payload), qos=1)
        timestamps_sent[payload["timestamp_ms"]] = time.time()
        print(f"[📤] Mensaje {i+1}/{count} enviado.")
        time.sleep(interval)

    client.loop_stop()

    # --- Esperar procesamiento ---
    print("\n[⏳] Esperando que Celery procese tareas...")
    time.sleep(5 + count * interval)

    # --- Leer CSV actualizado ---
    after = read_csv()
    new_rows = after[base_len:]
    print(f"[📈] Se detectaron {len(new_rows)} nuevas filas en CSV.")

    # --- Calcular latencias ---
    latencies = []
    for row in new_rows:
        ts_sent_ms = int(row.get("timestamp_ms", "0") or "0")
        if ts_sent_ms in timestamps_sent:
            latency = (time.time() - timestamps_sent[ts_sent_ms]) * 1000
            latencies.append(latency)

    if not latencies:
        print("[⚠️] No se pudieron asociar timestamps; revisa los IDs de correlación.")
        return

    avg_lat = sum(latencies) / len(latencies)
    print(f"\n[✅] Resultados de validación:")
    print(f"   • Mensajes enviados: {count}")
    print(f"   • Mensajes procesados: {len(latencies)}")
    print(f"   • Latencia promedio: {avg_lat:.2f} ms")
    print(f"   • Mín: {min(latencies):.2f} ms | Máx: {max(latencies):.2f} ms")

    # --- Guardar resultados ---
    result_file = Path("validation_results.csv")
    with open(result_file, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["msg_index", "latency_ms"])
        for i, val in enumerate(latencies, 1):
            writer.writerow([i, round(val, 2)])
    print(f"[💾] Resultados guardados en {result_file.resolve()}")

    # --- Graficar ---
    plt.figure(figsize=(8, 4))
    plt.bar(range(1, len(latencies)+1), latencies, color='skyblue')
    plt.xlabel("Mensaje")
    plt.ylabel("Latencia (ms)")
    plt.title(f"Latencia promedio: {avg_lat:.2f} ms")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--broker", default="localhost")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--interval", type=float, default=0.5)
    args = parser.parse_args()
    main(broker=args.broker, count=args.count, interval=args.interval)
