"""Adds a stylesheet to a generated page, optionally written by Gemini.

Without ``GEMINI_API_KEY`` a built-in stylesheet is used, so the app works
offline. Model output is treated as untrusted: only CSS from the reply is
kept, and anything that could close the <style> element is removed.
"""

import logging
import re

from config import GEMINI_API_KEY, GEMINI_MODEL

log = logging.getLogger(__name__)

STYLE_MARKER = "<!-- STYLES -->"

DEFAULT_CSS = """
:root { color-scheme: light; --ink: #1f2937; --muted: #6b7280; --line: #d1d5db; --accent: #2563eb; }
* { box-sizing: border-box; }
body { margin: 0; font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; color: var(--ink); background: #f9fafb; }
.page { max-width: 720px; margin: 40px auto; padding: 32px; background: #fff; border: 1px solid var(--line); border-radius: 10px; }
.row { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; margin-bottom: 18px; }
.label { font-weight: 600; min-width: 120px; }
.field { flex: 1 1 220px; padding: 10px 12px; border: 1px solid var(--line); border-radius: 6px; font: inherit; }
.field:focus { outline: 2px solid var(--accent); outline-offset: 1px; border-color: var(--accent); }
.choice { display: inline-flex; align-items: center; gap: 6px; color: var(--muted); }
.button { padding: 10px 20px; border: 0; border-radius: 6px; background: var(--accent); color: #fff; font: inherit; cursor: pointer; }
.button:hover { filter: brightness(1.1); }
.image { border-radius: 6px; max-width: 100%; }
""".strip()

PROMPT = (
    "Write a clean, modern CSS stylesheet for the HTML page below. It uses the classes "
    "page, row, label, field, choice, button and image. Reply with CSS only, no explanation.\n\n"
)

_FENCE = re.compile(r"```(?:css)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def sanitize_css(text: str) -> str:
    """Extract CSS from a model reply and neutralise anything that could escape <style>."""
    match = _FENCE.search(text)
    css = match.group(1) if match else text
    css = re.sub(r"</?\s*style[^>]*>", "", css, flags=re.IGNORECASE)
    css = css.replace("<", "\\3C ")  # no raw '<' at all inside the style element
    css = re.sub(r"@import[^;]*;", "", css, flags=re.IGNORECASE)  # no remote stylesheets
    css = re.sub(r"expression\s*\(", "", css, flags=re.IGNORECASE)
    return css.strip()


def gemini_css(html: str) -> str:
    import google.generativeai as genai  # optional dependency

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    reply = model.generate_content(PROMPT + html, request_options={"timeout": 30})
    return sanitize_css(reply.text)


def add_styles(html: str) -> tuple:
    """Return ``(styled_html, source)`` where ``source`` is "gemini" or "default"."""
    css, source = DEFAULT_CSS, "default"
    if GEMINI_API_KEY:
        try:
            generated = gemini_css(html)
            if generated:
                css, source = generated, "gemini"
        except Exception:  # network, quota, or SDK errors: fall back quietly
            log.exception("Gemini styling failed; using the default stylesheet")
    style = f"<style>\n{css}\n</style>"
    if STYLE_MARKER in html:
        return html.replace(STYLE_MARKER, style, 1), source
    return html.replace("</head>", style + "\n</head>", 1), source
