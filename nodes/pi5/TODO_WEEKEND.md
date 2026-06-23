# Node 1 · Pi5 — Pendiente para el fin de semana

**Estado:** Código en el hardware físico (RPi5 @ 192.168.33.100)
**Rama:** `feat/node-pi5`

---

## Qué hacer cuando llegues

### 1. Copiar el código desde la Pi5

```bash
# Desde tu laptop / copiloto server:
scp rogelio@192.168.33.100:~/detection_v2_json.py nodes/pi5/
scp rogelio@192.168.33.100:~/requirements_pi5.txt nodes/pi5/requirements.txt

# Si tienes más scripts en la Pi5:
scp -r rogelio@192.168.33.100:~/hailo/ nodes/pi5/hailo/
```

### 2. Archivos que deben quedar en esta rama

```
nodes/pi5/
├── detection_v2_json.py      ← entry point principal (30-58 FPS)
├── requirements.txt          ← paho-mqtt, hailo-runtime, etc.
├── hailo/                    ← HEF model + runtime scripts (opcional)
└── TODO_WEEKEND.md           ← este archivo (borrar cuando esté completo)
```

### 3. Commit y push

```bash
git add nodes/pi5/
git commit -m "feat: Node 1 Pi5 detection script + Hailo HEF pipeline"
git push origin feat/node-pi5
```

---

## Contexto técnico

| Parámetro | Valor |
|---|---|
| Hardware | RPi5 8GB + Hailo-8 AI HAT+ (26 TOPS) |
| Modelo | YOLOv8n → compilado a `.hef` (19MB, -88% tamaño) |
| Dataset | BDD100K vehicle detection |
| FPS | 30–58 FPS en tiempo real |
| mAP50 | 0.986 |
| MQTT topic | `perception/vehicles/detections` |
| IP | 192.168.33.100 |

## Stack en la Pi5

- Hailo Runtime + TAPPAS
- Python 3.11
- paho-mqtt
- OpenCV (preview opcional)
