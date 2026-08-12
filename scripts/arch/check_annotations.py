"""Validate the model annotations against the atlas's drawing constraints.

Most annotation fields are drawn inside fixed-width SVG boxes or single table
cells, so an over-long string does not wrap -- it runs out of its box and over
whatever is beside it. Eyeballing 21 models x ~10 fields does not catch that
reliably, so the limits are checked here instead.

The second job is coverage: reporting which models are missing which fields, so
a silently-empty section is visible before the page is published rather than
after.

Usage
-----
``.venv/bin/python scripts/arch/check_annotations.py``

Exit status is non-zero when any hard limit is exceeded or a model key is
unknown; missing optional fields are reported but do not fail the run.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

_HERE = Path(__file__).resolve().parent
_MODELS = _HERE / "annotations_models.json"
_PAGE_DATA = _HERE / "page_data.json"

#: field -> max characters. Derived from the drawn geometry: the schematic's
#: sub-block is 424 user units wide and its detail lines are set at 9.5px in a
#: 0.6-advance monospace, which fits ~66 characters after the 13-unit inset.
_LIMITS = {
    "params": 22,
    "peShort": 42,
    "attnShort": 34,
    "kvPerToken": 22,
    "mtp": 46,
    "heads": 22,
    "headDim": 18,
}
_MAP_LIMITS = {
    "mixerNames": 34,
    "mixerDetail": 62,
    "peByLayer": 62,
}
_LIST_LIMITS = {"badges": 22, "warnBadges": 30}

#: Fields whose absence leaves a visible hole in the page.
_EXPECTED = ("params", "signature", "pe", "attention", "ffn", "peShort",
             "attnShort", "mixerNames", "peByLayer", "sources")


def main() -> int:
    if not _MODELS.exists():
        print(f"missing {_MODELS.name} — nothing to check")
        return 1
    notes: Dict[str, Any] = json.loads(_MODELS.read_text())
    families = notes.pop("_families", {})
    page = json.loads(_PAGE_DATA.read_text())
    known = set(page["models"])

    problems: List[str] = []
    gaps: Dict[str, List[str]] = {}

    unknown = sorted(set(notes) - known)
    if unknown:
        problems.append(f"unknown model keys: {unknown}")
    missing_models = sorted(known - set(notes))
    if missing_models:
        problems.append(f"models with no annotation: {missing_models}")

    for key in sorted(set(notes) & known):
        note = notes[key]
        for field, limit in _LIMITS.items():
            value = note.get(field)
            if isinstance(value, str) and len(value) > limit:
                problems.append(f"{key}.{field}: {len(value)} chars > {limit} — {value!r}")
        for field, limit in _MAP_LIMITS.items():
            for sub, value in (note.get(field) or {}).items():
                if isinstance(value, str) and len(value) > limit:
                    problems.append(
                        f"{key}.{field}.{sub}: {len(value)} chars > {limit} — {value!r}")
        for field, limit in _LIST_LIMITS.items():
            for value in (note.get(field) or []):
                if isinstance(value, str) and len(value) > limit:
                    problems.append(f"{key}.{field}: {len(value)} chars > {limit} — {value!r}")

        for source in note.get("sources") or []:
            if not str(source.get("url", "")).startswith("http"):
                problems.append(f"{key}.sources: non-http url {source.get('url')!r}")
        for flag in note.get("flags") or []:
            if flag.get("kind") not in ("contradiction", "unverified", "serving"):
                problems.append(f"{key}.flags: unexpected kind {flag.get('kind')!r}")

        # A mixer name must exist for every mixer kind the model actually uses,
        # or the schematic falls back to a generic label on a real mechanism.
        # A kind may be named per VARIANT instead (DeepSeek-V4 runs three
        # attention variants under one kind), so a compound "kind:variant" key
        # satisfies the requirement for that kind.
        names = note.get("mixerNames") or {}
        for kind in ("full", "sliding", "linear", "ssm"):
            if not page["models"][key]["counts"].get(kind):
                continue
            variants = {
                t.get("variant") for t in page["models"][key]["tracks"]
                if t["mix"] == kind and t.get("variant")
            }
            named = kind in names or (
                variants and all(f"{kind}:{v}" in names for v in variants)
            )
            if not named:
                gaps.setdefault(key, []).append(f"mixerNames.{kind}")

        for field in _EXPECTED:
            if not note.get(field):
                gaps.setdefault(key, []).append(field)

    missing_families = sorted(
        {f["id"] for f in page["families"]} - set(families)
    )
    if missing_families:
        gaps.setdefault("_families", []).extend(missing_families)

    print(f"annotated models: {len(set(notes) & known)}/{len(known)}   "
          f"families: {len(families)}/{len(page['families'])}")
    if gaps:
        print("\nMISSING FIELDS (page renders a dash or a generic label):")
        for key in sorted(gaps):
            print(f"  {key}: {', '.join(gaps[key])}")
    if problems:
        print("\nHARD PROBLEMS:")
        for line in problems:
            print(f"  {line}")
        return 1
    print("\nall length and shape limits OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
