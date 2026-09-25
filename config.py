"""Central configuration. Everything machine-specific comes from the environment.

Copy ``.env.example`` to ``.env`` (git-ignored) or export the variables in your shell.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_dotenv(path: Path = BASE_DIR / ".env") -> None:
    """Minimal .env loader so python-dotenv isn't required."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

# --- Model -------------------------------------------------------------------
# Directory containing the TensorFlow Object Detection API ("models/research").
TF_MODELS_RESEARCH_DIR = os.environ.get("TF_MODELS_RESEARCH_DIR", "")
MODEL_PATH = Path(os.environ.get("MODEL_PATH", BASE_DIR / "frozen_inference_graph_816.pb"))
LABELS_PATH = Path(os.environ.get("LABELS_PATH", BASE_DIR / "labels.pbtxt"))
MIN_SCORE = float(os.environ.get("MIN_SCORE", "0.5"))

# Detector input size (width, height) used during training.
IMAGE_SIZE = (950, 1000)

# --- Styling (optional) ------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

# --- Web app -----------------------------------------------------------------
RESULTS_DIR = BASE_DIR / "static" / "results"
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "8"))
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
