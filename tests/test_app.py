import io
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

import config

config.RESULTS_DIR = Path(tempfile.mkdtemp())
from app import app  # noqa: E402


def png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(buf, format="PNG")
    return buf.getvalue()


class AppTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(config.RESULTS_DIR, ignore_errors=True)

    def setUp(self):
        self.client = app.test_client()

    def post(self, data: bytes, name: str):
        return self.client.post("/generate", data={"image": (io.BytesIO(data), name)},
                                content_type="multipart/form-data")

    def test_index_has_security_headers(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("default-src 'self'", r.headers["Content-Security-Policy"])

    def test_missing_file(self):
        self.assertEqual(self.client.post("/generate").status_code, 400)

    def test_rejects_wrong_extension(self):
        self.assertEqual(self.post(png_bytes(), "sketch.exe").status_code, 400)

    def test_rejects_non_image_with_image_extension(self):
        self.assertEqual(self.post(b"<?php system($_GET['c']); ?>", "shell.png").status_code, 400)

    def test_path_traversal_name_is_harmless(self):
        r = self.post(b"not an image", "../../app.py.png")
        self.assertEqual(r.status_code, 400)
        self.assertTrue(Path("app.py").exists())

    def test_rejected_uploads_leave_nothing_behind(self):
        self.post(b"junk", "x.png")
        self.assertEqual(list(config.RESULTS_DIR.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
