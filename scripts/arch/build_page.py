"""Inject the page data into the atlas template and emit the publishable page.

Kept separate from ``build_page_data.py`` so the two things that change on
different schedules stay apart: the data changes when a checkpoint moves or an
annotation is written, the template changes when the design does. This script
only does the join.

The template carries the literal token ``__PAGE_DATA__`` inside a
``<script type="application/json">`` element; it is replaced with the compact
JSON of ``page_data.json``. Two characters are escaped on the way in --
``<`` and ``&`` -- because an unescaped ``</script>`` inside JSON string data
would close the element early and silently truncate the page.

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
    # Rebuild the data first so the page can never lag the configs or the
    # annotations -- a stale page that looks fresh is the failure mode here.
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
