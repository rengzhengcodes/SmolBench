"""Offline acceptance tests for scripts/deduction/launch_trace_box.sh (13-15).

The launcher's whole job is to emit an EC2 user-data script, so the guarantees
worth pinning are properties OF THAT EMITTED TEXT plus the order of the AWS
calls around it. Both are checked by running the real script with a fake ``aws``
first on ``PATH``: no credentials, no network, no instance, and the fake records
every argv it is handed -- including the ``--user-data`` blob, which is the
artifact the review finding was actually about.

What is pinned, and why:

* **The GitHub token never reaches the instance as a value.** The prior revision
  interpolated ``$GITHUB_ACCESS_TOKEN`` into the unquoted heredoc AND into a
  ``su ubuntu -c "... GITHUB_ACCESS_TOKEN='...' ..."`` argv. User-data is
  readable from the EC2 console and is not secret storage; a ``-c`` argv is
  readable from ``ps``. These tests export a sentinel token into the launcher's
  own environment and assert it appears nowhere in what the launcher emits.
* **The token is resolved on the box, from SSM, decrypted.** Only the parameter
  NAME travels.
* **``run-instances`` is guarded by a ``describe-instances`` check on the tag,**
  filtered to pending/running so a terminated box from a prior trace of the same
  commit cannot block a relaunch.
"""

from __future__ import annotations

import os
import subprocess

import pytest

from tests._paths import SCRIPTS

SCRIPT = SCRIPTS / "deduction" / "launch_trace_box.sh"

#: Written into the launcher's environment under the OLD variable name. If any
#: of it survives into the emitted user-data, the review finding is not fixed.
SENTINEL = "ghp_SENTINEL_TOKEN_MUST_NOT_LEAK_0123456789"


@pytest.fixture
def fake_aws(tmp_path):
    """Put a recording ``aws`` stub first on PATH; yield the call-log directory.

    The stub appends one line per invocation to ``calls.log`` (subcommand only,
    for ordering) and dumps each invocation's full argv to its own
    ``argv.<n>`` file, NUL-separated, so a test can inspect the ``--user-data``
    blob verbatim without shell-quoting games -- and, crucially, without a
    newline-separated dump splitting that multi-line blob across records.
    ``describe-instances`` answers ``None`` -- awscli's ``--output text``
    spelling for "no match" -- so the launcher proceeds to launch.
    """
    bindir = tmp_path / "bin"
    bindir.mkdir()
    log = tmp_path / "calls.log"
    stub = bindir / "aws"
    stub.write_text(
        "#!/bin/bash\n"
        f'echo "$2" >> {log}\n'
        f'n=$(wc -l < {log})\n'
        f'printf "%s\\0" "$@" > {tmp_path}/argv.$n\n'
        'if [ "$2" = "describe-instances" ]; then echo None; exit 0; fi\n'
        'if [ "$2" = "run-instances" ]; then echo i-fake0123; exit 0; fi\n'
        'echo ami-fake0123\n'
    )
    stub.chmod(0o755)
    yield tmp_path, bindir


def _run(bindir, *args, env_extra=None):
    env = dict(os.environ)
    env["PATH"] = f"{bindir}:{env['PATH']}"
    env["GITHUB_ACCESS_TOKEN"] = SENTINEL
    env.update(env_extra or {})
    return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True,
                          text=True, timeout=120, env=env)


def _user_data(workdir):
    """The ``--user-data`` value from the recorded ``run-instances`` argv."""
    for path in sorted(workdir.glob("argv.*")):
        argv = path.read_text().split("\0")
        if "run-instances" in argv:
            return argv[argv.index("--user-data") + 1]
    raise AssertionError(f"no run-instances call recorded in {workdir}")


def test_script_parses():
    """`bash -n` on both the launcher and the runbook it ships."""
    for path in (SCRIPT, SCRIPTS / "deduction" / "trace_mathlib_ec2.sh"):
        proc = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
        assert proc.returncode == 0, f"{path.name}: {proc.stderr}"


def test_dry_run_needs_no_aws_at_all(tmp_path):
    """The plan prints with an EMPTY environment and no `aws` binary on PATH.

    `env -i` with a minimal PATH is the check: it proves the dry-run makes no
    AWS call whatsoever (the AMI lookup is skipped and printed unresolved),
    which is what makes this script reviewable without an account.
    """
    proc = subprocess.run(
        ["env", "-i", "PATH=/usr/bin:/bin", f"HOME={tmp_path}",
         f"GITHUB_ACCESS_TOKEN={SENTINEL}", "bash", str(SCRIPT), "--dry-run"],
        capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert "region=us-west-2" in proc.stdout
    assert "ssm_param=/smolbench/deduction/github_access_token" in proc.stdout
    assert SENTINEL not in proc.stdout + proc.stderr


def test_token_value_never_reaches_the_user_data(fake_aws):
    """13-15: the emitted user-data carries the SSM parameter NAME, never a token.

    Was: the unquoted heredoc expanded ``$GITHUB_ACCESS_TOKEN`` into user-data
    and into the ``su ubuntu -c`` command string, so the token was readable
    from the EC2 console and from ``ps`` on the box. Now the box resolves it
    itself, through its instance role.
    """
    workdir, bindir = fake_aws
    proc = _run(bindir)
    assert proc.returncode == 0, proc.stderr
    user_data = _user_data(workdir)

    assert SENTINEL not in user_data, "the token VALUE leaked into user-data"
    assert SENTINEL not in proc.stdout + proc.stderr
    # The fetch happens on the instance, decrypted, by parameter name.
    assert "ssm get-parameter" in user_data
    assert "--with-decryption" in user_data
    assert "/smolbench/deduction/github_access_token" in user_data
    # The `su` line must not carry the secret on its argv at all -- neither a
    # literal nor a launcher-interpolated one.
    su_lines = [ln for ln in user_data.splitlines() if ln.lstrip().startswith("su ubuntu")]
    assert len(su_lines) == 1, su_lines
    assert "GITHUB_ACCESS_TOKEN" not in su_lines[0], su_lines[0]
    assert "trace_mathlib_ec2.sh" in su_lines[0]
    # A missing/empty parameter must fail loudly rather than run unauthenticated.
    assert "exit 1" in user_data


def test_launcher_env_token_is_not_required(fake_aws):
    """The launcher no longer needs the token in its own environment.

    The old `: "${GITHUB_ACCESS_TOKEN:?...}"` guard made an operator export the
    secret on the workstation that runs this script; the whole point of moving
    to SSM is that nothing but the instance ever holds it.
    """
    workdir, bindir = fake_aws
    env = dict(os.environ)
    env["PATH"] = f"{bindir}:{env['PATH']}"
    env.pop("GITHUB_ACCESS_TOKEN", None)
    proc = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True,
                          timeout=120, env=env)
    assert proc.returncode == 0, proc.stderr
    assert "i-fake0123" in proc.stdout


def test_describe_instances_guards_run_instances(fake_aws):
    """13-15: an in-flight box for this commit's tag stops a second launch.

    Three properties, because only the combination is the fix: the check runs
    BEFORE `run-instances`; it filters on instance-state-name so a terminated
    box from a prior trace of the same commit does not block a relaunch; and
    `--force` skips it.
    """
    workdir, bindir = fake_aws
    proc = _run(bindir)
    assert proc.returncode == 0, proc.stderr
    calls = (workdir / "calls.log").read_text().split()
    assert "describe-instances" in calls and "run-instances" in calls
    assert calls.index("describe-instances") < calls.index("run-instances")

    describe = next(p.read_text().split("\0") for p in sorted(workdir.glob("argv.*"))
                    if "describe-instances" in p.read_text().split("\0"))
    filters = [a for a in describe if a.startswith("Name=")]
    assert any(a.startswith("Name=tag:Name,Values=smolbench-trace-") for a in filters), filters
    assert "Name=instance-state-name,Values=pending,running" in filters, filters


def test_force_skips_the_idempotency_check(fake_aws):
    """`--force` launches without asking, for a manually-killed stuck box."""
    workdir, bindir = fake_aws
    proc = _run(bindir, "--force")
    assert proc.returncode == 0, proc.stderr
    calls = (workdir / "calls.log").read_text().split()
    assert "describe-instances" not in calls
    assert "run-instances" in calls


def test_an_in_flight_instance_stops_the_launch(fake_aws, tmp_path):
    """A pending/running match short-circuits: id printed, nothing launched."""
    workdir, bindir = fake_aws
    (bindir / "aws").write_text(
        "#!/bin/bash\n"
        f'echo "$2" >> {workdir}/calls.log\n'
        'if [ "$2" = "describe-instances" ]; then echo i-already-running; exit 0; fi\n'
        'echo ami-fake0123\n'
    )
    (bindir / "aws").chmod(0o755)
    proc = _run(bindir)
    assert proc.returncode == 0, proc.stderr
    assert "i-already-running" in proc.stdout
    assert "run-instances" not in (workdir / "calls.log").read_text()
