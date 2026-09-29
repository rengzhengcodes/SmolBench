"""Freeze the Horn results of the ICLR 2027 submission into a release data folder.

Writes one file per model with the exact cells behind the paper table, full generations
included, plus the calibration rows that chose each model's chain length:

    <out>/README.md
    <out>/MANIFEST.json                    file list, SHA-256, row counts, chain lengths
    <out>/horn/rows/<model>.jsonl          1,200 cells: 4 arms x 100 seeds x 3 replicates
    <out>/horn/calibration/<model>.jsonl   lem-only calibration rows (seeds 200-229)

The main rows are selected by ``notebooks/deduction/analysis/horn_results.py`` exactly as
the paper table was: merged across run sources, one row per cell, at the model's chosen
chain length, with a ``missing`` row for a cell that never produced an answer. Each row
keeps its stored verdict fields (``iclr`` scoring) and gains ``scoring_default``, the
verdict fields under ``default`` scoring. Calibration rows are kept only when their prompt
matches what the current generator renders for that seed.

usage: freeze_release_data.py --scratchpad <run tree> --calibration <by_model dir> --out <dir>
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
for p in (REPO_ROOT, REPO_ROOT / "notebooks" / "deduction" / "analysis"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# pylint: disable=wrong-import-position
import horn_results as hr  # noqa: E402

from smolbench.deduction.horn.cli import build_theory  # noqa: E402
from smolbench.deduction.horn.extract import verdict_fields  # noqa: E402
from smolbench.deduction.horn.render import Tokenizer, render  # noqa: E402
from smolbench.deduction.horn.repro import load_protocol  # noqa: E402

VERDICT_FIELDS = ("answer", "verdict", "steps", "route", "reason", "ignored_lines")
CALIB_RUNG = re.compile(r"^calib_m(\d+)$")
DATA_VERSION = "horn-iclr2027-v1"


def _clean(r: dict) -> dict:
    """The row without the loader's private fields; ``_source`` becomes ``source``."""
    out = {k: v for k, v in r.items() if not k.startswith("_")}
    if "_source" in r:
        out["source"] = r["_source"]
    out.setdefault("scoring", "iclr")
    return out


def main_rows(scratchpad: Path, rungs: Path) -> tuple[dict[str, list[dict]], dict[str, int], list[str]]:
    """Per model, the paper's cells with both scorings.

    Rows keep the order in which the table pipeline first read them: the bootstrap in
    ``horn_results.arm_stats`` draws seeds in that order, so the same order reproduces
    the published intervals exactly.
    """
    res = hr.run_pipeline(scratchpad, scoring="iclr", rungs=rungs, keep_text=True)
    rescore = hr.Rescorer("default", rungs)
    by_model: dict[str, list[dict]] = collections.defaultdict(list)
    for key in res.rows:
        model, m, *_ = key
        if res.chosen.get(model) != m:
            continue
        r = res.rows[key]
        row = _clean(r)
        if r.get("verdict") == "missing":
            row["scoring_default"] = {"verdict": "missing"}
        else:
            alt = dict(r)
            rescore(model, m, alt)
            row["scoring_default"] = {f: alt.get(f) for f in VERDICT_FIELDS}
        by_model[model].append(row)
    return by_model, res.chosen, res.anomalies


def calibration_rows(calib_dir: Path, models: list[str]) -> tuple[dict[str, list[dict]], collections.Counter]:
    """Per model, lem calibration rows whose prompt matches the current generator."""
    proto = load_protocol()
    tok = Tokenizer()
    rendered: dict[tuple[int, int], tuple] = {}
    stats: collections.Counter = collections.Counter()
    out: dict[str, list[dict]] = {}
    for model in models:
        seen: dict[tuple, dict] = {}
        for path in sorted((calib_dir / model / "calibration").glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                mt = CALIB_RUNG.match(r.get("rung", ""))
                if not mt or r.get("arm") != "lem":
                    stats["not a lem calibration row"] += 1
                    continue
                if r.get("verdict") == "exception":
                    stats["exception"] += 1
                    continue
                m, seed = int(mt.group(1)), int(r["seed"])
                key = (m, seed, int(r["rep"]))
                if key in seen:
                    stats["duplicate"] += 1
                    continue
                if (m, seed) not in rendered:
                    th = build_theory(seed, m, proto["height"], proto["alt_per_lemma"])
                    rendered[(m, seed)] = (th, render(th, "lem", tok))
                th, rd = rendered[(m, seed)]
                sha = hashlib.sha256(rd.prompt.encode()).hexdigest()[:16]
                if r.get("prompt_sha256"):
                    ok = r["prompt_sha256"] == sha
                else:
                    ok = r.get("n_prompt_tokens_rendered") == rd.n_tokens
                if not ok:
                    stats["prompt differs from the current generator"] += 1
                    continue
                row = _clean(r)
                row.pop("_file", None)
                if r.get("finish_reason") in ("stop", "length"):
                    iclr = verdict_fields(th, rd, r.get("content") or "", r["finish_reason"], "iclr")
                    if iclr["verdict"] != r["verdict"]:
                        stats["stored verdict differs from iclr rescoring"] += 1
                    alt = verdict_fields(th, rd, r.get("content") or "", r["finish_reason"], "default")
                    row["scoring_default"] = {f: alt[f] for f in VERDICT_FIELDS}
                seen[key] = row
                stats["kept"] += 1
        out[model] = [seen[k] for k in sorted(seen)]
    return out, stats


def _write_jsonl(path: Path, rows: list[dict]) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")
    path.write_bytes(data)
    return {"rows": len(rows), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


README = """# Horn benchmark results, ICLR 2027 submission ({version})

Model outputs and verdicts behind the Horn-rule deduction results. The code that reads this
folder is `smolbench.deduction.horn` (branch `release/iclr2027` of the SmolBench repository).

## Layout

- `horn/rows/<model>.jsonl`: the 1,200 cells behind the paper table for each model:
  4 arms (lem, pad, disc, both) x 100 theories (seeds 100-199) x 3 replicates, at the
  model's chain length m.
- `horn/calibration/<model>.jsonl`: lem-only rows on the calibration seeds (200-229) at
  the chain lengths tried while choosing m.
- `MANIFEST.json`: every file with its SHA-256, row count and size, and each model's m.

## Row fields

- Cell: `spec_key` (model), `rung` (`m<m>`, `stage2_m<m>` or `calib_m<m>`), `arm`, `seed`, `rep`.
- Request: `model` (served name or Bedrock id), `sampling`, `prompt_sha256` (vLLM rows) or
  `n_prompt_tokens_rendered`, `ts`, `source` (bedrock, spot, b200 or orcd).
- Response: `content`, `reasoning`, `finish_reason`, `prompt_tokens`, `completion_tokens`.
- Verdict under `iclr` scoring (as submitted): `answer`, `verdict`, `steps`, `route`,
  `reason`, `ignored_lines`, `scoring`.
- Verdict under `default` scoring: the same fields under `scoring_default`.

Verdicts: `success` is the only pass; `invalid_step`, `incomplete`, `given_up`, `no_answer`,
`length` (output cap hit) and `missing` (a cell that never produced an answer) are failures.

The prompts are not included: `python -m smolbench.deduction.horn.repro render --model <model>`
regenerates them from their seeds and checks them against recorded digests.
"""


def main(argv: list[str] | None = None) -> int:
    """Write the release folder."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", maxsplit=1)[0])
    ap.add_argument("--scratchpad", type=Path, default=hr.SCRATCHPAD, help="run tree read by horn_results.py")
    ap.add_argument("--rungs", type=Path, default=None, help="served rungs (default <scratchpad>/roster2)")
    ap.add_argument("--calibration", type=Path, required=True, help="by_model dir with <model>/calibration/*.jsonl")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    rows, chosen, anomalies = main_rows(a.scratchpad, a.rungs or a.scratchpad / "roster2")
    models = [m for m in hr.MODELS if m in rows]
    calib, cstats = calibration_rows(a.calibration, models)
    manifest: dict = {"version": DATA_VERSION, "models": {}, "files": {}}
    for model in models:
        n_missing = sum(r["verdict"] == "missing" for r in rows[model])
        manifest["models"][model] = {"m": chosen[model], "cells": len(rows[model]), "missing": n_missing}
        manifest["files"][f"horn/rows/{model}.jsonl"] = _write_jsonl(a.out / "horn" / "rows" / f"{model}.jsonl", rows[model])
        manifest["files"][f"horn/calibration/{model}.jsonl"] = _write_jsonl(
            a.out / "horn" / "calibration" / f"{model}.jsonl", calib[model]
        )
    (a.out / "README.md").write_text(README.format(version=DATA_VERSION), encoding="utf-8")
    (a.out / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    for line in anomalies:
        print(f"note: {line}")
    print(f"calibration rows: {dict(cstats)}")
    for model, info in manifest["models"].items():
        print(f"{model:28s} m={info['m']:<3d} cells={info['cells']} missing={info['missing']} "
              f"calibration={manifest['files'][f'horn/calibration/{model}.jsonl']['rows']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
