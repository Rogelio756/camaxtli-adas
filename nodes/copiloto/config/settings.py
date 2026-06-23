# ===============================
# CONFIGURACIÓN DEL SISTEMA ADAS
# ===============================

from pathlib import Path
from dotenv import load_dotenv
import os

ENV_PATH = Path("/mnt/bigdata/ADAS/adas.env")
load_dotenv(dotenv_path=ENV_PATH)

# =======================
#  Red
# =======================
LAPTOP_IP        = os.getenv("LAPTOP_IP", "127.0.0.1")
PI5_IP           = os.getenv("PI5_IP", "192.168.33.100")
PI4_IP           = os.getenv("PI4_IP", "192.168.33.103")

# =======================
#  MQTT
# =======================
MQTT_BROKER      = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT        = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC       = os.getenv("MQTT_TOPIC", "perception/vehicles/detections")

# =======================
#  Streams y puertos
# =======================
PI5_STREAM_PORT  = int(os.getenv("PI5_STREAM_PORT", "8080"))
DASHBOARD_PORT   = int(os.getenv("DASHBOARD_PORT", "5000"))

# =======================
#  CÁMARA
# =======================
CAMERA_DEVICE    = os.getenv("CAMERA_DEVICE", "/dev/video0")
FRAME_WIDTH      = 1280
FRAME_HEIGHT     = 720
FPS              = 30

# Resolución nativa de la cámara de la Pi5 (origen de los bbox MQTT)
PI5_FRAME_WIDTH  = 1280
PI5_FRAME_HEIGHT = 720

# =======================
#  MODELO YOLO PLACAS
# =======================
PLATE_MODEL_PATH = os.getenv("PLATE_MODEL_PATH", "/home/rogelio/runs/detect/placas_yolov8n2/weights/best.pt")
PLATE_CONFIDENCE = 0.60

# =======================
#  OCR COOL DOWN
# =======================
OCR_INTERVAL_SEC = 3  # segundos entre ejecuciones OCR

# =======================
#  PATHS DEL PROYECTO
# =======================
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR   = PROJECT_ROOT / "data"
PLATES_DIR = DATA_DIR / "plates"
RAW_DIR    = PLATES_DIR / "raw"
ROI_DIR    = PLATES_DIR / "roi"
CSV_PATH   = PLATES_DIR / "plates_log.csv"
LOGS_DIR   = PROJECT_ROOT / "logs"

for d in [DATA_DIR, PLATES_DIR, RAW_DIR, ROI_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# =======================
#  OCR EXTERNAL WORKER
# =======================
OCR_PYTHON    = os.getenv("OCR_PYTHON", "/home/rogelio/venv_lp/bin/python3")
OCR_DET_SINGLE = os.getenv("OCR_DET_SINGLE", "/home/rogelio/venv_lp/det_ocr_single.py")
OCR_WORKER    = PROJECT_ROOT / "utils" / "ocr_worker.py"
