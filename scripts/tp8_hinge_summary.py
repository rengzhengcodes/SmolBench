"""Render the tp=8 hinge JSONs as plain text.

This matches the shape of notebooks/deduction/results/TP4HINGE_SUMMARY.txt,
so the tp=1, tp=4, and tp=8 arms of the determinism record read
identically.

Per arm, this script prints byte agreement k/n; the engine-config facts
that prove the arm really ran at tp=8, with the custom all-reduce path
live; and the cache counters before and after. It also prints per-row
SHA and length for ALL rows, and, where an archived tp=4 arm exists,
the SHA-level tp=4-vs-tp=8 cross comparison.

USAGE
    .venv/bin/python scripts/tp8_hinge_summary.py [model ...]
"""
import json
import pathlib
import sys

RESULTS = pathlib.Path("/workspace/SmolBench/notebooks/deduction/results")


def render(model: str) -> str:
    p = RESULTS / f"tp8hinge_{model}.json"
    if not p.exists():
        return f"(no report for {model})\n"
    d = json.loads(p.read_text())
    o = []
    inst = d.get("instance") or {}
    o.append(f"model={model} type={inst.get('instance_type')} "
             f"expect_tp={d.get('expect_tp')} n_prompts={d.get('n_prompts')} "
             f"prompts_match_tp4={d.get('prompt_set_matches_tp4_hinge')}")
    o.append(f"instance={inst.get('instance_id')} @ {inst.get('availability_zone')} "
             f"({d.get('provisioned_utc')} -> {d.get('finished_utc')})")
    for arm, e in (d.get("arms") or {}).items():
        o.append(f"\n--- arm {arm} ---")
        if e.get("skipped_for_budget_at_min") is not None:
            o.append(f"  SKIPPED for budget at {e['skipped_for_budget_at_min']} min")
        if e.get("FAILED"):
            o.append(f"  FAILED: {e['FAILED']}")
        cfg = e.get("server_config") or {}
        o.append(f"  served_tp={e.get('served_tp')} gpu={cfg.get('gpu')} "
                 f"vllm={cfg.get('vllm_version')}")
        o.append(f"  args={e.get('vllm_args')}")
        sl = e.get("serve_log") or {}
        if sl.get("engine_config_parsed"):
            o.append(f"  engine_config={sl['engine_config_parsed']}")
        if sl.get("worker_ranks"):
            o.append(f"  worker_ranks={len(sl['worker_ranks'])}: "
                     f"{sl['worker_ranks'][0]}..{sl['worker_ranks'][-1]}")
        for when in ("fingerprint", "fingerprint_after"):
            fp = e.get(when) or {}
            lines = [l for l in (fp.get("cache_metric_lines") or [])
                     if "queries_total" in l or "hits_total" in l]
            if lines:
                o.append(f"  cache counters {when}: " + "; ".join(l.split("}")[-1].strip()
                         + " <- " + l.split("{")[0] for l in lines))
        for k in ("serve_plus_passes_s", "n_prompts_this_arm", "n_prompts_compared",
                  "P1_truncated_at_min", "P2_truncated_at_min",
                  "retried_rows_P1", "retried_rows_P2", "P1_errors", "P2_errors"):
            if e.get(k) is not None:
                o.append(f"  {k}: {e[k]}")
        c = e.get("within_process_baseline")
        if c:
            if c["n"] == 0:
                o.append("  WITHIN-PROCESS: NOT MEASURED (0 rows compared)")
            else:
                o.append(f"  WITHIN-PROCESS: {c['identical']}/{c['n']} byte-identical "
                         f"(rate {c['rate']:.3f}); excluded-empty={c['excluded_empty_rows']}; "
                         f"n_before_exclusion={c['n_before_exclusion']}")
            s1 = e.get("sha_table_P1") or {}
            s2 = e.get("sha_table_P2") or {}
            diffs = {x["prompt"]: x for x in c.get("diffs", [])}
            for pid in sorted(set(s1) & set(s2)):
                if pid in diffs:
                    x = diffs[pid]
                    o.append(f"    DIFF {pid}: len {x['len_a']} vs {x['len_b']}, "
                             f"sha {x['sha_a']} vs {x['sha_b']}, "
                             f"common_prefix={x['common_prefix_chars']}")
                else:
                    o.append(f"    SAME {pid}: sha={s1[pid]['sha256_12']} "
                             f"len={s1[pid]['len']}")
        x = e.get("cross_tp_vs_tp4_det_P1")
        if x:
            if not x.get("available"):
                o.append(f"  CROSS-TP vs tp=4: unavailable ({x.get('reason')})")
            else:
                o.append(f"  CROSS-TP vs tp=4 det P1 (SHA-level): "
                         f"{x['identical']}/{x['n']} identical")
                o.append(f"    CONFOUND: {x['confound_note']}")
                for r in x["rows"]:
                    o.append(f"    {'SAME' if r['same'] else 'DIFF'} {r['prompt']}: "
                             f"tp4 {r['tp4_sha']}/{r['tp4_len']} vs "
                             f"tp8 {r['tp8_sha']}/{r['tp8_len']}")
    return "\n".join(o) + "\n"


def main() -> int:
    models = sys.argv[1:] or ["ministral-3-3b", "nemotron-3-super-120b-a12b"]
    txt = "tp8 HINGE -- 2026-08-21/22 -- determinism bundle at tensor-parallel 8\n\n"
    txt += "\n\n".join(render(m) for m in models)
    out = RESULTS / "TP8HINGE_SUMMARY.txt"
    out.write_text(txt)
    print(txt)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
