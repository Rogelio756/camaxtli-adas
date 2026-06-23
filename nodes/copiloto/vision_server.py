import os
import base64
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_PROMPT = (
    "Describe brevemente el vehículo y la placa visible. "
    "Máximo 2 oraciones en español."
)


def describe_image(image_path: str, prompt: str = None) -> str:
    if prompt is None:
        prompt = DEFAULT_PROMPT
    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "llava",
                "prompt": prompt,
                "images": [img_b64],
                "stream": False,
            },
            timeout=60,
        )
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        print(f"[LLM] HTTP {response.status_code}: {response.text[:200]}")
        return ""
    except Exception as e:
        print(f"[LLM] Error: {e}")
        return ""


@app.route("/describe", methods=["POST"])
def describe():
    data = request.get_json()
    img_path = data.get("image")
    plate    = data.get("plate_text")

    if not img_path or not os.path.exists(img_path):
        return jsonify({"success": False, "error": "Imagen no encontrada"})

    print("[VISION] Procesando:", img_path)

    prompt = DEFAULT_PROMPT
    if plate:
        prompt = (
            f"La placa detectada es '{plate}'. "
            "Describe brevemente el vehículo y confirma si la placa es legible. "
            "Máximo 2 oraciones en español."
        )

    description = describe_image(img_path, prompt)

    return jsonify({
        "success": bool(description),
        "description": description,
    })


if __name__ == "__main__":
    print("🚀 Vision Server en http://localhost:8001/describe")
    app.run(host="0.0.0.0", port=8001)
