"""Turns the ordered list of detected UI elements into an HTML page."""

from pathlib import Path
from typing import Iterable, List, Sequence

BREAK = "BREAK"

# Inline SVG placeholder so generated pages don't depend on a running server.
_IMAGE_PLACEHOLDER = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='160' height='100'>"
    "<rect width='100%' height='100%' fill='%23e5e7eb'/>"
    "<text x='50%' y='55%' font-family='sans-serif' font-size='14' fill='%236b7280' "
    "text-anchor='middle'>Image</text></svg>"
)


def element_html(name: str, index: int) -> str:
    """HTML snippet for one detected element. ``index`` keeps ids unique."""
    templates = {
        "TextBox": f'<input type="text" id="field{index}" class="field" placeholder="Text">',
        "Label": f'<label class="label" for="field{index + 1}">Label</label>',
        "RadioButton": f'<label class="choice"><input type="radio" name="group"> Option {index}</label>',
        "CheckBox": f'<label class="choice"><input type="checkbox"> Option {index}</label>',
        "Button": '<button type="button" class="button">Button</button>',
        "Image": f'<img class="image" src="{_IMAGE_PLACEHOLDER}" alt="Image placeholder" height="100">',
    }
    return templates.get(name, "")


def rows_from_elements(lines: Iterable[str]) -> List[List[str]]:
    """Parse ``name,x,y`` lines separated by ``BREAK`` markers into rows of names."""
    rows: List[List[str]] = [[]]
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line == BREAK:
            rows.append([])
            continue
        rows[-1].append(line.split(",", 1)[0])
    return [r for r in rows if r]


def render_page(rows: Sequence[Sequence[str]], title: str = "Generated page") -> str:
    body = []
    counter = 0
    for row in rows:
        parts = []
        for name in row:
            counter += 1
            snippet = element_html(name, counter)
            if snippet:
                parts.append("      " + snippet)
        if parts:
            body.append('    <div class="row">\n' + "\n".join(parts) + "\n    </div>")
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"  <title>{title}</title>\n"
        "  <!-- STYLES -->\n"
        "</head>\n"
        "<body>\n"
        '  <form class="page" onsubmit="return false">\n'
        + "\n".join(body)
        + "\n  </form>\n</body>\n</html>\n"
    )


def generate_html(elements_path: Path, out_path: Path) -> Path:
    """Read the detector's element list and write the generated HTML page."""
    rows = rows_from_elements(Path(elements_path).read_text(encoding="utf-8").splitlines())
    Path(out_path).write_text(render_page(rows), encoding="utf-8")
    return Path(out_path)
