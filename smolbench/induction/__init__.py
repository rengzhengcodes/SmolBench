"""Provide the induction benchmarks package.

``periodic`` (generalized FizzBuzz over overlapping periodic harmonics) and
``chromatic`` (sceptre-handoff sequences over chromatic intervals) are the two
benchmarks; ``_common`` holds the generation machinery they share,
``experiment`` the replicated-evaluation and EC2-lifecycle facade that runs
them, and ``figures`` their plotting helpers. See
``smolbench/induction/README.md`` for conceptual background.
"""
