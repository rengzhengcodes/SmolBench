# Pending: purge + gap-fill before analysis

Do this AFTER the sweep exits and BEFORE running the pre-registered analysis.

During the 2026-07-14 run segment, infra-caused exception rows accumulated in
`all_rows.jsonl` while the sweep was live (first 8 flagged ~06:50Z: 4 sanity
DojoInitError with a healthy std cache — transient Dojo-init pressure, not the
eviction — and 4 cell "Inference endpoint unreachable" rows from an egress-IP
flap). The file cannot be rewritten while the sweep holds it open in append
mode, and resume replays recorded exceptions, so:

1. After the sweep process exits, purge rows matching:
   `verdict == "exception"` AND payload contains any of
   `Unexpected EOF` / `DojoInitError` / `BlockingIOError` / `unreachable after`
   (keep `DojoTacticTimeoutError` rows — genuine, pre-registered as missing).
   Back up the file first (`.bak-purge<N>-<ts>` beside it, as before).
2. Relaunch the sweep once with the same arguments as a gap-fill pass: resume
   skips everything recorded and re-runs only the purged cells/sanity checks.
3. Only then run `cmd_analyze` + the McNemar gate per PREREGISTRATION.md.

## Known non-recoverable: core-namespace theorems

Sanity checks for theorems whose source file lives in the traced repo's std /
core packages (`List.*`, `String.*`, `Array.*`, `Std.*`, ...) fail
DojoInitError **systematically** — 0 successes vs 46+8 exceptions across every
segment of this run, while mathlib-file theorems pass 62/62. Almost certainly
the std cache eviction also removed LeanDojo's *trace* artifacts for std-package
files, which `lake build` does not regenerate (mathlib-file inits only consume
std as a library and still work). Do NOT chase this mid-run: the gap-fill pass
will fail these sanity checks again, and per PREREGISTRATION.md a sanity
failure drops the theorem for ALL arms symmetrically (~8–15 of 300 theorems,
negligible power impact). Expect the purge/gap-fill cycle to converge with
these theorems absent; that is correct behavior, not data loss. If a future
run wants them back, re-trace the std package (or re-download the traced
cache) before sampling.

Delete this file once done.
