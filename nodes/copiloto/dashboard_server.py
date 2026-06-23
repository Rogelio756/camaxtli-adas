# ======================================================
#   ADAS COPILOTO — DASHBOARD SERVER (API REST)
#   Arquitectura Profesional
#   Autor: Rogelio + ChatGPT (Senior Embedded AI)
# ======================================================

import os
import csv
import json
from datetime import datetime
from flask import Flask, jsonify, send_file, send_from_directory, request
from flask_socketio import SocketIO
import requests
from config.settings import DATA_DIR, PROJECT_ROOT, CSV_PATH as PLATES_CSV_PATH

# ======================================================
#   CONFIG
# ======================================================

CSV_PATH        = PLATES_CSV_PATH
LLM_REPORTS_CSV = DATA_DIR / "llm_reports.csv"
DASHBOARD_STATE = PROJECT_ROOT / "dashboard_state.json"
ROI_PATH        = DATA_DIR / "plates" / "roi"

FRONTEND_PATH = '/mnt/bigdata/ADAS/camaxtli-adas/frontend'

VISION_SERVER_URL = "http://localhost:8001/describe"

app = Flask(__name__, static_url_path="/static")
socketio = SocketIO(app, cors_allowed_origins="*", message_queue="redis://")


# ======================================================
#   HELPERS
# ======================================================

def read_last_rows(n=20):
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, "r") as f:
        reader = list(csv.reader(f))
    return reader[-n:] if reader else []


def parse_row(row):
    d = {
        "timestamp_local": None,
        "timestamp_mqtt": None,
        "veh_label": None,
        "veh_conf": None,
        "veh_bbox": None,
        "raw_path": None,
        "roi_path": None,
        "plate_text": None,
        "plate_conf": None,
        "status": None,
    }
    try:
        d["timestamp_local"] = row[0]
        d["timestamp_mqtt"] = row[1]
        d["veh_label"] = row[2]
        d["veh_conf"] = float(row[3]) if row[3] else None
        d["veh_bbox"] = row[4]
        d["raw_path"] = row[5]
        d["roi_path"] = row[6]
        d["plate_text"] = row[7]
        d["plate_conf"] = float(row[8]) if row[8] else None
        d["status"] = row[9] if len(row) > 9 else None
    except:
        pass
    return d


def get_last_detection():
    rows = read_last_rows(1)
    if not rows:
        return None
    return parse_row(rows[0])


def save_llm_report(timestamp, plate, raw_path, description):
    """Guarda reporte LLM en CSV."""
    is_new = not os.path.exists(LLM_REPORTS_CSV)

    with open(LLM_REPORTS_CSV, "a", newline="") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["timestamp", "plate", "raw_path", "description"])
        w.writerow([timestamp, plate, raw_path, description])


def read_state():
    if not os.path.exists(DASHBOARD_STATE):
        return {}
    try:
        with open(DASHBOARD_STATE, "r") as f:
            return json.load(f)
    except:
        return {}


def write_state(state):
    with open(DASHBOARD_STATE, "w") as f:
        json.dump(state, f, indent=4)


# ======================================================
#   TTS — Enviar texto a la PI4 vía MQTT
# ======================================================

def send_tts(text):
    """Envía texto a la Raspberry Pi 4 vía MQTT para síntesis de voz."""
    import json
    import paho.mqtt.client as mqtt

    from config.settings import PI4_IP
    MQTT_BROKER = PI4_IP
    MQTT_TOPIC  = "adas/tts/speak"

    try:
        client = mqtt.Client()
        client.connect(MQTT_BROKER, 1883, 60)

        payload = json.dumps({"text": text})
        client.publish(MQTT_TOPIC, payload)

        print(f"[SERVER] TTS enviado: {text}")
        client.disconnect()

    except Exception as e:
        print(f"[SERVER] Error enviando TTS: {e}")


# ======================================================
#   API ROUTES
# ======================================================

@app.route("/")
def root_page():
    from flask import render_template
    return render_template("dashboard.html")


# ── Frontend CAMAXTLI ──

@app.route('/splash')
def splash():
    return send_from_directory(f'{FRONTEND_PATH}/splash', 'index.html')


@app.route('/dashboard')
def dashboard():
    return send_from_directory(f'{FRONTEND_PATH}/dashboard', 'hud.html')


@app.route('/data')
def data_explorer():
    return send_from_directory(f'{FRONTEND_PATH}/data_explorer', 'index.html')


@app.route('/frontend/<path:subpath>')
def frontend_static(subpath):
    return send_from_directory(FRONTEND_PATH, subpath)


@app.route('/splash/<path:filename>')
def splash_static(filename):
    return send_from_directory(f'{FRONTEND_PATH}/splash', filename)


@app.route('/dashboard/<path:filename>')
def dashboard_static(filename):
    return send_from_directory(f'{FRONTEND_PATH}/dashboard', filename)


@app.route('/data/<path:filename>')
def data_static(filename):
    return send_from_directory(f'{FRONTEND_PATH}/data_explorer', filename)


@app.route("/api/last")
def api_last():
    rows = read_last_rows(1)
    if not rows:
        return jsonify({"success": False, "error": "No detecciones"})
    return jsonify({"success": True, "data": parse_row(rows[0])})


@app.route("/api/history")
def api_history():
    limit = int(request.args.get("limit", 20))
    rows = read_last_rows(limit)
    parsed = [parse_row(r) for r in rows]
    parsed.reverse()
    return jsonify({"success": True, "data": parsed})


@app.route("/api/raw")
def api_raw():
    last = read_last_rows(1)
    if not last:
        return jsonify({"error": "no raw"}), 404
    row = parse_row(last[0])
    if not row["raw_path"] or not os.path.exists(row["raw_path"]):
        return jsonify({"error": "raw missing"}), 404
    return send_file(row["raw_path"], mimetype="image/jpeg")


@app.route("/api/roi")
def api_roi():
    last = read_last_rows(1)
    if not last:
        return jsonify({"error": "no roi"}), 404
    row = parse_row(last[0])
    if not row["roi_path"] or not os.path.exists(row["roi_path"]):
        return jsonify({"error": "roi missing"}), 404
    return send_file(row["roi_path"], mimetype="image/jpeg")

#--------------------------------------------------------------
@app.route("/api/metrics")
def api_metrics():
    history = read_last_rows(200)
    parsed = [parse_row(r) for r in history]

    # OCR Stats
    ocr_ok = sum(1 for p in parsed if p["plate_text"] and p["status"] == "OK")
    ocr_total = len(parsed)
    ocr_rate = (ocr_ok / ocr_total * 100) if ocr_total else 0
    last_ok = next((p["plate_text"] for p in reversed(parsed) if p["status"] == "OK"), "—")

    # FPS calculation by timestamps
    timestamps = []
    for p in parsed:
        try:
            timestamps.append(datetime.fromisoformat(p["timestamp_local"].replace(" ", "T")))
        except:
            pass

    fps = 0
    if len(timestamps) > 1:
        delta = (timestamps[-1] - timestamps[0]).total_seconds()
        fps = len(timestamps) / delta if delta > 0 else 0

    # Averages for pipeline times
    def avg(key):
        vals = [p.get(key, 0) for p in parsed if p.get(key) is not None]
        return round(sum(vals)/len(vals), 3) if vals else 0

    times = {
        "yolo": avg("t_yolo"),
        "crop": avg("t_crop"),
        "ocr": avg("t_ocr"),
        "llm": avg("t_llm"),
        "total": avg("t_total")
    }

    return jsonify({
        "success": True,
        "ocr_ok": ocr_ok,
        "ocr_total": ocr_total,
        "ocr_rate": round(ocr_rate, 2),
        "last_plate_ok": last_ok,
        "fps": round(fps, 2),
        "times": times
    })



@app.route("/api/heatmap")
def api_heatmap():
    rows = read_last_rows(500)
    parsed = [parse_row(r) for r in rows]

    heat = {}
    for p in parsed:
        ts = p.get("timestamp_local")
        if not ts:
            continue

        hour = ts.split("T")[-1][:2] if "T" in ts else ts.split(" ")[-1][:2]
        heat[hour] = heat.get(hour, 0) + 1

    return jsonify({"success": True, "data": heat})


@app.route("/api/llm/run", methods=["POST"])
def api_llm_run():
    data = request.json
    model = data.get("model", "llava")
    preset = data.get("preset", "short")

    state = read_state()
    raw_path = state.get("raw_path")
    if not raw_path:
        return jsonify({"success": False, "error": "no raw"}), 400

    try:
        r = requests.post(VISION_SERVER_URL, json={
            "model": model,
            "preset": preset,
            "image": raw_path,
            "plate_text": state.get("plate_text", "")
        })
        res = r.json()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    desc = res.get("description", "—")
    state["llm_description"] = desc
    write_state(state)

    save_llm_report(
        timestamp=datetime.now().isoformat(),
        plate=state.get("plate_text", "—"),
        raw_path=raw_path,
        description=desc
    )

    return jsonify({"success": True, "description": desc})


@app.route("/api/llm/save", methods=["POST"])
def api_llm_save():
    state = read_state()
    text = state.get("llm_description", "")
    raw_path = state.get("raw_path", "")

    folder = DATA_DIR / "llm_full_reports"
    os.makedirs(folder, exist_ok=True)

    out_path = os.path.join(folder, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    with open(out_path, "w") as f:
        f.write(f"# Reporte LLM\n")
        f.write(f"**Timestamp:** {datetime.now().isoformat()}\n\n")
        f.write(f"**RAW:** {raw_path}\n\n")
        f.write(text)

    return jsonify({"success": True, "path": out_path})


# ======================================================
#   AUDIO — API ENDPOINTS TTS
# ======================================================

@app.route("/api/audio/read_report", methods=["POST"])
def api_audio_read():
    state = read_state()
    text = state.get("llm_description")

    if not text:
        return jsonify({"success": False, "error": "No hay descripción generada"}), 400

    send_tts(text)
    return jsonify({"success": True, "message": "Reporte enviado a la Pi4"})


@app.route("/api/audio/read_plate", methods=["POST"])
def api_audio_plate():
    last = get_last_detection()

    if not last or not last.get("plate_text"):
        send_tts("No se detectó ninguna placa.")
        return jsonify({"success": True, "message": "Placa no detectada"})

    plate = last["plate_text"]
    text = f"La placa detectada es {plate}"
    send_tts(text)

    return jsonify({"success": True, "message": text})


@app.route("/api/audio/read_status", methods=["POST"])
def api_audio_status():
    state = read_state()
    
    ocr_rate = state.get("ocr_rate")
    last_plate = state.get("plate_text")

    ocr_text = (
        f"La tasa de reconocimiento es {ocr_rate:.1f} por ciento. "
        if ocr_rate is not None else
        "No hay datos recientes del OCR. "
    )

    plate_text = (
        f"La última placa detectada fue {last_plate}."
        if last_plate else
        "No se ha detectado ninguna placa recientemente."
    )

    final_text = f"Estado del sistema ADAS: {ocr_text}{plate_text}"

    send_tts(final_text)
    return jsonify({"success": True, "message": final_text})


@app.route("/api/stats")
def api_stats():
    rows   = read_last_rows(10000)
    parsed = [parse_row(r) for r in rows]
    confs  = [p["plate_conf"] for p in parsed if p["plate_conf"] is not None]
    roi_count = sum(1 for p in parsed if p.get("roi_path"))
    dates  = {(p.get("timestamp_local") or "")[:10] for p in parsed if p.get("timestamp_local")}
    return jsonify({
        "total_plates":   len(parsed),
        "avg_conf":       round(sum(confs) / len(confs), 4) if confs else 0,
        "total_images":   roi_count,
        "total_sessions": len(dates),
    })


@app.route("/api/plates")
def api_plates():
    page  = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    rows  = read_last_rows(10000)
    parsed = [parse_row(r) for r in rows]
    parsed.reverse()
    start = (page - 1) * limit
    page_data = parsed[start : start + limit]
    return jsonify([{
        "plate":      p.get("plate_text"),
        "confidence": p.get("plate_conf"),
        "timestamp":  p.get("timestamp_local"),
        "session":    (p.get("timestamp_local") or "")[:10],
        "image":      "/api/roi" if p.get("roi_path") else None,
    } for p in page_data])


@app.route("/api/sessions")
def api_sessions():
    rows   = read_last_rows(10000)
    parsed = [parse_row(r) for r in rows]

    # Sort ascending by timestamp
    def ts_key(p):
        return p.get("timestamp_local") or ""

    parsed.sort(key=ts_key)

    # Group into sessions: gap > 30 min → new session
    GAP_SECONDS = 30 * 60
    sessions = []
    current  = []

    for p in parsed:
        raw_ts = p.get("timestamp_local")
        if not raw_ts:
            continue
        try:
            t = datetime.fromisoformat(raw_ts.replace(" ", "T").split(".")[0])
        except Exception:
            continue

        if current:
            prev_t = current[-1]["_dt"]
            if (t - prev_t).total_seconds() > GAP_SECONDS:
                sessions.append(current)
                current = []
        p["_dt"] = t
        current.append(p)

    if current:
        sessions.append(current)

    result = []
    for i, grp in enumerate(sessions, start=1):
        confs = [r["plate_conf"] for r in grp if r.get("plate_conf") is not None]
        result.append({
            "session":  f"S{i}",
            "date":     grp[0]["_dt"].strftime("%Y-%m-%d"),
            "avg_conf": round(sum(confs) / len(confs), 4) if confs else 0,
            "total":    len(grp),
        })

    return jsonify(result)


@app.route("/api/images")
def api_images():
    page  = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 16))

    # Build lookup: basename(roi_path) → {plate_text, plate_conf, timestamp_local}
    rows   = read_last_rows(10000)
    parsed = [parse_row(r) for r in rows]
    lookup = {}
    for p in parsed:
        rp = p.get("roi_path")
        if rp:
            lookup[os.path.basename(rp)] = p

    if not ROI_PATH.exists():
        return jsonify([])

    files = sorted(ROI_PATH.iterdir(), reverse=True)
    jpg_files = [f for f in files if f.suffix.lower() in (".jpg", ".jpeg", ".png")]

    start     = (page - 1) * limit
    page_files = jpg_files[start : start + limit]

    result = []
    for f in page_files:
        meta = lookup.get(f.name, {})
        ts   = meta.get("timestamp_local") or ""
        result.append({
            "filename":  f.name,
            "url":       f"/api/images/{f.name}",
            "plate":     meta.get("plate_text") or "",
            "conf":      meta.get("plate_conf") or 0,
            "timestamp": ts[11:19] if len(ts) > 18 else ts,
        })

    return jsonify(result)


@app.route("/api/images/<path:filename>")
def api_images_file(filename):
    return send_from_directory(str(ROI_PATH), filename)


# ======================================================
#   MAIN
# ======================================================

if __name__ == "__main__":
    print("🚀 API Dashboard corriendo en http://localhost:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
