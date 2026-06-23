# managers/camera_manager.py

import cv2
from config.settings import CAMERA_DEVICE, FRAME_WIDTH, FRAME_HEIGHT, FPS


class CameraManager:
    """
    Manejo robusto de webcam para ADAS (resuelve frames negros, resoluciones inválidas,
    warm-up necesario en V4L2 y errores de apertura).
    """

    def __init__(self, device=CAMERA_DEVICE):
        self.device = device
        print(f"[CAM] Inicializando cámara en {self.device}")

        # ---- 1. Abrir cámara con V4L2 ----
        self.cap = cv2.VideoCapture(self.device, cv2.CAP_V4L2)

        # ---- 2. Forzar MJPEG antes de cualquier configuración ----
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

        # ---- 3. Establecer la resolución correcta ----
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

        # ---- 4. Ajustar FPS soportado por la cámara ----
        self.cap.set(cv2.CAP_PROP_FPS, FPS)

        # ---- 5. Warm-up obligatorio para cámaras USB ----
        for i in range(8):
            self.cap.read()

        # ---- 6. Validar apertura ----
        if not self.cap.isOpened():
            raise RuntimeError(f"[CAM] No se pudo abrir la cámara: {self.device}")

        # ---- 7. Validar primer frame real ----
        ok, frame = self.cap.read()
        if not ok or frame is None:
            raise RuntimeError(
                f"[CAM] Cámara abrió pero no entrega frames válidos. "
                f"Verifica formato/resolución: {self.device}"
            )

        print(f"[CAM] Cámara lista. Frame inicial: {frame.shape}")

    def capture_frame(self):
        ok, frame = self.cap.read()
        if not ok or frame is None:
            print("[CAM] Error capturando frame.")
            return None
        return frame

    def release(self):
        if self.cap is not None:
            self.cap.release()
            print("[CAM] Cámara liberada.")
