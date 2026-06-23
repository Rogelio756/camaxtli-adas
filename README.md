<div align="center">

# CAMA**X**TLI
### Edge AI · Advanced Driver Assistance System

*A distributed, edge-only ADAS for real-time vehicle detection and license plate recognition*

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Hailo](https://img.shields.io/badge/Hailo--8_NPU-Edge_AI-FF6B00?style=flat-square)
![YOLOv8](https://img.shields.io/badge/YOLOv8n-mAP₅₀_0.986-00B388?style=flat-square)
![Flask](https://img.shields.io/badge/Flask-SocketIO-000000?style=flat-square&logo=flask)
![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-660066?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![MCPR 2026](https://img.shields.io/badge/MCPR_2026-Springer_LNCS-7B2D8B?style=flat-square)

</div>

---

## 📑 Publications

> This system is the result of a research journey that began as an invitation.
> Dr. Juan Villegas-Cortez recognized the potential of this work while still in development
> and invited its presentation at NEO 2025. That early exposure shaped the final system,
> which was later accepted as a full paper at MCPR 2026, published under
> Springer Lecture Notes in Computer Science.

| Event | Date | Location | Publication | Work |
|---|---|---|---|---|
| **NEO 2025** · 12th Intl. Workshop on Numerical and Evolutionary Optimization | Sep 23–26, 2025 | Tijuana, B.C. · México | Book of Abstracts | Terminal Project · approved by Dept. of Electronics · UAM Azcapotzalco |
| **MUTVI UAM** · Institutional Poster Presentation | May 14, 2026 | UAM Azcapotzalco · CDMX | Academic Poster | MUTVI — formal institutional presentation |
| **MCPR 2026** · Mexican Conference on Pattern Recognition | Jun 26, 2026 | Cd. Juárez · México | **Springer LNCS · Session 9 · Paper #37** | CAMAXTLI ADAS — complete system |

---

## 🏗️ System Architecture · Three Physical Nodes

CAMAXTLI runs entirely on edge hardware — no cloud dependency, no external APIs.
Three physical nodes communicate over a local MQTT network.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CAMAXTLI · Edge Network                         │
│                     TP-Link TL-WR802N · 192.168.33.x               │
└──────────────┬──────────────────────┬──────────────────────────────┘
               │                      │                      │
               ▼                      ▼                      ▼
┌──────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│   NODE 1 · Pi5       │ │  NODE 2 · Copiloto  │ │   NODE 3 · Pi4      │
│   192.168.33.100     │ │  192.168.33.101      │ │   192.168.33.102    │
│                      │ │                      │ │                     │
│  RPi5 + Hailo-8 NPU  │ │  Dell G3 · Ubuntu   │ │  RPi4 + WM8960      │
│                      │ │  20.04               │ │  Audio HAT          │
│  · YOLOv8n HEF       │ │                      │ │                     │
│  · 30–58 FPS         │ │  · Flask + SocketIO  │ │  · Piper TTS        │
│  · MJPEG :8080       │ │  · LLaVA (Ollama)    │ │  · Voice alerts     │
│  · MQTT publisher    │ │  · EasyOCR / LPR     │ │  · MQTT subscriber  │
│                      │ │  · Celery + Redis    │ │  · Yodoit 15.6"     │
│                      │ │  · Mosquitto broker  │ │  · Anker 165W       │
└──────────────────────┘ └─────────────────────┘ └─────────────────────┘
```

---

## ⚡ Key Results · Paper Validated

| Metric | Value | Details |
|---|---|---|
| **mAP₅₀** | `0.986` | YOLOv8n · BDD100K dataset |
| **E2E Latency** | `230 ms` | Camera → TTS alert |
| **OCR Precision** | `93–96%` | VeRP dataset · 8,823 images |
| **Model Size Reduction** | `−88%` | 158 MB → 19 MB HEF (Hailo) |
| **Detection FPS** | `30–58 FPS` | RPi5 + Hailo-8 NPU |

---

## 🔄 Data Pipeline · End-to-End

```
📷 Camera (USB)
    │
    ▼
⚡ YOLOv8n · Hailo-8 NPU          ← Node 1 · Pi5
    │  Vehicle detection · BBox
    ▼
📡 MQTT Publish (JSON)             ← Network · Mosquitto broker
    │  topic: adas/detections
    ▼
🔍 License Plate ROI Crop          ← Node 2 · Copiloto Server
    │  PlateDetector · ONNX
    ▼
📖 OCR / LPR Pipeline              ← Celery async worker
    │  EasyOCR + PaddleOCR
    │  93–96% precision
    ▼
🧠 LLaVA Multimodal LLM            ← Ollama · scene analysis
    │  Scene description
    ▼
🔊 TTS Alert · Piper               ← Node 3 · Pi4 + WM8960
    │  Voice notification
    ▼
📊 CAMAXTLI Dashboard              ← Flask + SocketIO · :5000
    Splash → HUD → Data Explorer
```

---

## 🖥️ CAMAXTLI Dashboard · Three States

The frontend features three interactive states:

| State | Description |
|---|---|
| **◈ Splash Screen** | Boot screen · node initialization · MQTT heartbeat |
| **⬡ Dashboard HUD** | Live stream · pipeline monitor · LPR · LLM analysis |
| **⬢ Data Explorer** | CSV viewer · ROI image gallery · OCR confidence charts |

---

## 📁 Repository Structure

```
camaxtli-adas/
│
├── frontend/                    # CAMAXTLI UI · Three states
│   ├── splash/                  # Boot screen · node status via MQTT
│   │   ├── index.html
│   │   └── styles.css
│   └── dashboard/               # HUD · real-time + data explorer
│       ├── hud.html
│       ├── hud.css
│       └── ws.js                # Socket.IO client
│
├── backend/                     # Copiloto Server · Flask + OCR + LLM
│   ├── server/                  # Flask app · SocketIO · API routes
│   │   ├── dashboard_server.py  # Main Flask server · port 5000
│   │   ├── main_adas.py         # ADASOrchestrator
│   │   └── vision_server.py     # LLaVA server
│   ├── pipeline/                # OCR · LPR · Celery tasks
│   │   ├── tasks_lp.py
│   │   └── plate_pipeline/
│   └── managers/                # MQTT · camera · plate · data
│       ├── mqtt_manager.py
│       ├── camera_manager.py
│       ├── plate_detector.py
│       ├── ocr_client.py
│       └── data_logger.py
│
├── nodes/                       # Edge node scripts
│   ├── pi5/                     # YOLOv8n + Hailo · MQTT publisher
│   │   ├── detection_v2_json.py
│   │   └── setup_env.sh         # Hailo runtime setup
│   └── pi4/                     # Piper TTS · WM8960 audio
│       └── tts_listener.py
│
├── scripts/                     # System orchestration
│   ├── start_adas.sh            # Single-command boot · all nodes
│   └── setup.sh                 # Environment setup
│
├── docs/                        # Technical documentation
│   ├── Architecture.md
│   ├── Hardware.md
│   ├── Setup.md
│   └── API.md
│
├── .env.example                 # Environment template (no secrets)
├── requirements.txt             # Python dependencies
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Raspberry Pi 5 + Hailo-8 AI HAT+
- Raspberry Pi 4 + WM8960 Audio HAT
- Linux laptop / desktop (Ubuntu 20.04+)
- TP-Link TL-WR802N router (or any local network)
- Python 3.10+, Node.js 18+

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/camaxtli-adas.git
cd camaxtli-adas
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your network IPs and paths
nano .env
```

### 3. Install dependencies

```bash
# Python backend
pip install -r requirements.txt

# Hailo runtime (Pi5 only)
cd nodes/pi5 && source setup_env.sh
```

### 4. Launch the system

```bash
# Single command — boots all nodes in order
./scripts/start_adas.sh
```

The CAMAXTLI splash screen will appear while nodes initialize.
Dashboard opens automatically at `http://localhost:5000` when all nodes are ready.

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Network
LAPTOP_IP=192.168.33.101
PI5_IP=192.168.33.100
PI4_IP=192.168.33.103

# MQTT
MQTT_BROKER=192.168.33.101
MQTT_PORT=1883
MQTT_TOPIC=adas/detections

# Models
PLATE_MODEL_PATH=/path/to/your/best.pt
OCR_PYTHON=/path/to/venv_lp/bin/python3
OCR_DET_SINGLE=/path/to/det_ocr_single.py

# Pi5 Stream
PI5_STREAM_URL=http://192.168.33.100:8080/video_feed
PI5_FRAME_WIDTH=1280
PI5_FRAME_HEIGHT=720
```

---

## 🛠️ Hardware Bill of Materials

| Component | Model | Role |
|---|---|---|
| SBC · Detection | Raspberry Pi 5 (8GB) | Node 1 · YOLOv8n inference |
| AI Accelerator | Hailo-8 AI HAT+ | NPU · 26 TOPS |
| SBC · Audio | Raspberry Pi 4 (4GB) | Node 3 · TTS output |
| Audio HAT | WM8960 Audio HAT | Speaker + mic interface |
| Server | Dell G3 3590 · Ubuntu 20.04 | Node 2 · OCR + LLM + dashboard |
| Router | TP-Link TL-WR802N | Local edge network |
| Display | Yodoit 15.6" portable | HDMI output from Pi4 |
| Power | Anker 165W power bank | Pi nodes · portable power |
| Camera | USB camera (×1) | Vehicle detection feed |

---

## 📊 Datasets

| Dataset | Size | License | Use |
|---|---|---|---|
| **BDD100K** | 100K images | BSD | Vehicle detection training |
| **VeRP** (Vietnamese Vehicle Registration Plates) | 8,823 images | CC BY 4.0 | LPR / OCR training |

---

## 👨‍💻 About the Author

**Rogelio Leonardo Méndez Macías**
Electronics Engineering Student · Edge AI Researcher
Universidad Autónoma Metropolitana · Azcapotzalco · México

> *"Quiero que los hijos puedan ver a sus padres regresar a casa después de un largo día de trabajo."*
> — The motivation behind every line of code in this project.

CAMAXTLI is the result of my thesis project — a distributed ADAS built from the ground up
on three physical hardware nodes, with the conviction that technology should protect
the people we love. The name honors **Camaxtli**, the tutelary deity of Tlaxcala —
the land of my father — who guided, protected, and watched over his people.

**Research Advisors**

| Advisor | Department |
|---|---|
| Dr. Juan Villegas-Cortez | Systems Dept. · UAM Azcapotzalco |
| Dr. Andrés Ferreyra Ramírez | Electronics Dept. · UAM Azcapotzalco |
| M. en C. Arturo Zúñiga-López | UAM Azcapotzalco |
| Dr. Salomón Cordero-Sánchez | Depto. de Química · UAM Iztapalapa |

🏔 Tlaxcala &nbsp;·&nbsp; 🏙 Ciudad de México &nbsp;·&nbsp; 🎓 UAM Azcapotzalco &nbsp;·&nbsp; 🇲🇽 México

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**CAMAXTLI** &nbsp;·&nbsp; Tlaxcala · Ciudad de México &nbsp;·&nbsp; UAM Azcapotzalco
<br>
MCPR 2026 · Springer Lecture Notes in Computer Science · Paper #37

*Para que lleguen a casa.*

</div>
