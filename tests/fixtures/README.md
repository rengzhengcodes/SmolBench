# tests/fixtures/

Shared fixtures for the offline suite. `roster_configs.json` is read by
`tests/evals/test_deploy_specs.py`, which drift-pins `ec2.MODEL_ATTENTION_HEADS`
against it, and by `scripts/arch/fetch_arch_facts.py --check`.

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
