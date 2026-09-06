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

`golden_quizzes.json`'s `production_seed_0`/`production_seed_1` `zero`
entries were regenerated when the zero-information arm stopped rendering
the position range: its question is now "How many of the positions include
'<label>'?", with no `$seq_len`, because on the default 1..n pathway the
period-1 harmonic's answer IS `seq_len` and the old question printed it in
the prompt of the very arm that estimates the chance floor. The other three
arms' hashes (and both library-generator pins) are UNCHANGED by that fix, so
a diff touching more than those two values is a regression, not a
re-baseline. The two new values were computed from the intended rendering
BEFORE the code was written (the study template minus its
" 1 through $seq_len" clause), so they are a prediction the implementation
had to meet, not a recording of whatever it produced.
