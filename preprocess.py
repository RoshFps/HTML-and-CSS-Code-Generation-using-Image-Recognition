"""Image preprocessing applied before running the element detector."""

from pathlib import Path

import cv2
import numpy as np

from config import IMAGE_SIZE


def preprocessing(path_to_image, out_dir) -> str:
    """Resize, dilate and edge-detect a sketch. Returns the path of the processed image."""
    img = cv2.imread(str(path_to_image))
    if img is None:
        raise ValueError(f"Could not read image: {path_to_image}")

    img = cv2.resize(img, IMAGE_SIZE)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    dilated = cv2.dilate(gray, np.ones((2, 2), np.uint8), iterations=1)
    edges = cv2.Canny(dilated, 100, 101)

    out_path = Path(out_dir) / "edges.png"
    cv2.imwrite(str(out_path), edges)
    return str(out_path)
