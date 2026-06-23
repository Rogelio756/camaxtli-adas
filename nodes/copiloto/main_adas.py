import json
import os
import time
from datetime import datetime
import cv2
import requests
from flask_socketio import SocketIO as _SocketIO

# Emisor desacoplado — usa Redis como bus; no importa dashboard_server
_sio = _SocketIO(message_queue="redis://")

from managers.mqtt_manager import MQTTManager
from managers.camera_manager import CameraManager
from managers.plate_detector import PlateDetector
from managers.ocr_client import OCRClient
from managers.data_logger import DataLogger

from config.settings import (
    MQTT_TOPIC,
    CAMERA_DEVICE,
    CSV_PATH,
    RAW_DIR,
    ROI_DIR,
    OCR_INTERVAL_SEC,
    PI5_FRAME_WIDTH,
    PI5_FRAME_HEIGHT
)

VISION_SERVER_URL = "http://localhost:8001/describe"

DASHBOARD_STATE_FILE = "dashboard_state.json"


# ============================================================
# 📌 Guardar estado en dashboard_state.json
# ============================================================
def update_dashboard(plate_text, plate_conf, raw_path, roi_path, msg, llm_description=None):
    state = {
        "timestamp": datetime.now().isoformat(),
        "raw_path": raw_path,
        "roi_path": roi_path,
        "plate_text": plate_text,
        "confidence": plate_conf,
        "last_json": msg,
        "llm_description": llm_description
    }
    with open(DASHBOARD_STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)


# ============================================================
#                  🚘 ADAS ORCHESTRATOR
# ============================================================
class ADASOrchestrator:
    def __init__(self):
        print("🧠 Inicializando ADAS Orchestrator…")

        self.mqtt = MQTTManager(topic=MQTT_TOPIC)
        self.camera = CameraManager(CAMERA_DEVICE)
        self.plates = PlateDetector()
        self.ocr = OCRClient()
        self.logger = DataLogger(CSV_PATH)

        self.last_ocr_time = 0
        self._last_cycle_ts = 0.0
        self._ocr_total = 0
        self._ocr_success = 0
        self._last_plate = None
        self._last_conf = 0.0
        self._last_llm_emit = 0.0

        self.mqtt.set_callback(self.handle_vehicle_detection)

    # ============================================================
    # 🔥 Procesar detección enviada por Raspberry Pi 5
    # ============================================================
    def handle_vehicle_detection(self, msg):

        t_start = time.time()

        # FPS: intervalo entre ciclos consecutivos
        if self._last_cycle_ts:
            fps_val = round(1.0 / max(t_start - self._last_cycle_ts, 0.001), 1)
            _sio.emit("fps_update", {"fps": fps_val})
        self._last_cycle_ts = t_start

        print("\n🚘 JSON recibido desde Raspberry Pi 5")
        print(msg)

        detections = msg.get("detections", [])
        _sio.emit("detection", {
            "count": len(detections),
            "labels": [d["label"] for d in detections],
        })
        if not detections:
            print("[MAIN] No hay detecciones.")
            return

        veh = next((d for d in detections if d["label"] == "car"), None)
        if not veh:
            print("[MAIN] Ningún vehículo detectado.")
            return

        veh_bbox = veh["bbox"]

        # Cooldown OCR
        now = time.time()
        if now - self.last_ocr_time < OCR_INTERVAL_SEC:
            print("[OCR] Cooldown activo.")
            return
        self.last_ocr_time = now

        # Capturar imagen completa
        frame = self.camera.capture_frame()
        if frame is None:
            print("[CAM] No se pudo capturar frame.")
            return

        # Escalar bbox de la resolución Pi5 a la resolución local
        h_frame, w_frame = frame.shape[:2]
        scale_x = w_frame / PI5_FRAME_WIDTH
        scale_y = h_frame / PI5_FRAME_HEIGHT
        x1, y1, x2, y2 = veh_bbox
        veh_bbox = [
            max(0, int(x1 * scale_x)),
            max(0, int(y1 * scale_y)),
            min(w_frame, int(x2 * scale_x)),
            min(h_frame, int(y2 * scale_y)),
        ]
        print(f"▶ BBOX Pi5={veh['bbox']} → local={veh_bbox} (frame={w_frame}x{h_frame})")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_path = f"{RAW_DIR}/raw_{ts}.jpg"
        cv2.imwrite(raw_path, frame)
        cv2.imwrite("/tmp/adas_latest_frame.jpg", frame)  # frame compartido
        print(f"[LOG] RAW → {raw_path}")

        # ===============================
        #  DETECCIÓN DE PLACA (ONNX)
        # ===============================
        roi_plate, abs_bbox_plate = self.plates.refine_plate(frame, veh_bbox)

        # ------------------------------------------------------------
        # Caso A: NO SE ENCONTRÓ PLACA
        # ------------------------------------------------------------
        if roi_plate is None:
            print("[PLATE] No se encontró placa.")

            # Llamar a LLM SOLO con RAW + detecciones
            llm_desc = self.call_llm(raw_path, detections, None)

            update_dashboard(
                plate_text=None,
                plate_conf=None,
                raw_path=raw_path,
                roi_path=None,
                msg=msg,
                llm_description=llm_desc
            )

            self.logger.log(
                timestamp_local=datetime.now(),
                timestamp_mqtt=msg.get("timestamp"),
                veh_label=veh["label"],
                veh_conf=veh["confidence"],
                veh_bbox=str(veh_bbox),
                raw_path=raw_path,
                roi_path=None,
                plate_text=None,
                plate_conf=None,
                status="NO_PLATE"
            )
            return

        # ------------------------------------------------------------
        # Caso B: SÍ HAY PLACA
        # ------------------------------------------------------------
        roi_path = f"{ROI_DIR}/roi_{ts}.jpg"
        cv2.imwrite(roi_path, roi_plate)
        print(f"[LOG] ROI → {roi_path}")

        # Ejecutar OCR
        ocr_res = self.ocr.run_ocr(roi_path)
        print(f"[OCR] → {ocr_res}")

        plate_text = ocr_res.get("plate_text")
        plate_conf = ocr_res.get("confidence")

        self._ocr_total += 1
        if plate_text and (plate_conf or 0) > 0.5:
            self._ocr_success += 1
            self._last_plate = plate_text
            self._last_conf = plate_conf
        _sio.emit("ocr_rate", {"rate": round(self._ocr_success / self._ocr_total, 3)})

        _sio.emit("plate_detected", {
            "plate":      plate_text or "--",
            "confidence": round(plate_conf or 0, 3),
            "timestamp":  datetime.now().strftime("%H:%M:%S"),
            "image_url":  "/api/images/" + os.path.basename(roi_path),
        })
        latency_ms = round((time.time() - t_start) * 1000)
        _sio.emit("latency_update", {"latency": latency_ms})

        # LLM: descripción de la escena completa
        llm_desc = self.call_llm(raw_path, detections, plate_text)
        if llm_desc:
            print(f"[LLM] Descripción: {llm_desc}")
            _sio.emit("llm_result", {"text": llm_desc, "source": "llm"})
            self._last_llm_emit = time.time()
        elif time.time() - self._last_llm_emit > 5 and self._last_plate:
            # LLM caído — emitir último evento conocido como fallback
            _sio.emit("llm_result", {
                "text": (
                    f"Último evento registrado: placa {self._last_plate} "
                    f"detectada con {self._last_conf:.1%} de confianza. "
                    "Sistema LLM no disponible."
                ),
                "source": "fallback",
            })
            self._last_llm_emit = time.time()

        # Actualizar dashboard
        update_dashboard(
            plate_text=plate_text,
            plate_conf=plate_conf,
            raw_path=raw_path,
            roi_path=roi_path,
            msg=msg,
            llm_description=llm_desc
        )

        # Guardar en CSV
        self.logger.log(
            timestamp_local=datetime.now(),
            timestamp_mqtt=msg.get("timestamp"),
            veh_label=veh["label"],
            veh_conf=veh["confidence"],
            veh_bbox=str(veh_bbox),
            raw_path=raw_path,
            roi_path=roi_path,
            plate_text=plate_text,
            plate_conf=plate_conf,
            status="OK" if plate_text else "OCR_FAILED"
        )

        if plate_text:
            self.mqtt.client.publish(
                "adas/tts/speak",
                json.dumps({
                    "text": (
                        f"Placa detectada: {plate_text}. "
                        f"Confianza {int((plate_conf or 0) * 100)} por ciento."
                    ),
                    "priority": "normal",
                }),
            )

        print("→ Ciclo completado.")

    # ============================================================
    # 🧠 Llamar al servidor de visión LLM
    # ============================================================
    def call_llm(self, img_path, detections, plate_text):

        payload = {
            "image": img_path,
            "detections": detections,
            "plate_text": plate_text
        }

        try:
            r = requests.post(VISION_SERVER_URL, json=payload, timeout=10)

            if r.status_code != 200:
                print("[LLM] Error HTTP:", r.text)
                return None

            res = r.json()
            if not res.get("success"):
                print("[LLM] Error:", res.get("error"))
                return None

            return res.get("description")

        except Exception as e:
            print("[LLM] Excepción:", str(e))
            return None

    # ============================================================
    def run(self):
        print(f"[MQTT] Escuchando en topic '{MQTT_TOPIC}'")
        print(f"[CAM] Dispositivo: {CAMERA_DEVICE}")
        print(f"[LOG] CSV: {CSV_PATH}")
        print("🚀 ADAS Orchestrator corriendo...\n")
        self.mqtt.listen_forever()


if __name__ == "__main__":
    orchestrator = ADASOrchestrator()
    orchestrator.run()
