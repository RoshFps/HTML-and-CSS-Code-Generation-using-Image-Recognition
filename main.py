"""Detects hand-drawn UI elements with a Faster R-CNN model and writes HTML.

Requires TensorFlow 1.15 (or TF 2.x in compat mode) and the TensorFlow Object
Detection API. Paths are configured in ``config.py`` / ``.env``.
"""

import sys
from itertools import groupby
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

import config

if config.TF_MODELS_RESEARCH_DIR:
    sys.path.append(config.TF_MODELS_RESEARCH_DIR)

import tensorflow.compat.v1 as tf  # noqa: E402
from object_detection.utils import label_map_util  # noqa: E402

# This repository ships a modified visualization_utils.py that adds return_coordinates().
import visualization_utils as vis_util  # noqa: E402
from script_gen import BREAK, generate_html  # noqa: E402

tf.disable_v2_behavior()

# Elements whose centres are within this many pixels vertically share a row.
ROW_TOLERANCE_PX = 30

_graph = None
_category_index = None


def _load_model():
    """Load the frozen graph and label map once, on first use."""
    global _graph, _category_index
    if _graph is not None:
        return _graph, _category_index
    if not config.MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Model not found at {config.MODEL_PATH}. Download frozen_inference_graph_816.pb "
            "and set MODEL_PATH (see README)."
        )
    graph = tf.Graph()
    with graph.as_default():
        graph_def = tf.GraphDef()
        with tf.gfile.GFile(str(config.MODEL_PATH), "rb") as fid:
            graph_def.ParseFromString(fid.read())
        tf.import_graph_def(graph_def, name="")
    _graph = graph
    _category_index = label_map_util.create_category_index_from_labelmap(
        str(config.LABELS_PATH), use_display_name=True
    )
    return _graph, _category_index


def run_inference_for_single_image(image: np.ndarray, graph) -> dict:
    with graph.as_default(), tf.Session() as sess:
        names = {out.name for op in graph.get_operations() for out in op.outputs}
        tensors = {
            key: graph.get_tensor_by_name(key + ":0")
            for key in ("num_detections", "detection_boxes", "detection_scores", "detection_classes")
            if key + ":0" in names
        }
        image_tensor = graph.get_tensor_by_name("image_tensor:0")
        out = sess.run(tensors, feed_dict={image_tensor: image})

    out["num_detections"] = int(out["num_detections"][0])
    out["detection_classes"] = out["detection_classes"][0].astype(np.int64)
    out["detection_boxes"] = out["detection_boxes"][0]
    out["detection_scores"] = out["detection_scores"][0]
    return out


def group_into_rows(elements: List[Tuple[str, int, int]]) -> List[List[Tuple[str, int, int]]]:
    """Group ``(name, x, y)`` centres into rows (top to bottom), each sorted left to right."""
    if not elements:
        return []
    elements = sorted(elements, key=lambda e: e[2])
    row_ids, row, prev_y = [], 0, elements[0][2]
    for _, _, y in elements:
        if y - prev_y > ROW_TOLERANCE_PX:
            row += 1
        row_ids.append(row)
        prev_y = y
    rows = []
    for _, group in groupby(zip(row_ids, elements), key=lambda p: p[0]):
        rows.append(sorted((e for _, e in group), key=lambda e: e[1]))
    return rows


def write_elements(rows, path: Path) -> Path:
    lines = []
    for i, row in enumerate(rows):
        if i:
            lines.append(BREAK)
        lines += [f"{name},{x},{y}" for name, x, y in row]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def processImage(image_path, out_dir) -> Tuple[Path, Optional[Path]]:
    """Run detection on a preprocessed image.

    Writes ``detections.jpg`` (boxes drawn on the sketch) and, if anything was
    found, ``generated.html`` into ``out_dir``. Returns both paths; the HTML
    path is ``None`` when no elements were detected.
    """
    out_dir = Path(out_dir)
    graph, category_index = _load_model()

    image = Image.open(image_path).convert("RGB").resize(config.IMAGE_SIZE, Image.NEAREST)
    image_np = np.array(image, dtype=np.uint8)
    output = run_inference_for_single_image(np.expand_dims(image_np, 0), graph)

    common = dict(use_normalized_coordinates=True, line_thickness=5, min_score_thresh=config.MIN_SCORE)
    vis_util.visualize_boxes_and_labels_on_image_array(
        image_np, output["detection_boxes"], output["detection_classes"],
        output["detection_scores"], category_index, max_boxes_to_draw=60, **common
    )
    coordinates = vis_util.return_coordinates(
        image_np, output["detection_boxes"], output["detection_classes"],
        output["detection_scores"], category_index, **common
    )

    detections_path = out_dir / "detections.jpg"
    cv2.imwrite(str(detections_path), cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR))

    if not coordinates:
        return detections_path, None

    elements = []
    for ymin, ymax, xmin, xmax, labels in (c[:5] for c in coordinates):
        name = labels[0].split(":")[0]
        elements.append((name, int((xmin + xmax) / 2), int((ymin + ymax) / 2)))

    elements_path = write_elements(group_into_rows(elements), out_dir / "elements.txt")
    html_path = generate_html(elements_path, out_dir / "generated.html")
    return detections_path, html_path


if __name__ == "__main__":
    import argparse

    from preprocess import preprocessing

    parser = argparse.ArgumentParser(description="Convert a hand-drawn sketch into HTML.")
    parser.add_argument("image", type=Path)
    parser.add_argument("-o", "--out", type=Path, default=Path("output"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    det, html = processImage(preprocessing(args.image, args.out), args.out)
    print(f"Detections: {det}")
    print(f"HTML: {html or 'no elements detected'}")
