# Pipeline OCR · LPR

Procesamiento asíncrono de placas via Celery + Redis.

## Flujo
1. MQTT recibe detección del Pi5
2. `main_adas.py` recorta ROI del vehículo
3. `plate_detector.py` detecta placa en ROI (ONNX)
4. `ocr_client.py` ejecuta EasyOCR/PaddleOCR
5. Resultado emitido via SocketIO al dashboard
6. `data_logger.py` guarda en CSV + imagen ROI

## Precisión
- Confianza promedio: 96.5%
- Dataset: VeRP (8,823 imágenes)
