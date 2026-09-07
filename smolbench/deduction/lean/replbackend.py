"""Drive a Lean 4 REPL session for one theorem, via `lean_interact`.

The Lean-side backend `smolbench.deduction.lean.verify` sits on top of: locate the
theorem's source (`declaration_text`), cut the statement off its proof and rename it
(`rename_declaration`, `theorem_statement_stub`), elaborate a `:= by sorry` stub for a proof
state (`open_session`), then send tactics at it (`ReplSession.step`, `classify_step`).

`open_session`'s environment is import-only: it restores the module's imports but not its
file-level `open`/`variable`/`namespace` scope, so a statement depending on that scope fails
to elaborate (`ReplError`, reported as ``"exception"``). Re-elaborating the whole file
prefix would avoid this but cost much more; the spec chose cost over completeness.

Untested against a real Lean toolchain (none on the dev box) -- exercised only against
scripted fakes, except the pure text-processing functions (`find_statement_end`,
`rename_declaration`, `declaration_text`, `module_name`), which were measured against a
real mathlib4 checkout at the corpus commit.
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


#: Name every theorem statement is re-declared under before it is sent to the
#: REPL. See `rename_declaration` for why a rename is mandatory rather than
#: cosmetic.
TARGET_NAME: str = "smolbenchTarget"

#: Environment variable naming the mathlib4 checkout to run the REPL against.
#: Read at CALL time by `mathlib_root`, never cached at import, so a test or a
#: late ``os.environ`` assignment takes effect.
MATHLIB_ROOT_ENV: str = "SMOLBENCH_MATHLIB_ROOT"


class ReplError(Exception):
    """A REPL-level (infrastructure) failure: no Lean verdict was obtained.

    Deliberately not a `RuntimeError`: `verify.verify_proof_tail` maps `RuntimeError` to
    verdict ``"replay_failed"`` (the recorded ground-truth prefix doesn't replay), a claim
    about the corpus. A dead REPL, timeout, or unelaborable statement says nothing about the
    corpus and must land on ``"exception"`` instead.
    """


class StatementError(ReplError):
    """A DETERMINISTIC failure to obtain a proof state for a theorem's statement.

    Raised when the declaration has no statement/proof boundary to cut at, or the resulting
    stub does not elaborate. Splits `open_session`'s retry policy from `ReplError`: starting
    a server or importing a module is worth retrying (a cold/racing ``lake`` build cache
    fails transiently), but stub elaboration is deterministic -- attempt 3 fails exactly as
    attempt 1 did, so retrying it would only cost sleeps and process startups for a failure
    that, under this backend's import-only environment, is expected to be common. Still a
    `ReplError`, so existing handlers (`verify` reports it as ``"exception"``, never
    ``"replay_failed"``) need no change.
    """


@dataclass(frozen=True)
class StepOutcome:
    """What Lean did with one tactic, normalised away from `lean_interact` types.

    Field order is part of the contract: callers construct these positionally.
    """

    #: What happened. ``"success"`` (whole proof closed), ``"lean_error"``
    #: (Lean rejected the tactic), ``"incomplete"`` (tactic ran, goals remain),
    #: ``"given_up"`` (a ``sorry`` closed or contaminated the proof), or
    #: ``"exception"`` (the REPL itself failed -- see `classify_step`).
    kind: Literal["success", "lean_error", "incomplete", "given_up", "exception"]
    #: Proof-state id to branch the NEXT tactic from. None when there is no
    #: usable continuation (``"lean_error"``, ``"exception"``).
    proof_state: int | None
    #: Lean's message text (``"lean_error"``) or the REPL's message text
    #: (``"exception"``); None for every other kind. Never empty when set.
    error: str | None
    #: Remaining goals, ``"\\n\\n"``-joined, only for ``"incomplete"``; None
    #: otherwise (including an ``"incomplete"`` with an empty goal list).
    goals_pp: str | None


# ---------------------------------------------------------------------------
# Path / module-name plumbing
# ---------------------------------------------------------------------------


def module_name(file_path: str) -> str:
    """Convert a corpus ``file_path`` into the Lean module name to ``import``.

    `file_path` is repo-relative and always ``/``-separated (a LeanDojo trace value, not a
    host path), e.g. ``"Mathlib/Algebra/Group/Basic.lean"`` -> ``"Mathlib.Algebra.Group.Basic"``.

    Raises `ValueError` if `file_path` is empty or not ``.lean``-suffixed, naming the
    offending path: otherwise a bad path reaches the REPL as an ``import`` of a nonexistent
    module, and Lean's message for that doesn't mention the corpus row that produced it.
    """
    if not file_path or not file_path.endswith(".lean"):
        raise ValueError(f"not a Lean source path (expected a '.lean' suffix): {file_path!r}")
    return file_path[: -len(".lean")].replace("/", ".")


def mathlib_root(root: str | Path | None = None) -> Path:
    """Resolve the mathlib4 checkout the REPL should run inside.

    Resolution order: the `root` argument, else ``SMOLBENCH_MATHLIB_ROOT`` read AT CALL TIME
    (nothing cached, nothing read at import), so the variable can be set after this module
    is imported. Symlinks are NOT resolved: callers/tests compare against the literal path
    given, and a Lean project reached through a symlink works.

    Raises `RuntimeError` if nothing is configured, the path is missing/not a directory, or
    the directory has no ``lean-toolchain``, checked in that order so the "not a Lean
    project" diagnosis is only reached once the directory is known to exist. `open_session`
    runs this before starting any Lean process, so a misconfiguration costs milliseconds,
    not a REPL startup.
    """
    # Read here, not at module scope: a module-level os.getenv would freeze whatever value
    # was set at first import -- for a long-lived sweep process, that's "not yet configured".
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


# ---------------------------------------------------------------------------
# Lean source scanning
# ---------------------------------------------------------------------------

#: Bracket pairs `find_statement_end` counts. Beyond ASCII, Lean uses ``⟨⟩``
#: for anonymous constructors and ``⁅⁆`` for Lie brackets / interval notation,
#: both of which can legitimately wrap a ``:=``.
_OPEN_BRACKETS = "([{⟨⁅"
_CLOSE_BRACKETS = ")]}⟩⁆"

#: Characters that terminate a declaration's identifier token, in addition to
#: whitespace: binder openers and the type ascription colon.
_IDENT_TERMINATORS = ":({[⦃⟨"

#: Declaration keywords `rename_declaration` will rename. ``def`` is
#: deliberately absent: the corpus holds theorems, and a ``def`` has no tactic
#: proof to slice, so accepting one would quietly produce a nonsense stub.
_DECLARATION_KEYWORDS = ("theorem", "lemma")

#: Characters that may continue a Lean identifier. Used for the word-boundary
#: test around a keyword, so ``mytheorem`` / ``theorem_of`` / ``Foo.lemma`` are
#: not mistaken for the keyword itself.
_IDENT_CHARS = re.compile(r"[A-Za-z0-9_'.!?]")


def _iter_code_positions(text: str) -> Iterator[int]:
    """Yield, in order, the index of every character of `text` outside a comment.

    One left-to-right pass; indices are offsets into the ORIGINAL `text` (comments are
    skipped in-place, not stripped into a new string, since every caller needs to slice
    `text` at the index it gets back). Nested block comments are not supported -- the first
    ``-/`` closes -- since mathlib4 does not nest them in declaration headers.
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

    The boundary is the first ``:=`` at bracket depth 0 and outside any comment. Both
    exclusions are load-bearing, measured against the real mathlib4 checkout at the corpus
    commit: an ``autoParam`` default puts a ``:=`` inside parens
    (``theorem foo (h : Nat := by simp) : ...``, e.g. ``Basis.reindexFinsetRange_self``),
    and a doc/trailing comment routinely contains ``:=`` too.

    Over the 300 pinned corpus theorems, this rule found a boundary for 228 of the 229 it
    was applied to. The one miss, ``Filter.bot_pow``, is an equation-style proof with no
    ``:=`` at all; no heuristic rescues it, since it carries no traced tactics and is never
    verified.

    Returns None when no depth-0, non-comment ``:=`` exists.
    """
    depth = 0
    for i in _iter_code_positions(text):
        ch = text[i]
        if ch in _OPEN_BRACKETS:
            depth += 1
        elif ch in _CLOSE_BRACKETS:
            # Clamp at 0: a slice that starts mid-expression can open with a
            # closer, and going negative would make a later `:=` look nested.
            depth = max(depth - 1, 0)
        elif depth == 0 and ch == ":" and text.startswith(":=", i):
            return i
    return None


def rename_declaration(text: str, target_name: str = TARGET_NAME) -> str:
    """Rewrite a declaration's identifier to `target_name`, leaving all else intact.

    The environment already contains the original theorem (`open_session` imports its
    module), so re-declaring it under its own name raises Lean's "has already been
    declared" in the *modal* case, not an edge case -- renaming is mandatory.

    Uses the comment-aware scanner (`_iter_code_positions`), not a regex: 213 of
    mathlib4's 106,445 column-0 ``theorem``/``lemma`` declarations are preceded by a
    docstring containing the words "theorem <word>" or "lemma <word>", and a naive regex
    renames the docstring instead of the declaration -- a silent miss that only surfaces
    later as an "already declared" elaboration error.

    Leading attributes, modifiers, and any preceding docstring are returned byte-identical.
    ``def`` is not accepted (see `_DECLARATION_KEYWORDS`). Raises `ValueError` if no
    ``theorem``/``lemma`` keyword occurs outside a comment, or one occurs with no following
    identifier; the message quotes a truncated prefix of `text`.
    """
    n = len(text)
    for i in _iter_code_positions(text):
        keyword = next((kw for kw in _DECLARATION_KEYWORDS if text.startswith(kw, i)), None)
        if keyword is None:
            continue
        # Word boundaries on both sides, so `mytheorem`, `theorem_of` and
        # `Foo.lemma` are not mistaken for the keyword.
        if i > 0 and _IDENT_CHARS.match(text[i - 1]):
            continue
        after = i + len(keyword)
        if after < n and _IDENT_CHARS.match(text[after]):
            continue

        # The identifier is the next token: skip the separating whitespace,
        # then run to the first whitespace or binder/ascription opener.
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


#: Keywords that, at column 0, terminate `declaration_text`'s slice. Broader than
#: `_DECLARATION_KEYWORDS`: a slice must also stop at `end`/`namespace`/`open`/`section`
#: and friends, which aren't declarations but are unambiguously outside the current one.
_TOP_LEVEL_KEYWORDS = frozenset(
    {
        "theorem", "lemma", "def", "instance", "abbrev", "structure", "class",
        "inductive", "namespace", "end", "section", "open", "variable",
        "noncomputable", "protected", "private", "nonrec", "universe", "attribute",
        "example", "macro", "syntax", "notation", "deriving", "alias", "set_option",
        "import",
    }
)

#: Keywords that open a DECLARATION, as opposed to a command or scope marker. A strict
#: subset of `_TOP_LEVEL_KEYWORDS` and the arming set for `declaration_text`'s stop rule.
#: Excludes `set_option`/`open`/`namespace`/`variable`: those can legitimately appear in a
#: declaration's own header (`set_option maxHeartbeats 400000 in` above a theorem), and
#: arming on one would truncate the slice to the header.
_DECLARATION_OPENERS = frozenset(
    {
        "theorem", "lemma", "def", "instance", "abbrev", "structure", "class",
        "inductive", "example", "macro", "syntax", "notation", "alias",
    }
)

#: Modifiers that may precede the declaration keyword on the SAME line. Stripped
#: before asking whether a line opens a declaration (`_opens_a_declaration`).
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

    Attributes and same-line modifiers are stripped first, so
    ``protected theorem Foo.bar`` and ``@[simp] lemma baz`` both count.
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

    Nested blocks are not tracked (see `_iter_code_positions`); the first ``-/``
    closes. A ``--`` line comment outside a block ends the scan of the line.
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

    `start_line` is 1-indexed, matching `premises.slice_full_decl`'s convention for the same
    class of LeanDojo trace positions, so the two slicers agree. `BenchmarkTheorem.start`'s
    column is deliberately ignored: the corpus documents that field's indexing as untested,
    and a declaration's first line may be a docstring or attribute rather than the keyword,
    so the column could point into the wrong token anyway -- scanning forward from the line
    is the robust reading.

    The slice ends before the next column-0 line that starts something outside this
    declaration (`_TOP_LEVEL_KEYWORDS`, plus ``@[``/``/--``). That stop rule only arms once
    the declaration's own keyword line has been consumed, so a declaration whose first line
    is a docstring or attribute doesn't stop at its own ``theorem`` line and return only the
    header. Lines inside an open ``/- ... -/`` block never stop the slice. `max_lines`
    (default 400) caps the return so a missing stop keyword can't drag a whole file in.

    Raises `FileNotFoundError` (naming `file_path`, the corpus-side value) if the source is
    missing, or `ValueError` if `start_line` is below 1 or past the end of the file.
    """
    source = Path(root) / file_path
    if not source.is_file():
        raise FileNotFoundError(f"no such Lean source: {file_path} (looked in {root})")

    lines = source.read_text(encoding="utf-8").splitlines()
    if start_line < 1:
        raise ValueError(f"start_line must be >= 1 (1-indexed), got {start_line}")
    if start_line > len(lines):
        # `> len(lines)` rather than `>=`: start_line == len(lines) is the last
        # line and is legitimate.
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
            # Arm only AFTER appending, so the declaration's own keyword line
            # is always part of the slice -- true both when it is the start line
            # (`theorem foo ...` at start_line) and when a docstring/attribute
            # precedes it.
            armed = True
    return "\n".join(collected).rstrip()


def theorem_statement_stub(
    bt: BenchmarkTheorem,
    root: Path | None = None,
    target_name: str = TARGET_NAME,
) -> str:
    """Build the ``:= by sorry`` stub whose ``sorry`` opens `bt`'s proof state.

    The REPL has no "give me the goal of declaration X" request; the standard way to obtain
    a proof state is to elaborate a declaration whose proof is ``sorry`` -- the response
    then carries a `Sorry` entry with a ``proofState`` id tactics can branch from.

    Raises `StatementError` (a `ReplError` subclass, deterministic -- `open_session` must
    not retry it) if the declaration has no top-level ``:=`` (term-mode or equation-style
    proof), so there's no statement/proof boundary to open a state from. Also raises
    `ValueError` (`rename_declaration`, no renameable keyword) or `FileNotFoundError`
    (`declaration_text`, missing source).
    """
    # Step 1: source text. Called through the module-level name (not a local
    # alias / direct import) so tests and future backends can monkeypatch it.
    text = declaration_text(mathlib_root(root), bt.file_path, bt.start[0])

    # Step 2: cut the proof off. The slice still contains its proof, so "no
    # `:=`" means the proof is term/equation-style and unusable.
    end = find_statement_end(text)
    if end is None:
        raise StatementError(
            f"cannot open a proof state for {bt.full_name}: its declaration has no "
            "top-level ':=' (term-mode or equation-style proof), so there is no "
            "statement/proof boundary to cut at"
        )

    # Step 3/4: rename (the original is already in the environment) and stub.
    return f"{rename_declaration(text[:end], target_name).rstrip()}\n  := by sorry"


# ---------------------------------------------------------------------------
# Response classification
# ---------------------------------------------------------------------------


def classify_step(response: Any) -> StepOutcome:
    """Map one `lean_interact` reply onto a `StepOutcome`.

    The branch order is the taxonomy: reordering changes what the eval measures, and each
    branch is commented with why it sits where it does. `response` may be a
    `ProofStepResponse` or a `LeanError` -- `lean_interact.LeanServer.run` returns a
    `LeanError` rather than raising when the REPL's reply is exactly ``{"message": ...}``.
    `error` is never empty for ``"lean_error"``/``"exception"``.
    """
    # 1. REPL-level failure. `LeanError` is the REPL's own top-level channel (malformed
    #    request, unknown proof state, crashed process) -- infrastructure, not Lean
    #    rejecting the tactic. Getting this backwards inflates `lean_error` with infra
    #    outages.
    if isinstance(response, LeanError):
        return StepOutcome("exception", None, f"REPL error: {response.message}", None)

    status = response.proof_status or ""

    # 2. `sorry` before success: `Completed` WITH a sorry is sorry-shaped cheating (an LLM
    #    emitting `sorry`, or a tactic that leaves one behind) -- named `given_up` to match
    #    the old backend's `ProofGivenUp`. Checking success first would score it as a proof.
    if response.sorries or "sorry" in status.lower():
        return StepOutcome("given_up", None, None, None)

    # 3. Lean rejected the tactic. `get_errors()` filters on
    #    `severity == "error"`, so warnings (`unused variable`, deprecation)
    #    never count as a rejection.
    errors = response.get_errors()
    if errors or status.startswith("Error"):
        message = "\n".join(msg.data for msg in errors)
        return StepOutcome(
            "lean_error",
            None,
            # `error` must never be empty for this kind: a blank Lean error in a
            # results row is indistinguishable from a bug in this classifier.
            message or f"Lean reported proof status {status!r} with no error message",
            None,
        )

    # 4. Whole proof closed. Keyed on `proofStatus`, not `goals == []`: proofStatus is
    #    authoritative for the whole proof, while an empty `goals` list can coexist with
    #    unfinished sibling goals.
    if status.startswith("Completed"):
        return StepOutcome("success", response.proof_state, None, None)

    # 5. Otherwise the tactic ran and work remains.
    goals_pp = "\n\n".join(response.goals) if response.goals else None
    return StepOutcome("incomplete", response.proof_state, None, goals_pp)


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


@dataclass
class ReplSession:
    """A live REPL process pinned to one theorem, plus a per-request timeout.

    Thin by design: `verify` owns the verdict policy, this owns only the
    transport and the translation of transport failures into `ReplError`.
    """

    #: A `lean_interact.LeanServer`, or any object exposing ``run(request, *,
    #: timeout=...)`` and ``kill()``. Kept structurally typed so tests and a
    #: future pooled/remote backend can substitute one.
    server: object
    #: Seconds allowed per request, passed straight through to `server.run`.
    #: None means no timeout.
    timeout: int | None
    #: The theorem's ``full_name``. Used ONLY to make error messages
    #: attributable; nothing here reads the corpus row.
    theorem: str

    def run(self, request: Any) -> Any:
        """Send one request, translating transport failures into `ReplError`.

        `lean_interact` raises builtin `TimeoutError` (and kills the server) on a slow
        request, and `BrokenPipeError` when the REPL closes; both are translated because
        `runner.py` records ``f"{type(exc).__name__}: {exc}"`` into the row's
        ``lean_error`` column, and a uniform `ReplError` with a ``timeout:``-shaped message
        keeps timeouts greppable without adding a seventh verdict string. A `LeanError`
        reply is returned as a value here, not raised (see `classify_step`).
        """
        try:
            return self.server.run(request, timeout=self.timeout)
        except TimeoutError as exc:
            raise ReplError(f"timeout after {self.timeout}s on {self.theorem}: {exc}") from exc
        except BrokenPipeError as exc:
            raise ReplError(f"REPL closed on {self.theorem}: {exc}") from exc

    def step(self, proof_state: int, tactic: str) -> StepOutcome:
        """Apply `tactic` at `proof_state` and classify the reply.

        Proof states are immutable, so many calls may branch from the same id. Combinators
        (``;``, ``<;>``) are part of a single tactic and must not be split by the caller.
        Raises `ReplError` for any REPL-level trouble -- transport failure (`run`) or the
        REPL's own error channel (`classify_step` kind ``"exception"``) -- so callers cannot
        silently record it as a Lean verdict.
        """
        outcome = classify_step(self.run(ProofStep(proof_state=proof_state, tactic=tactic)))
        if outcome.kind == "exception":
            raise ReplError(outcome.error or "REPL-level failure with no message")
        return outcome

    def close(self) -> None:
        """Kill the REPL process. Safe to call more than once.

        A failure to kill an already-dead process is logged at DEBUG and swallowed, since
        `close` runs in `finally` blocks and a teardown failure escaping would mask the real
        error being propagated. Nothing else here is swallowed.
        """
        try:
            self.server.kill()
        except Exception as exc:  # noqa: BLE001 - teardown must not mask the real error
            logger.debug("killing the REPL for %s failed: %s", self.theorem, exc)


# ---------------------------------------------------------------------------
# Session opening
# ---------------------------------------------------------------------------

#: Mirrors the retired `_open_dojo_with_retry`. Server startup occasionally
#: fails when several sessions open concurrently: the Lean subprocess races on
#: the build cache. A reopen usually succeeds within seconds, so retry with
#: backoff.
_REPL_OPEN_RETRIES = 3
#: One entry per SLEEP, i.e. ``_REPL_OPEN_RETRIES - 1``: the last attempt raises
#: instead of sleeping.
_REPL_OPEN_BACKOFF_S = (5.0, 15.0)


def _default_server_factory(root: Path) -> LeanServer:
    """Start a `LeanServer` on the mathlib4 checkout at `root`.

    A separate function, not inlined into `open_session`, so tests can substitute a fake
    and a pooled/remote server can be dropped in without touching the open/retry logic.
    `LeanServer.__init__` asserts its config and starts the process, so this returns a live
    server or raises.
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

    `server_factory` is an injection seam: takes the resolved root `Path`, returns a
    started server exposing ``run``/``kill``; defaults to `_default_server_factory`.
    Returns the live session and the proof-state id of the stub's ``sorry`` (the state
    tactic 0 of the proof should apply to).

    Raises `ReplError` if the checkout is misconfigured, the server failed to start, or the
    module failed to import (never a bare `RuntimeError`: `verify.verify_proof_tail` reads
    that as ``"replay_failed"``, a claim about the corpus -- see the translation comment
    below). Raises `StatementError` (a non-retried `ReplError` subclass) if the declaration
    has no statement/proof boundary, or its stub didn't elaborate.

    Configuration and statement derivation happen before any Lean process starts, so a
    misconfiguration or unusable declaration fails in milliseconds rather than after a REPL
    startup; both are deterministic, so they sit outside the retry loop. Inside the loop the
    same rule applies one level down: server start and ``import`` are retried, stub
    elaboration (`StatementError`) is not.
    """
    # `mathlib_root` signals misconfiguration with a plain `RuntimeError` -- right for a
    # direct caller, pinned by its own tests, but wrong once it travels toward
    # `verify.verify_proof_tail`, whose first except clause maps RuntimeError to
    # "replay_failed" (a claim the recorded ground truth doesn't replay). An operator who
    # forgot SMOLBENCH_MATHLIB_ROOT would otherwise see every theorem condemned as broken
    # ground truth. Translating here, not in `mathlib_root`, keeps both contracts right.
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
            # Terminal: same statement/environment/answer every time. Kill the server first
            # (no orphaned Lean processes), then propagate without sleeping.
            if session is not None:
                session.close()
            raise
        except Exception as exc:  # noqa: BLE001 - retried below, or re-raised
            # No orphaned Lean processes: the server this attempt started (if any) dies
            # with the attempt.
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

    Two REPL round trips: a fresh-environment ``import`` (``env=None`` starts a new session
    in which ``import`` is legal), then the stub in the environment that produced.

    Raises `ReplError` (retryable) if the ``import`` round trip failed -- routinely a
    cold/racing ``lake`` build cache, which is what `open_session`'s backoff exists for.
    Raises `StatementError` (deterministic, not retried) if the stub didn't elaborate or
    produced no ``sorry`` to branch from -- the single most likely failure mode in
    production (see the module docstring on import-only environments), so every message
    carries the REPL's own text verbatim rather than degrading a whole eval into unexplained
    `exception` rows.
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
