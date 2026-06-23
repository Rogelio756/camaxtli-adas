# Managers · Abstracción de componentes

| Manager | Responsabilidad |
|---|---|
| `mqtt_manager.py` | Conexión y publicación MQTT |
| `camera_manager.py` | Frame capture y preprocessing |
| `plate_detector.py` | Detección de placa en ROI (YOLO ONNX) |
| `ocr_client.py` | Cliente OCR · EasyOCR + PaddleOCR |
| `data_logger.py` | CSV + imágenes ROI |
| `vehicle_selector.py` | Selección del vehículo más relevante |
