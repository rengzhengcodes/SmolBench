"""One supervised shard of a direct ``notebooks/induction/run_study.py`` run.

`Shard` is the unit ``scripts/fleet/run_shards.py`` supervises: one child
process, its log file, its EC2 state file and the counters the shared restart
policy (``scripts/fleet/policy.py``) needs. It used to be declared INSIDE
``run_shards.main()``, closing over that function's ``args`` namespace, which
meant it could only be built by parsing a command line -- so nothing could
construct one to drive the supervision loop, and every field it read was
invisible in its own definition. Lifting it here with an explicit constructor
makes each of those fields a named parameter and leaves ``run_shards.main()``
holding only argument parsing and the derivations that turn ``args`` into
these parameters.

It is loaded BY FILE PATH, never a bare ``import shards``: ``scripts/fleet``
has no ``__init__.py`` -- it is not a package -- so a bare import name is
absent from ``sys.path`` for a script launched from an arbitrary working
directory. See ``_config.load_fleet_module``, the loader every fleet consumer
now calls.
"""

from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path
from typing import Mapping, Optional


class Shard:
    """One shard of a direct ``run_study.py`` run, and its supervision state.

    A shard is either LAUNCHED by this process (``proc`` holds a
    ``subprocess.Popen``) or ADOPTED from an already-running process found by
    ``run_shards.find_adoptable`` (``adopted_pid`` holds its pid); never both,
    and `launch` clears ``adopted_pid`` when it takes over.

    Parameters
    ----------
    index : int
        Shard index, ``0 <= index < count``. Used only for logging and for the
        state-file/log names the caller has already derived.
    selector : str or None
        The ``INDUCTION_SHARD`` selector ``"i/n"``, or ``None`` for an
        unsharded (``--no-shard``) run. This is the value
        ``run_shards.find_adoptable`` matches a live process's environment
        against, so ``None`` is meaningful -- an unsharded run's environment
        genuinely has no ``INDUCTION_SHARD`` -- and is not a "missing" value.
    log : Path
        This shard's log FILE (not its directory). `launch` appends to it and
        `returncode` reads its tail. The caller derives the name; this class
        does not know the model or shard-count naming scheme.
    env : Mapping[str, str]
        The COMPLETE child environment (what ``run_shards.shard_env`` returns:
        the supervisor's own inherited environment plus the per-shard
        variables), not an overlay on the parent's.
    state_file : Path
        This shard's EC2 state file (what ``run_shards.state_file_for``
        returns). Not read here; carried so ``run_shards.terminate_shard_box``
        can reclaim the box from the shard alone.
    python : Path
        Interpreter to launch the driver with.
    driver : Path
        The driver script, ``notebooks/induction/run_study.py``.
    cwd : Path
        Working directory for the child (the repo root).

    Attributes
    ----------
    proc : subprocess.Popen or None
        The child this process launched, or ``None`` if adopted / not yet
        launched.
    adopted_pid : int or None
        The pid of an already-running shard this supervisor took over.
    launched_at : float
        ``time.time()`` of the most recent launch, or of adoption (whose true
        start is unknowable, so adoption uses "now", the conservative choice).
        ``0.0`` before either. Launch PROVENANCE only: nothing in the restart
        path reads it any more, because the shared policy counts relaunches
        rather than timing them. Its former reader was the deleted
        fast-crash-window test, whose age comparison is exactly what let a
        slow crash loop escape the halt.
    status : str
        One of ``"pending"``, ``"running"``, ``"done"``, ``"halted"``.
    crash_relaunches : int
        Relaunches this shard has had on a ``"crash"`` verdict.
    reclaim_relaunches : int
        Relaunches this shard has had on a ``"reclaim"`` verdict.

    Notes
    -----
    The two counters exist because ``policy.decide_relaunch`` takes the
    POST-increment attempt number: the supervisor bumps the counter matching
    the verdict and passes it straight in. They replace the old
    consecutive-fast-crash counter, which RESET on any slow crash and so could
    never stop a crash loop whose iterations happened to be slow.

    Known limitation (out of scope here): `alive` tests an ADOPTED shard's
    liveness with a ``/proc/<pid>`` existence check, and a pid is a recycled
    resource. If the adopted process dies and the operating system later hands
    the same pid to an unrelated process, this shard reads as alive forever and
    is never relaunched. Closing that needs a stronger identity than the pid --
    the process start time from ``/proc/<pid>/stat``, or matching
    ``/proc/<pid>/environ`` the way ``run_shards.find_adoptable`` does -- which
    is a behaviour change beyond lifting this class out of ``main()``, so it is
    named here rather than left silently in the code.
    """

    def __init__(
        self,
        index: int,
        selector: Optional[str],
        log: Path,
        env: Mapping[str, str],
        state_file: Path,
        python: Path,
        driver: Path,
        cwd: Path,
    ) -> None:
        self.index = index
        self.selector = selector
        self.log = log
        self.env = env
        self.state_file = state_file
        self.python = python
        self.driver = driver
        self.cwd = cwd
        self.proc: Optional[subprocess.Popen] = None
        self.adopted_pid: Optional[int] = None
        self.launched_at = 0.0
        self.status = "pending"  # pending|running|done|halted
        self.crash_relaunches = 0
        self.reclaim_relaunches = 0

    def alive(self) -> bool:
        """Report whether this shard's process is still running.

        Returns
        -------
        bool
            For a launched shard, whether ``proc.poll()`` is still ``None``.
            For an adopted one, whether ``/proc/<adopted_pid>`` still exists
            (see the class docstring on pid recycling). ``False`` for a shard
            that has neither -- one that is pending, done or halted.
        """
        if self.proc is not None:
            return self.proc.poll() is None
        if self.adopted_pid is not None:
            return Path(f"/proc/{self.adopted_pid}").exists()
        return False

    def returncode(self) -> Optional[int]:
        """Return this shard's exit status, inferring it for an adopted process.

        Returns
        -------
        int or None
            ``proc.poll()`` for a launched shard -- ``None`` while it is still
            running. For an adopted one, ``0`` if the driver's completion line
            is in the log tail and ``1`` otherwise.

        Notes
        -----
        Adopted processes leave no waitable handle. Infer success from the
        driver's unconditional ``INDUCTION STUDY RUN COMPLETE`` line instead.
        An unreadable log reads as a non-zero exit, which is the safe side:
        it costs a relaunch (bounded by the shared policy) rather than
        recording a run as finished that may not be.
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

        Creates the log's parent directory if needed, opens the log in APPEND
        mode -- so a relaunch adds to the shard's history rather than
        truncating the evidence of why the previous attempt died -- and starts
        the child in its own session (``start_new_session=True``) so a signal
        sent to the supervisor's process group does not also kill a run that
        may be hours into a paid GPU box.

        Side effects
        ------------
        Creates ``log.parent``, appends to `log`, spawns a process, and sets
        `proc`, `launched_at` and `status`; clears `adopted_pid`, because this
        process now owns a real handle and must stop consulting ``/proc``.
        """
        self.log.parent.mkdir(parents=True, exist_ok=True)
        with self.log.open("ab") as sink:
            self.proc = subprocess.Popen(
                [str(self.python), "-u", str(self.driver)],
                stdout=sink, stderr=subprocess.STDOUT,
                # A COPY of the mapping: Popen is handed the environment the
                # caller composed, but a shard must not be able to mutate the
                # object a caller may still hold or share between shards.
                env=dict(self.env),
                cwd=str(self.cwd), start_new_session=True,
            )
        self.adopted_pid = None
        self.launched_at = time.time()
        self.status = "running"
        logging.info(f"shard {self.index}: launched pid {self.proc.pid}")
