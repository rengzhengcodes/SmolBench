"""Offline contract for scripts/results/audit_run_completeness.py; no AWS.

``audit_induction`` used to report only what it found: a ``(model, arm)``
with zero objects in S3 never entered its ``seen`` dict, so an absent model
printed "ok". It now walks the expected grid and set-differences against
it, so an unlanded cell is examined and a 31st seed is named, not counted
as ``-1``.
"""

import os
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.results import audit_run_completeness as audit

#: A miniature roster: 2 models x 2 arms x 3 seeds, so an assertion names
#: every cell explicitly instead of restating the tool's own arithmetic.
FAKE_DRIVER = SimpleNamespace(
    MODELS={"model-a": "tag_a", "model-b": "tag_b"},
    INFO_TYPES=("intens", "zero"),
    BASE_SEED=0,
    N_REPLICATES=3,
)


class FakeStore:
    """``list_seeds`` only, the one method `audit_induction` uses."""

    def __init__(
        self, seeds_by_cell: dict[tuple[str, str], tuple[int, ...]] | None = None,
        default: tuple[int, ...] | range = (), raises: Exception | None = None
    ) -> None:
        self.seeds_by_cell = seeds_by_cell or {}
        self.default = default
        self.raises = raises
        self.calls = []

    def list_seeds(self, model: str, tag: str, info: str) -> list[int]:
        self.calls.append((model, tag, info))
        if self.raises is not None:
            raise self.raises
        return list(self.seeds_by_cell.get((model, info), self.default))


@pytest.fixture
def fake_driver(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Stand in for notebooks/induction/run_study.py.

    Injected rather than loaded, so this never runs the driver's
    module-scope ``load_dotenv``, which would mutate the environment for the
    whole pytest session (`test_the_real_roster_is_the_grid` covers the real
    driver).
    """
    monkeypatch.setattr(audit, "_induction_driver", lambda: FAKE_DRIVER)
    return FAKE_DRIVER


def test_a_cell_with_nothing_landed_is_examined_and_reported(
    fake_driver: SimpleNamespace
) -> None:
    """An empty store used to yield {} and read as 'ok'."""
    store = FakeStore()  # every cell empty
    gaps, examined = audit.audit_induction(store=store)
    assert examined == 4
    assert gaps == {
        "model-a": {"intens": {"missing": [0, 1, 2], "unexpected": []},
                    "zero": {"missing": [0, 1, 2], "unexpected": []}},
        "model-b": {"intens": {"missing": [0, 1, 2], "unexpected": []},
                    "zero": {"missing": [0, 1, 2], "unexpected": []}},
    }
    # The grid is walked by (model, MODELS[model], info) -- the analysis tag,
    # not the spec key, is what a store keyed on tags would need.
    assert sorted(store.calls) == [
        ("model-a", "tag_a", "intens"), ("model-a", "tag_a", "zero"),
        ("model-b", "tag_b", "intens"), ("model-b", "tag_b", "zero"),
    ]


def test_a_complete_grid_reports_nothing(fake_driver: SimpleNamespace) -> None:
    gaps, examined = audit.audit_induction(store=FakeStore(default=(0, 1, 2)))
    assert (gaps, examined) == ({}, 4)


def test_an_extra_seed_is_named_not_counted_negative(fake_driver: SimpleNamespace) -> None:
    """`EXPECTED_SEEDS - len(seeds)` turned a 4th seed into missing = -1."""
    store = FakeStore(seeds_by_cell={("model-a", "zero"): (0, 1, 2, 3)}, default=(0, 1, 2))
    gaps, _examined = audit.audit_induction(store=store)
    assert gaps == {"model-a": {"zero": {"missing": [], "unexpected": [3]}}}


def test_a_short_cell_names_the_missing_seed(fake_driver: SimpleNamespace) -> None:
    store = FakeStore(seeds_by_cell={("model-b", "intens"): (0, 2)}, default=(0, 1, 2))
    gaps, _examined = audit.audit_induction(store=store)
    assert gaps == {"model-b": {"intens": {"missing": [1], "unexpected": []}}}


def test_an_unknown_model_is_refused(fake_driver: SimpleNamespace) -> None:
    """A typo'd selection must fail loudly, not audit nothing and pass."""
    with pytest.raises(SystemExit) as excinfo:
        audit.audit_induction(models=["model-a", "typo"], store=FakeStore())
    assert "typo" in str(excinfo.value)


def test_an_empty_selection_examines_nothing(fake_driver: SimpleNamespace) -> None:
    """The zero-cell case main() refuses as 'AUDITED NOTHING'."""
    assert audit.audit_induction(models=[], store=FakeStore()) == ({}, 0)


def test_a_store_failure_propagates(fake_driver: SimpleNamespace) -> None:
    """A credentials/throttling error must never read as 'no seeds landed'."""
    with pytest.raises(RuntimeError):
        audit.audit_induction(store=FakeStore(raises=RuntimeError("AccessDenied")))


def test_the_real_roster_is_the_grid() -> None:
    """os.environ is restored after, since the driver's import-time load_dotenv would otherwise leak into later tests."""
    saved = dict(os.environ)
    try:
        driver = audit._induction_driver()
        store = FakeStore(default=range(driver.BASE_SEED,
                                        driver.BASE_SEED + driver.N_REPLICATES))
        gaps, examined = audit.audit_induction(store=store)
    finally:
        os.environ.clear()
        os.environ.update(saved)
    assert (len(driver.MODELS), len(driver.INFO_TYPES)) == (21, 4)
    assert (driver.BASE_SEED, driver.N_REPLICATES) == (0, 30)
    assert examined == 84 and gaps == {}
    assert {c[0] for c in store.calls} == set(driver.MODELS)


# ---------------------------------------------------------------------------
# both S3 seams resolve the bucket from one place
# ---------------------------------------------------------------------------
def test_both_audits_follow_smolbench_results_s3(monkeypatch: pytest.MonkeyPatch) -> None:
    """A redirected results store must reach both the induction and deduction halves."""
    from smolbench.evals.results_store import DEFAULT_RESULTS_BUCKET

    listed = []

    class FakeS3:
        def get_paginator(self, name: str) -> "FakeS3":
            return self

        def paginate(self, Bucket: str, Prefix: str, Delimiter: str) -> Any:
            listed.append(Bucket)
            return iter(())

    monkeypatch.setattr(audit, "_s3", FakeS3)

    monkeypatch.setenv("SMOLBENCH_RESULTS_S3", "s3://redirected-bucket/base")
    store = audit._induction_store()
    assert (store.bucket, store.base_prefix) == ("redirected-bucket", "base")
    assert store.experiment == audit.INDUCTION_EXPERIMENT
    assert list(audit.iter_deduction_lanes(local=False, deduction_prefix="spool/")) == []
    assert listed == ["redirected-bucket"]

    # ...and unset falls back to the one committed default, not a local copy.
    monkeypatch.delenv("SMOLBENCH_RESULTS_S3")
    assert audit._induction_store().bucket == DEFAULT_RESULTS_BUCKET
    assert list(audit.iter_deduction_lanes(local=False, deduction_prefix="spool/")) == []
    assert listed == ["redirected-bucket", DEFAULT_RESULTS_BUCKET]
