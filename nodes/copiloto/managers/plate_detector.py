# managers/plate_detector.py

import cv2
import numpy as np
from ultralytics import YOLO
from config.settings import PLATE_MODEL_PATH, PLATE_CONFIDENCE


class PlateDetector:
    """
    Detector de placas usando YOLO (formato .pt) sobre la ROI del vehículo.
    """

    def __init__(self):
        print(f"[PLATE] Cargando modelo YOLO de placas (PT): {PLATE_MODEL_PATH}")
        # Forzamos CPU para evitar problemas con CUDA
        self.model = YOLO(PLATE_MODEL_PATH)
        print("[PLATE] Modelo de placas cargado en CPU.")

    def refine_plate(self, frame, veh_bbox):
        """
        Recibe:
          - frame: imagen completa (BGR)
          - veh_bbox: [x1, y1, x2, y2] del vehículo (coordenadas absolutas)

        Devuelve:
          - roi_plate: recorte de la placa (BGR) o None
          - abs_bbox_plate: (x1, y1, x2, y2) en coordenadas del frame o None
        """
        if frame is None:
            print("[PLATE] Frame vacío.")
            return None, None

        h, w, _ = frame.shape

        try:
            x1, y1, x2, y2 = veh_bbox
        except Exception:
            print("[PLATE] BBOX de vehículo inválida:", veh_bbox)
            return None, None

        x1 = max(0, int(x1))
        y1 = max(0, int(y1))
        x2 = min(w, int(x2))
        y2 = min(h, int(y2))

        if x2 <= x1 or y2 <= y1:
            print("[PLATE] BBOX vehicular degenerada después de clamp.")
            return None, None

        vehicle_roi = frame[y1:y2, x1:x2].copy()
        if vehicle_roi.size == 0:
            print("[PLATE] ROI vehicular vacía.")
            return None, None

        print(f"[PLATE] frame={w}x{h}  veh_bbox_clamped=[{x1},{y1},{x2},{y2}]  vehicle_roi={vehicle_roi.shape[1]}x{vehicle_roi.shape[0]}")

        # Inferencia YOLO sobre el recorte del vehículo
        try:
            results = self.model.predict(
                vehicle_roi,
                conf=PLATE_CONFIDENCE,
                verbose=False,
                device="cpu"
            )
        except Exception as e:
            print("[PLATE] Error en inferencia YOLO:", e)
            return None, None

        if not results:
            print("[PLATE] Sin resultados YOLO.")
            return None, None

        r = results[0]
        if r.boxes is None or r.boxes.xyxy is None or len(r.boxes.xyxy) == 0:
            print("[PLATE] No se detectaron placas en la ROI vehicular.")
            return None, None

        # Elegimos la placa con mayor confianza
        confs = r.boxes.conf.cpu().numpy()
        best_idx = int(confs.argmax())
        best_box = r.boxes.xyxy[best_idx].cpu().numpy()  # [px1, py1, px2, py2]

        px1, py1, px2, py2 = best_box
        print(f"[PLATE] YOLO placa en ROI vehículo (raw): [{px1:.0f},{py1:.0f},{px2:.0f},{py2:.0f}]  conf={confs[best_idx]:.2f}")
        px1 = max(0, int(px1))
        py1 = max(0, int(py1))
        px2 = min(vehicle_roi.shape[1], int(px2))
        py2 = min(vehicle_roi.shape[0], int(py2))

        if px2 <= px1 or py2 <= py1:
            print("[PLATE] BBOX de placa degenerada en ROI.")
            return None, None

        # Convertir a coordenadas absolutas
        abs_x1 = x1 + px1
        abs_y1 = y1 + py1
        abs_x2 = x1 + px2
        abs_y2 = y1 + py2

        roi_plate = frame[abs_y1:abs_y2, abs_x1:abs_x2].copy()
        if roi_plate.size == 0:
            print("[PLATE] ROI de placa vacía tras recorte.")
            return None, None

        print(f"[PLATE] ROI placa final: abs=[{abs_x1},{abs_y1},{abs_x2},{abs_y2}]  tamaño={roi_plate.shape[1]}x{roi_plate.shape[0]}px")

        abs_bbox_plate = (abs_x1, abs_y1, abs_x2, abs_y2)
        return roi_plate, abs_bbox_plate

