"""One supervised shard of a direct ``notebooks/induction/run_study.py`` run.

`Shard` is the unit ``run_shards.py`` supervises: one child process, its log
file, its EC2 state file and the counters the shared restart policy
(``policy.py``) needs. Every field is a constructor parameter, so a shard can
be built -- and the supervision loop driven -- without an argparse namespace.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional


@dataclass
class Shard:
    """One shard of a direct ``run_study.py`` run, and its supervision state.

    A shard is either LAUNCHED by this process (`proc` holds a
    ``subprocess.Popen``) or ADOPTED from an already-running process found by
    `find_adoptable` (`adopted_pid` holds its pid), never both; `launch`
    clears `adopted_pid` when it takes over.

    selector: the ``INDUCTION_SHARD`` selector ``"i/n"``, or `None` for an
    unsharded run -- the value `find_adoptable` matches a live process's
    environment against, so `None` is meaningful, not a "missing" value.
    log: this shard's log FILE, not its directory; `launch` appends to it,
    `returncode` reads its tail.
    env: the COMPLETE child environment (`run_shards.shard_env`'s return),
    not an overlay on the parent's.
    state_file: not read here; carried so `run_shards.terminate_shard_box`
    can reclaim the box from the shard alone.

    `status` is one of ``"pending"``/``"running"``/``"done"``/``"halted"``.
    `crash_relaunches`/`reclaim_relaunches` are the POST-increment counts
    `policy.decide_relaunch` expects: the supervisor bumps the counter
    matching the verdict, then passes it straight in.

    Known limitation: `alive` tests an adopted shard's liveness with a
    ``/proc/<pid>`` existence check; if the OS later recycles that pid to an
    unrelated process, this shard reads as alive forever. Fixing it needs a
    stronger identity than the pid, e.g. matching ``/proc/<pid>/environ`` the
    way `find_adoptable` does.
    """

    index: int
    selector: Optional[str]
    log: Path
    env: Mapping[str, str] = field(repr=False)  # holds AWS/HF credentials
    state_file: Path
    python: Path
    driver: Path
    cwd: Path
    proc: Optional[subprocess.Popen] = None
    adopted_pid: Optional[int] = None
    status: str = "pending"  # pending|running|done|halted
    crash_relaunches: int = 0
    reclaim_relaunches: int = 0

    def alive(self) -> bool:
        """Report whether this shard's process is still running.

        For a launched shard: whether ``proc.poll()`` is still `None`. For an
        adopted one: whether ``/proc/<adopted_pid>`` still exists (see the
        class docstring on pid recycling). `False` for pending/done/halted.
        """
        if self.proc is not None:
            return self.proc.poll() is None
        if self.adopted_pid is not None:
            return Path(f"/proc/{self.adopted_pid}").exists()
        return False

    def returncode(self) -> Optional[int]:
        """Return this shard's exit status, inferring it for an adopted process.

        `proc.poll()` for a launched shard. An adopted process leaves no
        waitable handle, so success is inferred instead from the driver's
        unconditional ``INDUCTION STUDY RUN COMPLETE`` log line (``0`` if
        present, ``1`` otherwise); an unreadable log therefore reads as a
        non-zero exit, costing a bounded relaunch rather than risking a run
        recorded as finished that may not be.
        """
        if self.proc is not None:
            return self.proc.poll()
        try:
            tail = self.log.read_text(errors="replace")[-4000:]
        except OSError:
            tail = ""
        return 0 if "INDUCTION STUDY RUN COMPLETE" in tail else 1

    def launch(self) -> None:
        """Start the driver for this shard, appending to its log.

        Opens the log in APPEND mode, so a relaunch adds to the shard's
        history instead of truncating the evidence of why the previous
        attempt died, and starts the child in its own session
        (``start_new_session=True``) so a signal to the supervisor's process
        group doesn't also kill a run hours into a paid GPU box. Clears
        `adopted_pid`: this process now owns a real handle and must stop
        consulting ``/proc``.
        """
        self.log.parent.mkdir(parents=True, exist_ok=True)
        with self.log.open("ab") as sink:
            self.proc = subprocess.Popen(
                [str(self.python), "-u", str(self.driver)],
                stdout=sink, stderr=subprocess.STDOUT,
                # A copy: must not mutate an env object the caller may still
                # hold or share between shards.
                env=dict(self.env),
                cwd=str(self.cwd), start_new_session=True,
            )
        self.adopted_pid = None
        self.status = "running"
        logging.info(f"shard {self.index}: launched pid {self.proc.pid}")
