#!/usr/bin/env python3
import sys
import json
import cv2
from paddleocr import PaddleOCR

# ============================================================
#  1) CONFIGURACIÓN DE PADDLEOCR (solo modelos en inglés)
# ============================================================
ocr = PaddleOCR(
    lang='en',
    det=True,
    rec=True,
    use_angle_cls=True,
    show_log=False  # 🔥 importante: evitar spam de logs
)

# ============================================================
#  2) VALIDACIÓN DE ARGUMENTOS
# ============================================================
if len(sys.argv) < 2:
    print(json.dumps({"plate_text": None, "confidence": None}))
    sys.exit(0)

roi_path = sys.argv[1]

# ============================================================
#  3) CARGAR IMAGEN
# ============================================================
img = cv2.imread(roi_path)

if img is None:
    # ROI inválida
    print(json.dumps({"plate_text": None, "confidence": None}))
    sys.exit(0)

# ============================================================
#  4) PREPROCESADO (mejora OCR)
# ============================================================
# Convertimos a gris
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Aumentamos contraste
gray = cv2.equalizeHist(gray)

# ============================================================
#  5) EJECUTAR OCR
# ============================================================
try:
    result = ocr.ocr(gray, cls=True)
except Exception as e:
    print(json.dumps({"plate_text": None, "confidence": None}))
    sys.exit(0)

if not result or not result[0]:
    print(json.dumps({"plate_text": None, "confidence": None}))
    sys.exit(0)

# ============================================================
#  6) PROCESAR RESULTADOS
# ============================================================
best_text = None
best_conf = 0.0

for line in result[0]:
    text = line[1][0]
    conf = float(line[1][1])

    # Filtrar basura: texto muy largo o muy corto
    if len(text) < 4 or len(text) > 10:
        continue

    # Guardar el mejor candidato
    if conf > best_conf:
        best_text = text
        best_conf = conf

# ============================================================
#  7) SALIDA JSON
# ============================================================
if best_text is None:
    print(json.dumps({"plate_text": None, "confidence": None}))
else:
    print(json.dumps({
        "plate_text": best_text,
        "confidence": best_conf
    }))
