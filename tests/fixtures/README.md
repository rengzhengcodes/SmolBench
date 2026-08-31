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
