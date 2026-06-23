from typing import List, Dict, Any, Optional


class VehicleSelector:
    """
    Aísla la lógica para elegir qué vehículo usar del JSON.
    Ahora mismo: el de mayor confianza entre car/truck/bus.
    """

    VEHICLE_LABELS = ("car", "truck", "bus")

    def select(self, detections: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not detections:
            # print("[SEL] Sin detecciones en el mensaje.")
            return None

        vehicles = [
            d for d in detections if d.get("label") in self.VEHICLE_LABELS
        ]
        if not vehicles:
            # print("[SEL] No hay vehículos entre las detecciones.")
            return None

        best = max(vehicles, key=lambda d: d.get("confidence", 0.0))
        # print(f"[SEL] Vehículo seleccionado: {best}")
        return best
