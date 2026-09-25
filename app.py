"""Flask web app: upload a hand-drawn sketch, get HTML and CSS back."""

import logging
import shutil

from flask import Flask, render_template, request, url_for

import config
from css_gen import add_styles
from uploads import UploadError, new_job_dir, save_upload

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_MB * 1024 * 1024


@app.after_request
def security_headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    if resp.mimetype == "text/html" and request.endpoint != "static":
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline' "
            "https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
            "script-src 'self' 'unsafe-inline'; frame-src 'self'; object-src 'none'; base-uri 'none'",
        )
    return resp


@app.get("/")
def index():
    return render_template("index.html", max_mb=config.MAX_UPLOAD_MB)


@app.post("/generate")
def generate():
    job_dir = new_job_dir(config.RESULTS_DIR)
    try:
        input_path = save_upload(request.files.get("image"), job_dir)
    except UploadError as exc:
        shutil.rmtree(job_dir, ignore_errors=True)
        return render_template("index.html", error=str(exc), max_mb=config.MAX_UPLOAD_MB), 400

    try:
        # Heavy imports (TensorFlow) are deferred so the app starts quickly.
        from main import processImage
        from preprocess import preprocessing

        edges = preprocessing(input_path, job_dir)
        detections, html_path = processImage(edges, job_dir)
    except FileNotFoundError as exc:
        log.error("%s", exc)
        return render_template("index.html", error="The detection model isn't installed on this server.",
                               max_mb=config.MAX_UPLOAD_MB), 500
    except Exception:
        log.exception("Conversion failed")
        return render_template("index.html", error="Something went wrong while reading the sketch. Try a clearer photo.",
                               max_mb=config.MAX_UPLOAD_MB), 500

    job = job_dir.name
    url = lambda name: url_for("static", filename=f"results/{job}/{name}")  # noqa: E731

    if html_path is None:
        return render_template("result.html", input_image=url("input.png"), output_image=url(detections.name),
                               html_page=None, styled_page=None, source=None)

    styled_html, source = add_styles(html_path.read_text(encoding="utf-8"))
    (job_dir / "styled.html").write_text(styled_html, encoding="utf-8")

    return render_template(
        "result.html",
        input_image=url("input.png"),
        output_image=url(detections.name),
        html_page=url("generated.html"),
        styled_page=url("styled.html"),
        source=source,
    )


@app.errorhandler(413)
def too_large(_):
    return render_template("index.html", error=f"That file is larger than {config.MAX_UPLOAD_MB} MB.",
                           max_mb=config.MAX_UPLOAD_MB), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=config.FLASK_DEBUG, use_reloader=False)
