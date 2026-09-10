"""Supervision state for one direct ``run_study.py`` shard."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional


@dataclass
class Shard:
    """One shard of a direct ``run_study.py`` run, and its supervision state.

    A shard is launched (``proc``) or adopted (``adopted_pid``), never both.
    Adopted PID reuse can falsely report liveness; identity matching requires
    ``/proc/<pid>/environ``; ``launch`` clears ``adopted_pid`` because it owns a real handle.
    ``selector`` is the ``"i/n"`` value ``find_adoptable`` matches, or meaningful
    ``None`` for an unsharded run. ``env`` is the complete child environment, not
    a parent overlay; ``state_file`` is not read here but lets
    ``run_shards.terminate_shard_box`` reclaim the box from this shard alone.
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

        Adopted shards use PID existence and may suffer PID reuse.
        """
        if self.proc is not None:
            return self.proc.poll() is None
        if self.adopted_pid is not None:
            return Path(f"/proc/{self.adopted_pid}").exists()
        return False

    def returncode(self) -> Optional[int]:
        """Return this shard's exit status, inferring it for an adopted process.

        Adopted processes infer success from the completion line; an unreadable
        log fails, preferring a bounded relaunch to a false completed run.
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

        Append preserves prior failure evidence. A new session prevents a
        supervisor-group signal from killing a paid GPU run. Clear ``adopted_pid``
        because this process now owns a real handle and must stop consulting ``/proc``.
        """
        self.log.parent.mkdir(parents=True, exist_ok=True)
        with self.log.open("ab") as sink:
            self.proc = subprocess.Popen(
                [str(self.python), "-u", str(self.driver)],
                stdout=sink, stderr=subprocess.STDOUT,
                # Copy the environment; never mutate an object the caller may
                # still hold or share between shards.
                env=dict(self.env),
                cwd=str(self.cwd), start_new_session=True,
            )
        self.adopted_pid = None
        self.status = "running"
        logging.info(f"shard {self.index}: launched pid {self.proc.pid}")
