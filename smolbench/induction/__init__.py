"""Provide the induction benchmarks package.

This package holds the induction benchmarks: ``periodic`` (generalized
FizzBuzz over overlapping periodic harmonics) and ``chromatic``
(sceptre-handoff sequences over chromatic intervals). ``_common`` holds
generation machinery shared by both benchmarks, ``experiment`` provides the
replicated-evaluation and EC2-lifecycle facade that runs them, and
``figures`` provides plotting helpers for their analysis notebooks. See
``smolbench/induction/README.md`` for the benchmarks' conceptual background.
"""
