"""Run the Horn pipeline end to end on a laptop, with no model.

Renders a small rung, starts a local OpenAI-compatible server that answers every prompt
with the rung's designed proof, runs ``sweep.py`` against it, and prints the report.
Every cell should pass.

    python scripts/deduction/horn/demo.py --out /tmp/horn_demo
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
for p in (str(REPO_ROOT), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

# pylint: disable=wrong-import-position
import sweep  # noqa: E402  (scripts/deduction/horn/sweep.py)
from smolbench.deduction.horn.cli import parse_seeds  # noqa: E402
from smolbench.deduction.horn.repro import render_rung, report  # noqa: E402


class Oracle(BaseHTTPRequestHandler):
    """Answer a chat completion with the designed proof of the prompt's theory."""

    proofs: dict[str, list[str]] = {}

    def do_POST(self):  # noqa: N802  # pylint: disable=invalid-name
        """One non-streaming chat completion."""
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        prompt = body["messages"][-1]["content"]
        steps = self.proofs[hashlib.sha256(prompt.encode()).hexdigest()]
        content = "Proof:\n" + "\n".join(steps) + "\n"
        data = json.dumps(
            {
                "model": body["model"],
                "choices": [{"message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):  # noqa: A002  # pylint: disable=redefined-builtin
        return


def load_proofs(rung: Path) -> dict[str, list[str]]:
    """``sha256(prompt) -> designed proof steps`` for every rendered arm."""
    out = {}
    for meta in rung.glob("s*/*/meta.json"):
        prompt = (meta.parent / "prompt.md").read_text(encoding="utf-8")
        steps = json.loads(meta.read_text(encoding="utf-8"))["designed_proof"]
        out[hashlib.sha256(prompt.encode()).hexdigest()] = steps
    return out


def main(argv: list[str] | None = None) -> int:
    """Render, serve, sweep and report."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", maxsplit=1)[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--m", type=int, default=4, help="chain length")
    ap.add_argument("--seeds", default="0-4")
    ap.add_argument("--replicates", type=int, default=1)
    a = ap.parse_args(argv)

    rung = a.out / f"m{a.m}"
    render_rung(rung, a.m, parse_seeds(a.seeds))
    Oracle.proofs = load_proofs(rung)
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Oracle)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    out = a.out / "rows.jsonl"
    out.unlink(missing_ok=True)
    try:
        rc = sweep.main(
            [
                "--endpoint", f"http://127.0.0.1:{srv.server_address[1]}/v1",
                "--model", "oracle",
                "--thinking", "off",
                "--rung-dir", str(rung),
                "--replicates", str(a.replicates),
                "--no-stream",
                "--out", str(out),
            ]
        )  # fmt: skip
    finally:
        srv.shutdown()
    if rc:
        print(f"sweep failed (exit {rc})")
        return rc
    print(report([out]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
