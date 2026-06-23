import subprocess
import json
from config.settings import OCR_PYTHON, OCR_WORKER


class OCRClient:
    def run_ocr(self, roi_path):
        try:
            cmd = [
                OCR_PYTHON,
                OCR_WORKER,
                roi_path
            ]
            cmd = list(map(str, cmd))


            # FIX: asegurar que todo sea str (Path -> str) antes de join/subprocess
            cmd = list(map(str, cmd))

            print(f"[OCR] Ejecutando worker: {' '.join(cmd)}")

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=25
            )

            if proc.returncode != 0:
                print("[OCR] Worker retornó error:")
                print(proc.stderr)
                return {"plate_text": None, "confidence": None}

            raw_output = proc.stdout.strip()
            if not raw_output:
                print("[OCR] Salida vacía del worker")
                return {"plate_text": None, "confidence": None}

            # ----------------------------------------
            # 🔥 FIX: Tomar SOLO la última línea JSON
            # ----------------------------------------
            lines = raw_output.split("\n")
            last_line = lines[-1].strip()

            if not last_line.startswith("{"):
                print("[OCR] No se encontró JSON válido en la salida")
                print("Salida completa:", raw_output)
                return {"plate_text": None, "confidence": None}

            return json.loads(last_line)

        except subprocess.TimeoutExpired:
            print("[OCR] Timeout: el worker tardó más de 25s")
            return {"plate_text": None, "confidence": None}

        except Exception as e:
            print("[OCR] Excepción inesperada:", e)
            return {"plate_text": None, "confidence": None}
