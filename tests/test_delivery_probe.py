"""Offline tests for scripts/delivery_probe.py's two parsers.

The probe exists to answer ONE question during a live run -- "did the server
finish this request, and did the body reach us?" -- so the only things worth
pinning are the two readings that question rests on: the finish-reason split
(the 2026-08-14 loss hit ``length`` and spared ``stop``, and a parser that
collapsed the labels would have hidden exactly that) and the receive-queue
depth (an ESTABLISHED socket with an EMPTY queue is the fault's signature; a
socket with bytes waiting is just a slow reader).
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "delivery_probe",
    Path(__file__).resolve().parents[1] / "scripts" / "delivery_probe.py",
)
probe = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = probe
_SPEC.loader.exec_module(probe)


_METRICS = """\
# HELP vllm:num_requests_running Number of requests in model execution batches.
# TYPE vllm:num_requests_running gauge
vllm:num_requests_running{model_name="m"} 4.0
vllm:num_requests_waiting{model_name="m"} 0.0
vllm:generation_tokens_total{model_name="m"} 360874.0
vllm:prompt_tokens_total{model_name="m"} 1602.0
vllm:request_success_total{finished_reason="stop",model_name="m"} 13.0
vllm:request_success_total{finished_reason="length",model_name="m"} 28.0
vllm:some_other_metric{model_name="m"} 99.0
"""


def test_scrape_splits_finish_reasons(monkeypatch):
    """The stop/length split must survive parsing -- it IS the diagnosis."""

    class _Resp:
        def read(self):
            return _METRICS.encode()

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    monkeypatch.setattr(probe.urllib.request, "urlopen", lambda *a, **k: _Resp())
    got = probe.scrape_metrics("1.2.3.4", "key")

    assert got["vllm:request_success_total[stop]"] == 13.0
    assert got["vllm:request_success_total[length]"] == 28.0
    assert got["vllm:generation_tokens_total"] == 360874.0
    # Unlisted metrics are dropped rather than carried along as noise.
    assert "vllm:some_other_metric" not in got


def test_scrape_failure_is_a_measurement_not_an_exception(monkeypatch):
    """An unreachable box must be reported, never raised.

    The probe's whole job is to keep sampling ACROSS a blip -- a scrape that
    raised would end the watch at exactly the moment worth watching.
    """

    def _boom(*_a, **_k):
        raise OSError("Connection refused")

    monkeypatch.setattr(probe.urllib.request, "urlopen", _boom)
    got = probe.scrape_metrics("1.2.3.4", None)
    assert got["_scrape_error"] == 1.0
    assert "Connection refused" in got["_scrape_error_msg"]


def test_client_sockets_reports_recv_queue(monkeypatch):
    """Depth, not just count: an EMPTY queue is what says nothing arrived."""
    out = (
        "State   Recv-Q Send-Q  Local Address:Port   Peer Address:Port\n"
        "ESTAB   0      0       10.0.0.2:51234       1.2.3.4:8000\n"
        "ESTAB   4096   0       10.0.0.2:51236       1.2.3.4:8000\n"
    )
    monkeypatch.setattr(
        probe.subprocess, "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout=out, stderr=""),
    )
    rows = probe.client_sockets("1.2.3.4")
    assert rows == [("ESTAB", 0), ("ESTAB", 4096)]


def test_client_sockets_tolerates_missing_ss(monkeypatch):
    def _boom(*_a, **_k):
        raise FileNotFoundError("ss")

    monkeypatch.setattr(probe.subprocess, "run", _boom)
    assert probe.client_sockets("1.2.3.4") == []
