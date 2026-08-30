"""Hold the on-instance payloads: control agent, idle watchdog, cloud-init.

The ``.py.txt`` / ``.sh`` assets here ride to EC2 inside cloud-init user-data
(or, for the train template, directly inside ``RunInstances``' UserData).
Nothing on the client imports them as modules; they run under Ubuntu 22.04's
system python3 (3.10) and bash, so keep them stdlib-only and 3.10-compatible.
``tests/evals/test_ec2_payloads.py`` is their only pre-launch validation.

They are BYTE-EXACT payloads: every byte ships verbatim, comments included --
do not reformat them, and keep them LF-only (pinned by ``.gitattributes``). The
non-``.py`` extension keeps formatters and the import machinery away from files
whose bytes are a production contract (the agent also reads required env vars
at module top, so importing it would raise). EC2 caps user-data at 16 KB before
base64, and the cap binds on the GZIP-COMPRESSED bootstrap (see
``pack_user_data``), not the raw render, which no longer fits.

The assets are read ONCE at import time into plain ``str`` constants, so a test
can ``ast.parse()`` them directly and a missing file surfaces at import rather
than mid-provision.
"""

import gzip
from pathlib import Path

# Anchored to this file, matching the repo's __file__-anchoring convention --
# resolves identically under both editable venvs and a built wheel (the
# assets ship via [tool.setuptools.package-data] in pyproject.toml).
_HERE = Path(__file__).resolve().parent


def _asset(name: str) -> str:
    # Default universal-newline read_text (never newline=""): a CRLF-corrupted
    # checkout then still yields the LF bytes the heredocs and the 16 KB cap
    # were sized for, and the .gitattributes pin keeps CRLF out of the repo.
    return (_HERE / name).read_text(encoding="utf-8")


# Control agent: the notebook's only way to drive the instance (no SSH, no SSM
# role). Bearer-authenticated HTTP on :9000; every authenticated request also
# feeds the idle watchdog by touching last_active. /serve launches docker
# asynchronously because a cold `docker run` may first pull the multi-GB vLLM
# image; progress is observable via /status instead of a long-blocking POST.
AGENT_PY: str = _asset("agent.py.txt")

# Idle watchdog: a long-running service that checks once a minute. It is a
# plain loop under Restart=always rather than a systemd timer ON PURPOSE --
# the obvious OnUnitActiveSec=60 + Type=oneshot pairing fires exactly once,
# because a oneshot unit never enters the "active" state the timer measures
# from (found live: the smoke instance's watchdog never re-armed). Activity =
#   (a) any authenticated control-agent request (the agent touches last_active),
#   (b) movement in vLLM's request-token counters, or requests in flight
#       (clients hit vLLM directly during evals, invisible to the agent), or
#   (c) a container that is up but not yet answering /metrics (weights still
#       downloading/loading), honored only within the startup grace window.
# vLLM's --api-key only guards /v1/*; /metrics and /health are keyless on
# localhost, and the security group closes the port to everyone else.
WATCHDOG_PY: str = _asset("watchdog.py.txt")

# Cloud-init bootstrap for the SERVING box. @@PLACEHOLDER@@ markers are filled
# by render_user_data via str.replace -- NOT str.format/f-strings, since the
# embedded bash and python are full of braces and dollar signs. The max-
# lifetime backstop is scheduled FIRST so the box self-halts even if a later
# bootstrap step fails. Heredocs are single-quoted (<<'EOF') so the embedded
# scripts land byte-exact. The static systemd units stay inside this template
# on purpose: they render through the same heredoc mechanism, and keeping each
# heredoc next to its delimiter is what makes the truncation guard in
# render_user_data easy to reason about.
USER_DATA_TEMPLATE: str = _asset("user_data.sh")

def render_user_data(
    control_token: str,
    vllm_api_key: str,
    hf_token: str,
    idle_timeout_min: int,
    startup_grace_min: int,
    max_lifetime_min: int,
    image: str,
    s3_cache_uri: str = "",
    vllm_port: int = 8000,
) -> str:
    """Fill every ``@@PLACEHOLDER@@`` in ``USER_DATA_TEMPLATE``; assert completeness.

    Parameters
    ----------
    control_token : str
        Bearer token the control agent (``ec2.EC2_AGENT_PORT``) requires.
    vllm_api_key : str
        Bearer token vLLM requires. Both tokens are per-experiment.
    hf_token : str
        Token for gated checkpoints; ``""`` is fine (default specs are ungated).
    idle_timeout_min : int
        Minutes of inactivity before the on-instance watchdog self-halts.
    startup_grace_min : int
        Minutes a loading-but-not-yet-healthy model still counts as activity.
    max_lifetime_min : int
        Absolute ``shutdown -h`` backstop, this many minutes after boot.
    image : str
        ``docker pull``-able vLLM image reference.
    s3_cache_uri : str, optional
        ``s3://bucket/prefix`` model-cache mirror; ``""`` disables it.
    vllm_port : int, optional
        Rides in as ``SMOLBENCH_VLLM_PORT``. The ``8000`` default mirrors
        ``ec2.EC2_VLLM_PORT``, which this package must not import (ec2 imports
        it), so ec2.py passes the constant explicitly.

    Returns
    -------
    str
        The rendered script, NOT yet ready for ``RunInstances``' ``UserData``
        -- pass it through :func:`pack_user_data` first.

    Raises
    ------
    AssertionError
        A heredoc delimiter appears inside an embedded payload script (it would
        truncate the heredoc early), or an ``@@...@@`` marker survived
        substitution.
    """
    for payload, delimiter in ((AGENT_PY, "AGENT_EOF"), (WATCHDOG_PY, "WATCHDOG_EOF")):
        # A heredoc terminates at its delimiter; the scripts must never
        # contain one as a line of their own.
        assert delimiter not in payload, f"{delimiter} must not appear in the embedded script"
    rendered = USER_DATA_TEMPLATE
    for marker, value in (
        ("@@MAX_LIFETIME_MIN@@", str(max_lifetime_min)),
        ("@@CONTROL_TOKEN@@", control_token),
        ("@@VLLM_API_KEY@@", vllm_api_key),
        ("@@HF_TOKEN@@", hf_token),
        ("@@VLLM_IMAGE@@", image),
        ("@@S3_CACHE_URI@@", s3_cache_uri),
        ("@@IDLE_TIMEOUT_MIN@@", str(idle_timeout_min)),
        ("@@STARTUP_GRACE_MIN@@", str(startup_grace_min)),
        ("@@VLLM_PORT@@", str(vllm_port)),
        ("@@AGENT_PY@@", AGENT_PY.rstrip("\n")),
        ("@@WATCHDOG_PY@@", WATCHDOG_PY.rstrip("\n")),
    ):
        rendered = rendered.replace(marker, value)
    assert "@@" not in rendered, "unsubstituted placeholder left in user-data"
    return rendered


def pack_user_data(rendered: str) -> bytes:
    """Gzip-compress a rendered cloud-init script for the EC2 size cap (pure).

    EC2's 16 KB user-data limit (before base64) applies to these COMPRESSED
    bytes. Compression is transparent on both ends: cloud-init detects the gzip
    magic number and gunzips before running, and boto3 base64-encodes a
    ``bytes`` ``UserData`` directly.

    Returns
    -------
    bytes
        `rendered`, UTF-8 encoded then gzip-compressed, ready to pass straight
        to ``run_instances(UserData=...)``. ``mtime=0`` (rather than gzip's
        default "now") keeps the output byte-for-byte reproducible for
        identical input, which is what makes the byte-stability test in
        ``tests/evals/test_ec2_payloads.py`` meaningful.

    Raises
    ------
    AssertionError
        The compressed result is >= 16 KB.
    """
    # Design: mtime=0 rather than the gzip default (current wall-clock time)
    # -- see the Returns section above for why byte-reproducibility matters
    # here (it is also what makes the byte-stability test in
    # tests/evals/test_ec2_payloads.py meaningful rather than trivially true).
    packed = gzip.compress(rendered.encode(), mtime=0)
    assert len(packed) < 16384, f"compressed user-data too large: {len(packed)} bytes"
    return packed
