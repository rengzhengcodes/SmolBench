"""Drive a Lean 4 REPL session for one theorem via `lean_interact`.

Sessions restore imports, not file-level `open`/`variable`/`namespace` scope, so dependent
statements fail as ``"exception"``; restoring a file prefix costs more than that coverage.
Text processing was measured against mathlib4 at the corpus commit; REPL calls use fakes.
`verify` uses `module_name`, `declaration_text`, `rename_declaration`, and
`theorem_statement_stub`; `ReplSession.step` uses `classify_step`.
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, Literal

from lean_interact import Command, LeanREPLConfig, LeanServer, LocalProject, ProofStep
from lean_interact.interface import LeanError
from smolbench.deduction.lean.corpus import BenchmarkTheorem

logger = logging.getLogger(__name__)


#: REPL declaration name; the original already exists in its imported module.
TARGET_NAME: str = "smolbenchTarget"

#: Mathlib4 checkout, read at call time so late environment changes take effect.
MATHLIB_ROOT_ENV: str = "SMOLBENCH_MATHLIB_ROOT"


class ReplError(Exception):
    """REPL infrastructure failure, not a Lean verdict.

    This is not `RuntimeError`, which `verify.verify_proof_tail` maps to corpus claim
    ``"replay_failed"``; REPL failures must remain ``"exception"``.
    """


class StatementError(ReplError):
    """Deterministic failure to obtain a statement proof state.

    `open_session` retries transient server/import failures but never stub elaboration: attempt
    3 repeats attempt 1 under the same import-only environment. It remains ``"exception"``.
    """


@dataclass(frozen=True)
class StepOutcome:
    """Normalized result of one tactic.

    Field order is contractual because callers construct instances positionally.
    """

    #: Whole proof, Lean rejection, remaining goals, `sorry`, or REPL failure.
    kind: Literal["success", "lean_error", "incomplete", "given_up", "exception"]
    #: Next proof-state id; None after rejection or REPL failure.
    proof_state: int | None
    #: Lean or REPL message; never empty when set.
    error: str | None
    #: ``"\\n\\n"``-joined remaining goals, only for ``"incomplete"``.
    goals_pp: str | None


def module_name(file_path: str) -> str:
    """Convert a corpus ``file_path`` into the Lean module name to ``import``.

    Parameters
    ----------
    file_path : str
        Repo-relative, ``/``-separated path (e.g. ``Mathlib/Algebra/Group/Basic.lean``).

    Returns
    -------
    str
        Lean module name.

    Raises
    ------
    ValueError
        Empty or non-``.lean`` path, named before an untraceable REPL import error.
    """
    if not file_path or not file_path.endswith(".lean"):
        raise ValueError(f"not a Lean source path (expected a '.lean' suffix): {file_path!r}")
    return file_path[: -len(".lean")].replace("/", ".")


def mathlib_root(root: str | Path | None = None) -> Path:
    """Resolve the mathlib4 checkout the REPL should run inside.

    Read ``SMOLBENCH_MATHLIB_ROOT`` at call time so late configuration works; preserve symlinks
    because callers compare literal paths and Lean works through them. Validate before REPL startup.

    Parameters
    ----------
    root : str | Path | None, optional
        Checkout path overriding the environment.

    Returns
    -------
    Path
        Configured mathlib4 checkout.

    Raises
    ------
    RuntimeError
        Missing configuration, invalid directory, or missing ``lean-toolchain``, in that order.
    """
    # Avoid freezing a long-lived process's environment at import time.
    configured = root if root is not None else os.getenv(MATHLIB_ROOT_ENV)
    if not configured:
        raise RuntimeError(
            f"no mathlib4 checkout configured: set {MATHLIB_ROOT_ENV} to a mathlib4 "
            "checkout that has been built with elan/lake (the directory containing "
            "'lean-toolchain' and 'lakefile.lean'), or pass root= explicitly"
        )

    path = Path(configured)
    if not path.is_dir():
        raise RuntimeError(
            f"{MATHLIB_ROOT_ENV} does not point at an existing directory: {path}"
        )
    if not (path / "lean-toolchain").is_file():
        raise RuntimeError(
            f"{path} does not look like a Lean project: no 'lean-toolchain' file. "
            f"Point {MATHLIB_ROOT_ENV} at a mathlib4 checkout built with elan/lake."
        )
    return path


#: Lean brackets, including ``⟨⟩`` and ``⁅⁆``, can wrap a ``:=``.
_OPEN_BRACKETS = "([{⟨⁅"
_CLOSE_BRACKETS = ")]}⟩⁆"

#: Identifier terminators besides whitespace.
_IDENT_TERMINATORS = ":({[⦃⟨"

#: Renameable declarations; ``def`` has no tactic proof to slice.
_DECLARATION_KEYWORDS = ("theorem", "lemma")

#: Identifier continuations prevent partial keyword matches.
_IDENT_CHARS = re.compile(r"[A-Za-z0-9_'.!?]")


def _iter_code_positions(text: str) -> Iterator[int]:
    """Yield, in order, the index of every character of `text` outside a comment.

    Indices address the original text because callers slice it. The first ``-/`` closes because
    mathlib4 declaration headers do not nest block comments.

    Parameters
    ----------
    text : str
        Lean source.

    Yields
    ------
    int
        Non-comment character index.
    """
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("/-", i):
            end = text.find("-/", i + 2)
            i = n if end == -1 else end + 2
            continue
        if text.startswith("--", i):
            end = text.find("\n", i)
            i = n if end == -1 else end + 1
            continue
        yield i
        i += 1


def find_statement_end(text: str) -> int | None:
    """Index of the ``:=`` that separates a declaration's statement from its proof.

    Use the first depth-0, non-comment ``:=``: `autoParam` (e.g. `Basis.reindexFinsetRange_self`)
    and comments contain ``:=`` too.
    Across 300 pinned theorems it found 228 of 229 applicable boundaries; ``Filter.bot_pow``
    is equation-style, has no traced tactics, and is never verified.

    Parameters
    ----------
    text : str
        Declaration source.

    Returns
    -------
    int | None
        Depth-0 non-comment boundary, if present.
    """
    depth = 0
    for i in _iter_code_positions(text):
        ch = text[i]
        if ch in _OPEN_BRACKETS:
            depth += 1
        elif ch in _CLOSE_BRACKETS:
            # A mid-expression slice can start with a closer; negative depth hides later ``:=``.
            depth = max(depth - 1, 0)
        elif depth == 0 and ch == ":" and text.startswith(":=", i):
            return i
    return None


def rename_declaration(text: str, target_name: str = TARGET_NAME) -> str:
    """Rewrite a declaration's identifier to `target_name`, leaving all else intact.

    Rename because `open_session` imports the original. Use `_iter_code_positions`, not regex:
    213 of 106,445 mathlib4 declarations have a preceding docstring matching a declaration;
    regex would silently rename it. Preserve leading text byte-identically; reject ``def``.

    Parameters
    ----------
    text : str
        Declaration source.
    target_name : str, optional
        Replacement identifier.

    Returns
    -------
    str
        Source with a rewritten identifier.

    Raises
    ------
    ValueError
        Missing renameable declaration or identifier; quotes a source prefix.
    """
    n = len(text)
    for i in _iter_code_positions(text):
        keyword = next((kw for kw in _DECLARATION_KEYWORDS if text.startswith(kw, i)), None)
        if keyword is None:
            continue
        # Avoid partial keyword matches such as `mytheorem`.
        if i > 0 and _IDENT_CHARS.match(text[i - 1]):
            continue
        after = i + len(keyword)
        if after < n and _IDENT_CHARS.match(text[after]):
            continue

        start = after
        while start < n and text[start].isspace():
            start += 1
        end = start
        while end < n and not text[end].isspace() and text[end] not in _IDENT_TERMINATORS:
            end += 1
        if end == start:
            raise ValueError(
                f"{keyword!r} keyword is not followed by an identifier in: {text[:120]!r}"
            )
        return text[:start] + target_name + text[end:]

    raise ValueError(
        "no 'theorem'/'lemma' declaration keyword outside a comment in: " f"{text[:120]!r}"
    )


#: Column-0 keywords that end a declaration slice, including scope markers.
_TOP_LEVEL_KEYWORDS = frozenset(
    {
        "theorem", "lemma", "def", "instance", "abbrev", "structure", "class",
        "inductive", "namespace", "end", "section", "open", "variable",
        "noncomputable", "protected", "private", "nonrec", "universe", "attribute",
        "example", "macro", "syntax", "notation", "deriving", "alias", "set_option",
        "import",
    }
)

#: Declaration openers; ``set_option maxHeartbeats 400000 in`` can begin a header, so scope
#: commands must not arm the stop rule.
_DECLARATION_OPENERS = frozenset(
    {
        "theorem", "lemma", "def", "instance", "abbrev", "structure", "class",
        "inductive", "example", "macro", "syntax", "notation", "alias",
    }
)

#: Same-line declaration modifiers.
_DECLARATION_MODIFIERS = frozenset(
    {"private", "protected", "noncomputable", "nonrec", "partial", "unsafe", "scoped", "local"}
)

_LEADING_ATTRIBUTE = re.compile(r"^@\[[^\]]*\]\s*")
_LEADING_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_']*")


def _starts_top_level(line: str) -> bool:
    """True when `line` begins, at column 0, something outside the current slice."""
    if not line or line[0].isspace():
        return False
    if line.startswith("@[") or line.startswith("/--"):
        return True
    word = _LEADING_WORD.match(line)
    return word is not None and word.group(0) in _TOP_LEVEL_KEYWORDS


def _opens_a_declaration(line: str) -> bool:
    """True when `line` is the declaration's own keyword line (`theorem`/`def`/...).

    Strip attributes and same-line modifiers first, so ``protected theorem Foo.bar`` and
    ``@[simp] lemma baz`` count.

    Parameters
    ----------
    line : str
        Source line.

    Returns
    -------
    bool
        Whether the line opens a declaration.
    """
    if not line or line[0].isspace():
        return False
    rest = _LEADING_ATTRIBUTE.sub("", line)
    tokens = rest.split()
    idx = 0
    while idx < len(tokens) and tokens[idx] in _DECLARATION_MODIFIERS:
        idx += 1
    if idx >= len(tokens):
        return False
    word = _LEADING_WORD.match(tokens[idx])
    return word is not None and word.group(0) in _DECLARATION_OPENERS


def _advance_comment_state(line: str, in_comment: bool) -> bool:
    """Return whether a ``/- ... -/`` block is still open at the end of `line`.

    The first ``-/`` closes because nested blocks are not tracked; ``--`` ends its line.

    Parameters
    ----------
    line : str
        Source line.
    in_comment : bool
        Prior block-comment state.

    Returns
    -------
    bool
        Block-comment state after the line.
    """
    i = 0
    n = len(line)
    while i < n:
        if in_comment:
            if line.startswith("-/", i):
                in_comment = False
                i += 2
                continue
        else:
            if line.startswith("--", i):
                break  # rest of the line is a line comment; block state unchanged
            if line.startswith("/-", i):
                in_comment = True
                i += 2
                continue
        i += 1
    return in_comment


def declaration_text(root: Path, file_path: str, start_line: int, max_lines: int = 400) -> str:
    """Slice one declaration's source out of ``root / file_path``.

    `start_line` is 1-indexed to match `premises.slice_full_decl`; ignore `BenchmarkTheorem.start`'s
    untested column, which can point into a docstring or attribute, and scan forward from the line. Stop only
    at the next column-0 top-level line (including ``@[`` and ``/--``)
    after the declaration opener, so leading attributes/docstrings remain in the slice; block
    comments never stop it.

    Parameters
    ----------
    root : Path
        Mathlib4 checkout root.
    file_path : str
        Corpus Lean source path.
    start_line : int
        1-indexed slice start.
    max_lines : int, optional
        Maximum 400 lines so a missing stop keyword cannot consume a file.

    Returns
    -------
    str
        Declaration source.

    Raises
    ------
    FileNotFoundError
        Missing source, named by corpus path.
    ValueError
        `start_line` below 1 or past EOF.
    """
    source = Path(root) / file_path
    if not source.is_file():
        raise FileNotFoundError(f"no such Lean source: {file_path} (looked in {root})")

    lines = source.read_text(encoding="utf-8").splitlines()
    if start_line < 1:
        raise ValueError(f"start_line must be >= 1 (1-indexed), got {start_line}")
    if start_line > len(lines):
        # `start_line == len(lines)` is the legitimate final line.
        raise ValueError(
            f"start_line {start_line} is past the end of {file_path} ({len(lines)} lines)"
        )

    collected: list[str] = []
    armed = False
    in_comment = False
    for offset, line in enumerate(lines[start_line - 1 : start_line - 1 + max_lines]):
        if armed and not in_comment and offset > 0 and _starts_top_level(line):
            break
        collected.append(line)
        in_comment = _advance_comment_state(line, in_comment)
        if not in_comment and _opens_a_declaration(line):
            # Arm after appending so the opener remains in the slice.
            armed = True
    return "\n".join(collected).rstrip()


def theorem_statement_stub(
    bt: BenchmarkTheorem,
    root: Path | None = None,
    target_name: str = TARGET_NAME,
) -> str:
    """Build the ``:= by sorry`` stub whose ``sorry`` opens `bt`'s proof state.

    Elaborate ``sorry`` because the REPL has no goal-by-declaration request; its response carries
    the `Sorry` ``proofState`` tactics branch from.

    Parameters
    ----------
    bt : BenchmarkTheorem
        Theorem to stub.
    root : Path | None, optional
        Mathlib4 checkout root.
    target_name : str, optional
        Replacement identifier.

    Returns
    -------
    str
        Statement ending in ``:= by sorry``.

    Raises
    ------
    StatementError
        Missing top-level ``:=``; `open_session` must not retry this deterministic failure.
    ValueError
        No renameable declaration.
    FileNotFoundError
        Missing source.
    """
    # Module-level lookup lets tests and future backends monkeypatch it.
    text = declaration_text(mathlib_root(root), bt.file_path, bt.start[0])

    # No ``:=`` means a term/equation-style proof with no state boundary.
    end = find_statement_end(text)
    if end is None:
        raise StatementError(
            f"cannot open a proof state for {bt.full_name}: its declaration has no "
            "top-level ':=' (term-mode or equation-style proof), so there is no "
            "statement/proof boundary to cut at"
        )

    return f"{rename_declaration(text[:end], target_name).rstrip()}\n  := by sorry"


def classify_step(response: Any) -> StepOutcome:
    """Map one `lean_interact` reply onto a `StepOutcome`.

    Branch order defines the evaluation taxonomy. `LeanServer.run` returns `LeanError` rather
    than raising for ``{"message": ...}``; errors are never empty for failure outcomes.

    Parameters
    ----------
    response : Any
        `lean_interact` reply.

    Returns
    -------
    StepOutcome
        Normalized tactic outcome.
    """
    # `LeanError` is infrastructure, not a rejected tactic, or `lean_error` inflates.
    if isinstance(response, LeanError):
        return StepOutcome("exception", None, f"REPL error: {response.message}", None)

    status = response.proof_status or ""

    # Check `sorry` before completion or a contaminated proof scores as success.
    if response.sorries or "sorry" in status.lower():
        return StepOutcome("given_up", None, None, None)

    # Warnings never reject a tactic: `get_errors()` selects severity ``"error"``.
    errors = response.get_errors()
    if errors or status.startswith("Error"):
        message = "\n".join(msg.data for msg in errors)
        return StepOutcome(
            "lean_error",
            None,
            # Blank results-row errors are indistinguishable from classifier bugs.
            message or f"Lean reported proof status {status!r} with no error message",
            None,
        )

    # `proofStatus`, not empty goals, is authoritative; sibling goals can remain.
    if status.startswith("Completed"):
        return StepOutcome("success", response.proof_state, None, None)

    goals_pp = "\n\n".join(response.goals) if response.goals else None
    return StepOutcome("incomplete", response.proof_state, None, goals_pp)


@dataclass
class ReplSession:
    """Live REPL process for one theorem with a request timeout.

    `verify` owns verdict policy; this translates transport failures to `ReplError`.
    """

    #: Server-like object; structural typing permits fake, pooled, or remote backends.
    server: object
    #: Per-request seconds; None disables the timeout.
    timeout: int | None
    #: Theorem name, used only to attribute error messages.
    theorem: str

    def run(self, request: Any) -> Any:
        """Send one request, translating transport failures into `ReplError`.

        Translate timeout (which kills the server) and closed-pipe failures so `runner.py` records
        greppable ``timeout:`` errors without a seventh verdict; return `LeanError` values.

        Parameters
        ----------
        request : Any
            Lean server request.

        Returns
        -------
        Any
            Server reply.
        """
        try:
            return self.server.run(request, timeout=self.timeout)
        except TimeoutError as exc:
            raise ReplError(f"timeout after {self.timeout}s on {self.theorem}: {exc}") from exc
        except BrokenPipeError as exc:
            raise ReplError(f"REPL closed on {self.theorem}: {exc}") from exc

    def step(self, proof_state: int, tactic: str) -> StepOutcome:
        """Apply `tactic` at `proof_state` and classify the reply.

        Proof states are immutable, so calls may branch from one id; callers must not split
        combinators (``;``, ``<;>``).

        Parameters
        ----------
        proof_state : int
            Proof-state id.
        tactic : str
            Lean tactic.

        Returns
        -------
        StepOutcome
            Classified tactic result.

        Raises
        ------
        ReplError
            Transport or REPL-channel failure, never silently recorded as a Lean verdict.
        """
        outcome = classify_step(self.run(ProofStep(proof_state=proof_state, tactic=tactic)))
        if outcome.kind == "exception":
            raise ReplError(outcome.error or "REPL-level failure with no message")
        return outcome

    def close(self) -> None:
        """Kill the REPL process. Safe to call more than once.

        Swallow only kill failures because `finally` teardown must not mask the real error.
        """
        try:
            self.server.kill()
        except Exception as exc:  # noqa: BLE001 - teardown must not mask the real error
            logger.debug("killing the REPL for %s failed: %s", self.theorem, exc)


#: Retry concurrent-start build-cache races; reopening usually succeeds within seconds.
_REPL_OPEN_RETRIES = 3
#: Two delays serve three attempts; the final attempt raises.
_REPL_OPEN_BACKOFF_S = (5.0, 15.0)


def _default_server_factory(root: Path) -> LeanServer:
    """Start a `LeanServer` on the mathlib4 checkout at `root`.

    Keep this seam so fake, pooled, and remote servers can replace it without changing retry
    logic. `LeanServer.__init__` validates config and starts the process, so this returns a live
    server or raises.

    Parameters
    ----------
    root : Path
        Mathlib4 checkout.

    Returns
    -------
    LeanServer
        Started server.
    """
    return LeanServer(LeanREPLConfig(project=LocalProject(directory=str(root))))


def _describe(response: Any) -> str:
    """Render a REPL reply's messages verbatim, for an actionable `ReplError`."""
    if isinstance(response, LeanError):
        return response.message
    return "\n".join(f"[{msg.severity}] {msg.data}" for msg in response.messages)


def open_session(
    bt: BenchmarkTheorem,
    timeout: int = 600,
    root: str | Path | None = None,
    server_factory: Callable[[Path], object] | None = None,
) -> tuple[ReplSession, int]:
    """Start a REPL, elaborate `bt`'s statement as a stub, return its proof state.

    Resolve configuration and derive the statement before startup so deterministic failures cost
    milliseconds. Retry server startup and ``import``, never `StatementError` elaboration.

    Parameters
    ----------
    bt : BenchmarkTheorem
        Theorem to open.
    timeout : int, optional
        Per-request seconds.
    root : str | Path | None, optional
        Mathlib4 checkout root.
    server_factory : Callable[[Path], object] | None, optional
        Started server factory, defaulting to `_default_server_factory`.

    Returns
    -------
    tuple[ReplSession, int]
        Live session and stub proof-state id, where tactic 0 applies.

    Raises
    ------
    ReplError
        Misconfiguration, failed server start, or failed import; never bare `RuntimeError`.
    StatementError
        Missing statement boundary or failed stub elaboration; not retried.
    """
    # Translate here: `verify.verify_proof_tail` maps `RuntimeError` to the false corpus claim
    # ``"replay_failed"``, while direct `mathlib_root` callers need its native error.
    try:
        resolved_root = mathlib_root(root)
    except RuntimeError as exc:
        raise ReplError(str(exc)) from exc

    stub = theorem_statement_stub(bt, resolved_root)
    module = module_name(bt.file_path)
    factory = server_factory or _default_server_factory

    last_exc: Exception | None = None
    for attempt in range(_REPL_OPEN_RETRIES):
        session: ReplSession | None = None
        try:
            session = ReplSession(
                server=factory(resolved_root), timeout=timeout, theorem=bt.full_name
            )
            return session, _open_proof_state(session, bt, module, stub)
        except StatementError:
            # Deterministic; kill first so this terminal path leaves no Lean process.
            if session is not None:
                session.close()
            raise
        except Exception as exc:  # noqa: BLE001 - retried below, or re-raised
            # Each failed attempt must leave no Lean process.
            if session is not None:
                session.close()
            last_exc = exc
            if attempt + 1 < _REPL_OPEN_RETRIES:
                time.sleep(_REPL_OPEN_BACKOFF_S[attempt])
    assert last_exc is not None
    raise last_exc


def _open_proof_state(
    session: ReplSession,
    bt: BenchmarkTheorem,
    module: str,
    stub: str,
) -> int:
    """Import `module`, elaborate `stub` in it, and return the ``sorry``'s state id.

    Import in a fresh environment (``env=None``), then elaborate the stub in its result.

    Parameters
    ----------
    session : ReplSession
        Active REPL session.
    bt : BenchmarkTheorem
        Theorem to elaborate.
    module : str
        Lean module.
    stub : str
        Statement stub.

    Returns
    -------
    int
        Elaborated stub ``sorry`` state id.

    Raises
    ------
    ReplError
        Failed import, including a cold/racing ``lake`` build cache.
    StatementError
        Unelaborated stub or missing ``sorry``; preserve REPL text to explain exception rows.
    """
    imported = session.run(Command(cmd=f"import {module}"))
    if isinstance(imported, LeanError) or imported.get_errors():
        raise ReplError(f"could not import {module} for {bt.full_name}: {_describe(imported)}")

    elaborated = session.run(Command(cmd=stub, env=imported.env))
    if isinstance(elaborated, LeanError) or elaborated.get_errors() or not elaborated.sorries:
        raise StatementError(
            f"could not elaborate the statement of {bt.full_name} in module {module}: "
            f"{_describe(elaborated) or 'no sorry in the response'}\n--- stub ---\n{stub}"
        )

    proof_state = elaborated.sorries[0].proof_state
    if proof_state is None:
        raise StatementError(
            f"the stub for {bt.full_name} elaborated to a sorry with no proofState; "
            "no proof state can be branched from it"
        )
    return proof_state
