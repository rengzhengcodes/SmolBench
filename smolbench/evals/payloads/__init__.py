"""Hold the on-instance payloads: control agent, idle watchdog, cloud-init.

The ``.py.txt`` / ``.sh`` assets in this directory ride to EC2 inside
cloud-init user-data (or, for the train template, directly inside
``RunInstances``' UserData). Nothing on the client ever imports them as
modules. They run under Ubuntu 22.04's system python3 (3.10) and bash:
keep them stdlib-only and 3.10-compatible. ``tests/evals/test_ec2_payloads.py``
is their only pre-launch validation.

The assets are BYTE-EXACT payloads with a hard budget: EC2 caps user-data
at 16 KB before base64, and the cap binds on the GZIP-COMPRESSED bootstrap
(see ``pack_user_data``), not the raw rendered text -- the raw render no
longer fits. The headroom canary in ``tests/evals/test_ec2_payloads.py``
prints both the raw and compressed live margins. Every byte in ``agent.py.txt`` /
``watchdog.py.txt`` / ``user_data.sh`` ships verbatim, comments included
-- do not reformat them, and keep them LF-only (pinned by
``.gitattributes``). The non-``.py`` extension is deliberate: it keeps
black/isort/pylint and the import machinery away from files whose bytes
are a production contract (the agent also reads required env vars at
module top, so importing it would raise).

This module reads the assets ONCE, at import time, into plain ``str``
module constants -- not lazily. A test can then ``ast.parse()`` them
directly, and any missing-file breakage surfaces at import, not
mid-provision.
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
    """Fill the cloud-init user-data template; validate size and completeness.

    This function substitutes every ``@@PLACEHOLDER@@`` marker in
    ``USER_DATA_TEMPLATE`` via plain ``str.replace`` (not
    ``str.format``/f-strings -- the embedded bash and python are full of
    literal braces and dollar signs that would collide with template
    syntax). It then asserts the result is fully substituted, and fits
    EC2's user-data size cap.

    Parameters
    ----------
    control_token : str
        Per-experiment bearer token the control agent requires on
        ``ec2.EC2_AGENT_PORT``.
    vllm_api_key : str
        Per-experiment bearer token vLLM requires on ``ec2.EC2_VLLM_PORT``.
    hf_token : str
        Hugging Face token baked in for gated checkpoints, or ``""``.
        Empty is fine for the default (all-ungated) deploy specs.
    idle_timeout_min : int
        Minutes of inactivity before the on-instance watchdog self-halts.
    startup_grace_min : int
        Minutes a loading-but-not-yet-healthy model still counts as
        activity.
    max_lifetime_min : int
        Absolute backstop: ``shutdown -h`` scheduled this many minutes
        after boot, regardless of activity.
    image : str
        vLLM Docker image reference (``docker pull``-able).
    s3_cache_uri : str, optional
        ``s3://bucket/prefix`` model-cache mirror, or ``""`` to disable
        it (HF-only). Default ``""``.
    vllm_port : int, optional
        Port threaded into the instance as ``SMOLBENCH_VLLM_PORT`` (read
        by AGENT_PY/WATCHDOG_PY for their localhost health/metrics probes
        and the docker port-publish in ``_serve()``). The ``8000``
        default mirrors ``ec2.EC2_VLLM_PORT`` (a fixed, non-env
        constant; this package must not import ec2 -- ec2 imports it);
        ec2.py passes the constant explicitly at its provision call
        site.

    Returns
    -------
    str
        The fully rendered cloud-init script. This is not yet ready for
        ``RunInstances``' ``UserData`` kwarg on its own -- pass it
        through ``pack_user_data`` first, which gzip-compresses it (the
        size cap now binds on the compressed bytes; see that function's
        docstring).

    Raises
    ------
    AssertionError
        A heredoc delimiter appears inside an embedded payload script (it
        would truncate the heredoc early), or an ``@@...@@`` marker
        survives substitution.
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
    """Gzip-compress rendered cloud-init user-data for the EC2 size cap.

    EC2's 16 KB user-data limit (before boto3's base64 encoding) applies to
    these COMPRESSED bytes. This is
    transparent on the instance side: cloud-init auto-detects the gzip
    magic number and gunzips before running. It is also
    transparent to the AWS call site: ``RunInstances``' ``UserData``
    kwarg accepts either ``str`` or ``bytes``. boto3's
    ``base64_encode_user_data`` handler base64-encodes bytes directly
    (skipping only the UTF-8 encode step it would otherwise do for a
    ``str``), so passing these compressed bytes straight through to
    ``run_instances(UserData=...)`` needs no manual base64 anywhere in
    the call chain.

    Parameters
    ----------
    rendered : str
        Output of ``render_user_data`` (or any other fully-substituted
        cloud-init script) to compress.

    Returns
    -------
    bytes
        ``rendered``, UTF-8 encoded then gzip-compressed with
        ``mtime=0``. A fixed ``mtime`` (rather than the default "now")
        makes the output byte-for-byte reproducible across two calls
        with identical input. gzip's header otherwise embeds the
        compression wall-clock time, which would make this function's
        output non-deterministic, and would complicate any future
        byte-diffing of provisioned user-data.

    Raises
    ------
    AssertionError
        The compressed result is >= 16 KB (EC2's user-data cap, now
        measured post-compression rather than pre-compression).

    Notes
    -----
    This function is pure and side-effect-free. It uses
    ``gzip.compress`` at the default compression level: the payload is
    small (low tens of KB) and compresses in well under a millisecond,
    so trading compression ratio for speed via a lower level was not
    worth the tuning.
    """
    # Design: mtime=0 rather than the gzip default (current wall-clock time)
    # -- see the Returns section above for why byte-reproducibility matters
    # here (it is also what makes the byte-stability test in
    # tests/evals/test_ec2_payloads.py meaningful rather than trivially true).
    packed = gzip.compress(rendered.encode(), mtime=0)
    assert len(packed) < 16384, f"compressed user-data too large: {len(packed)} bytes"
    return packed
