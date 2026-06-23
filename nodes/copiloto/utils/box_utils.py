from typing import List, Tuple


def clip_box(bbox: List[float], img_w: int, img_h: int) -> Tuple[int, int, int, int]:
    """
    Ajusta una bbox [x1,y1,x2,y2] para que quede dentro de la imagen.
    Convierte a int y recorta en los bordes.
    """
    x1, y1, x2, y2 = bbox

    x1 = max(0, min(int(x1), img_w - 1))
    y1 = max(0, min(int(y1), img_h - 1))
    x2 = max(0, min(int(x2), img_w - 1))
    y2 = max(0, min(int(y2), img_h - 1))

    return x1, y1, x2, y2
