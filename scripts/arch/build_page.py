"""Inject the page data into the atlas template and emit the publishable page.

This script stays separate from ``build_page_data.py`` because the two files
change on different schedules. The data changes when a checkpoint moves or
someone writes a new annotation. The template changes when the design
changes. This script only joins the two.

The template holds the literal token ``__PAGE_DATA__`` inside a
``<script type="application/json">`` element. This script replaces the token
with the compact JSON of ``page_data.json``. It escapes two characters on the
way in, ``<`` and ``&``: an unescaped ``</script>`` inside the JSON string
data would close the element early and silently truncate the page.

Usage
-----
``.venv/bin/python scripts/arch/build_page.py``
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TEMPLATE = _HERE / "page_template.html"
_DATA = _HERE / "page_data.json"
_OUT = _HERE / "model_architectures.html"

_PLACEHOLDER = "__PAGE_DATA__"


def main() -> int:
    # Rebuild the data first. This stops the page from lagging the configs
    # or the annotations. A stale page that looks fresh is the failure mode
    # this guards against.
    subprocess.run([sys.executable, str(_HERE / "build_page_data.py")], check=True,
                   stdout=subprocess.DEVNULL)

    template = _TEMPLATE.read_text()
    if _PLACEHOLDER not in template:
        print(f"template is missing the {_PLACEHOLDER} token", file=sys.stderr)
        return 1

    data = json.loads(_DATA.read_text())
    payload = (
        json.dumps(data, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
    )
    page = template.replace(_PLACEHOLDER, payload)
    _OUT.write_text(page)

    annotated = sum(1 for m in data["models"].values() if m["note"])
    print(f"wrote {_OUT.relative_to(_HERE.parent.parent)} "
          f"({len(page) / 1024:.0f} KB, {len(data['models'])} models, "
          f"{annotated} annotated)")
    if annotated < len(data["models"]):
        missing = sorted(k for k, m in data["models"].items() if not m["note"])
        print(f"  NOT YET ANNOTATED ({len(missing)}): {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
