"""Validation and storage of user-uploaded sketch images."""

import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from config import ALLOWED_EXTENSIONS

# Refuse decompression bombs: a sketch never needs more than ~40 megapixels.
Image.MAX_IMAGE_PIXELS = 40_000_000


class UploadError(ValueError):
    """Raised with a message that is safe to show to the user."""


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def new_job_dir(root: Path) -> Path:
    """Create a fresh, unguessable directory for one conversion."""
    job = root / uuid.uuid4().hex
    job.mkdir(parents=True, exist_ok=False)
    return job


def save_upload(file: FileStorage, job_dir: Path) -> Path:
    """Validate an uploaded image and store it inside ``job_dir``.

    The user-supplied filename is only used to check the extension; the file is
    always written under a fixed name, so path traversal is impossible.
    """
    if file is None or not file.filename:
        raise UploadError("Choose an image to upload.")
    name = secure_filename(file.filename)
    if not allowed_file(name):
        raise UploadError("Only PNG and JPEG images are supported.")

    try:
        with Image.open(file.stream) as img:
            img.verify()  # detects truncated or non-image files
        file.stream.seek(0)
        with Image.open(file.stream) as img:
            if img.format not in {"PNG", "JPEG"}:
                raise UploadError("Only PNG and JPEG images are supported.")
            dest = job_dir / "input.png"
            img.convert("RGB").save(dest, format="PNG")  # re-encode: strips metadata and payloads
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise UploadError("That file isn't a readable image.") from None
    return dest
