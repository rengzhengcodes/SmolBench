# tests/fixtures/

Shared fixtures for the offline suite. Everything in this tree is TEST
INPUT ONLY -- no experiment, notebook, or script may read from here. In
particular `lean_mini*/` and `postcutoff/` are tiny synthetic stand-ins
for the LeanDojo exports, never usable corpora; the real corpora and
results live under `notebooks/` and on S3 (see `notebooks/ARCHIVE.md`).

`golden_quizzes.json` holds SHA-256 hashes of the induction generation
pipeline's output at the studies' production configs;
`tests/induction/test_golden_quizzes.py` regenerates the quizzes and
compares hashes, so golden answers are re-verified on every run without
committing the full prompt text.

Every entry is a hash of output the pipeline is required to produce, not a
snapshot of whatever it happened to produce when the fixture was written: a
hash change is a generation change that must be explained, never just
re-recorded. The `zero`-arm entries are the range-free rendering (no
`$seq_len`), so a leaked range would fail here even if the arm still ran.

Hashes alone cannot show *what* changed. Storing the hashed prompt text
alongside them, so a drift can be diffed, is tracked in issue #61.
