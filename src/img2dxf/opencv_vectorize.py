from __future__ import annotations

from .vectorize import Polyline


def trace_mask_opencv(mask: list[list[bool]], *, simplify: float = 0.75) -> list[Polyline]:
    """Trace black-pixel regions with OpenCV contours."""
    try:
        import cv2
        import numpy as np
    except ImportError as error:
        raise ValueError(
            "OpenCV backend requires opencv-python-headless. "
            'Install it with: python3 -m pip install -e ".[opencv]"'
        ) from error

    image = np.array(mask, dtype=np.uint8) * 255
    contours, _ = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    paths: list[Polyline] = []

    for contour in contours:
        if len(contour) < 3:
            continue
        epsilon = max(0.0, float(simplify))
        approx = cv2.approxPolyDP(contour, epsilon, True) if epsilon else contour
        path = [(int(point[0][0]), int(point[0][1])) for point in approx]
        if len(path) >= 3:
            paths.append(path)

    return paths
