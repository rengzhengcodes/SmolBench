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

The two `zero`-arm entries under `production_seed_0`/`production_seed_1` were
computed from the intended rendering before the non-leaking-zero-arm code was
written, so they are a prediction the implementation had to meet, not a
recording of whatever it produced.
