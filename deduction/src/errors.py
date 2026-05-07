"""Kimina error-message classifier + lookup-leak detector.

Translates the unstructured `messages` array from kimina-lean-server's
`/verify` response into a typed `ErrorClass` plus an optional
`lookup_leak_attempt` flag.

Per DESIGN.md, the flag fires when the failure is `identifier_not_found`
and the missing identifier names something the model could only know from
training (T itself, T's downstream in F, or files downstream of F). With
F's transitive imports as the import scope, those identifiers are *not*
in the prompt scope, so a reference to them is recall-from-training rather
than legitimate use of in-prompt context.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List, Optional, Sequence


class ErrorClass(str, Enum):
    IDENTIFIER_NOT_FOUND = "identifier_not_found"
    TYPE_MISMATCH = "type_mismatch"
    TIMEOUT = "timeout"
    PARSE_ERROR = "parse_error"
    SORRY = "sorry_in_proof"            # warning, not error, but worth flagging
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class ClassifiedError:
    error_class: ErrorClass
    detail: str                  # short, the salient line
    raw: str                     # full original message text
    missing_identifier: Optional[str] = None
    expected_type: Optional[str] = None
    got_type: Optional[str] = None


# ---------- regexes ----------

_UNKNOWN_IDENT_RE = re.compile(r"unknown (?:identifier|constant)\s+'([^']+)'")
_TYPE_MISMATCH_RE = re.compile(r"type mismatch", re.IGNORECASE)
_TIMEOUT_RE = re.compile(
    r"\b(deterministic timeout|maxHeartbeats|timeout|heartbeat (limit|deadline) (exceeded|reached))",
    re.IGNORECASE,
)
_PARSE_RE = re.compile(
    r"\b(expected\s+\S+|unexpected token|expected term|"
    r"expected ':='|unexpected end of input|unexpected character)",
    re.IGNORECASE,
)
_SORRY_RE = re.compile(r"\bsorry\b", re.IGNORECASE)
_EXPECTED_TYPE_RE = re.compile(
    r"has type[\s\S]*?but is expected to have type", re.IGNORECASE
)


def classify_one(message_text: str) -> ClassifiedError:
    """Classify a single error-text blob (the `data` field of one Kimina
    message). Pattern-matching is deliberately conservative — when in doubt
    we return OTHER and preserve the raw text for later analysis."""
    text = message_text.strip()
    detail = text.splitlines()[0][:300] if text else ""

    m = _UNKNOWN_IDENT_RE.search(text)
    if m:
        return ClassifiedError(
            error_class=ErrorClass.IDENTIFIER_NOT_FOUND,
            detail=detail,
            raw=text,
            missing_identifier=m.group(1),
        )

    if _EXPECTED_TYPE_RE.search(text) or _TYPE_MISMATCH_RE.search(text):
        return ClassifiedError(
            error_class=ErrorClass.TYPE_MISMATCH,
            detail=detail,
            raw=text,
        )

    if _TIMEOUT_RE.search(text):
        return ClassifiedError(error_class=ErrorClass.TIMEOUT, detail=detail, raw=text)

    if _PARSE_RE.search(text):
        return ClassifiedError(error_class=ErrorClass.PARSE_ERROR, detail=detail, raw=text)

    return ClassifiedError(error_class=ErrorClass.OTHER, detail=detail, raw=text)


def classify_messages(
    messages: Sequence[dict],
) -> List[ClassifiedError]:
    """Classify all error-severity messages from a Kimina /verify response.

    Warnings about `sorry` are also returned as ClassifiedError with
    ErrorClass.SORRY — useful for diagnosing replays that pass with sorries
    rather than real proofs.
    """
    out: List[ClassifiedError] = []
    for m in messages:
        sev = m.get("severity")
        text = str(m.get("data", ""))
        if sev == "error":
            out.append(classify_one(text))
        elif sev == "warning" and _SORRY_RE.search(text):
            out.append(ClassifiedError(error_class=ErrorClass.SORRY, detail="sorry warning", raw=text))
    return out


# ---------- lookup-leak detection ----------

# Lean identifier characters: letters (incl. Unicode), digits, primes, dots, underscores.
_DECL_HEAD_RE = re.compile(
    r"^\s*(?:@\[[^\]]*\]\s*)*"
    r"(?:noncomputable\s+|private\s+|protected\s+|scoped\s+|unsafe\s+|partial\s+|mutual\s+)*"
    r"(?:theorem|lemma|def|instance|abbrev|axiom|opaque|structure|inductive|class)\s+"
    r"([A-Za-z_][\w.Ͱ-Ͽ⁰-₟℀-⅏]*)",
    re.MULTILINE,
)


def declarations_in_text(text: str) -> List[str]:
    """Extract declared identifier names from a chunk of Lean source. Used
    on F lines L..end to compute "downstream of T in F"."""
    return [m.group(1) for m in _DECL_HEAD_RE.finditer(text)]


def is_lookup_leak(
    err: ClassifiedError,
    *,
    target_full_name: str,
    target_local_name: str,
    f_downstream_of_t_names: Iterable[str] = (),
    downstream_of_f_names: Iterable[str] = (),
) -> bool:
    """Decide whether an `identifier_not_found` error indicates the model
    tried to call a name that isn't (legitimately) in scope."""
    if err.error_class is not ErrorClass.IDENTIFIER_NOT_FOUND:
        return False
    name = err.missing_identifier
    if not name:
        return False
    if name == target_full_name or name == target_local_name:
        return True
    if name.startswith(target_full_name + "."):
        return True
    if name in set(f_downstream_of_t_names):
        return True
    if name in set(downstream_of_f_names):
        return True
    return False
