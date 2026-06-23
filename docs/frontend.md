# CAMAXTLI Frontend

Three-state web interface served by Flask.

## States
- `/splash` — Boot screen · node initialization via MQTT heartbeat
- `/dashboard` — Live HUD · real-time detections · LPR · LLM analysis  
- `/data` — Data Explorer · CSV viewer · ROI gallery · OCR charts

## Stack
- HTML5 + CSS3 + Vanilla JS
- Socket.IO client for real-time updates
- Fondo: #050d18 · Accent: #5ba3f5

## Files
- frontend/splash/ — index.html + styles.css
- frontend/dashboard/ — hud.html + hud.css + ws.js
- frontend/data_explorer/ — index.html + styles.css
