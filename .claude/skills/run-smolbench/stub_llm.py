"""Two local OpenAI-compatible stub LLM servers for driving a REAL lean sweep.

Used by `lean_smoke.sh --e2e`: fake models, real LeanDojo verification.

Port A (model "stub-good-model", served as provider `primeintellect`) answers
every chat completion with the CORRECT ground-truth tail for
Lagrange.eval_nodal_at_node at k=1, fenced as ```lean, so the sweep row must
come back `verdict: success`. Port B (model "stub-bad-model", served as
provider `openrouter`) answers with a bogus tactic, so the row must come back
`verdict: lean_error` ("unknown identifier 'nonexistent_lemma_xyz42'").

Both servers also answer the providers' context-length GETs (OpenRouter's
`/endpoints` shape and Prime Intellect's flat shape). Every POST is logged as
one JSON line to argv[1] so the caller can assert what the sweep actually sent
(seed / system message / temperature / model). Ports are OS-assigned and
printed once to stdout as {"pi": <port>, "or": <port>}. Stdlib only.
"""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REQLOG = sys.argv[1]
GOOD = "Here is the proof:\n```lean\nexact s.prod_eq_zero hi (sub_self (v i))\n```"
BAD = "```lean\nexact nonexistent_lemma_xyz42\n```"
LOCK = threading.Lock()


def make_handler(name, answer):
    class H(BaseHTTPRequestHandler):
        def _reply(self, obj):
            body = json.dumps(obj).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", "0") or "0")
            payload = json.loads(self.rfile.read(n) or b"{}")
            with LOCK, open(REQLOG, "a") as f:
                f.write(json.dumps({"stub": name, "path": self.path, "body": payload}) + "\n")
            self._reply({
                "model": payload.get("model", ""),
                "choices": [{"message": {"content": answer}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
            })

        def do_GET(self):
            if self.path.endswith("/endpoints"):  # OpenRouter ctx-length shape
                self._reply({"data": {"endpoints": [{"context_length": 100000}]}})
            else:  # Prime Intellect ctx-length shape
                self._reply({"context_length": 100000})

        def log_message(self, *a):
            pass

    return H


srv_pi = ThreadingHTTPServer(("127.0.0.1", 0), make_handler("PI", GOOD))
srv_or = ThreadingHTTPServer(("127.0.0.1", 0), make_handler("OR", BAD))
print(json.dumps({"pi": srv_pi.server_address[1], "or": srv_or.server_address[1]}), flush=True)
threading.Thread(target=srv_pi.serve_forever, daemon=True).start()
srv_or.serve_forever()
