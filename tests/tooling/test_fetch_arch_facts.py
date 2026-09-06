"""Offline contract for scripts/arch/fetch_arch_facts.py; no network.

Every fetch goes through an injected fake, so nothing here reaches the
Hugging Face hub. The properties pinned are the three the PR #14 reviewer
found broken: the fetch must use the deploy spec's pinned commit SHA rather
than the moving ``main`` branch, ``--check`` must compare revisions, and
``--check`` must run BEFORE either output file is written.
"""

import json
import sys

import pytest

from tests._paths import SCRIPTS

sys.path.insert(0, str(SCRIPTS / "arch"))

import fetch_arch_facts as faf  # noqa: E402
from smolbench.evals.providers.ec2 import EC2_DEPLOY_SPECS  # noqa: E402

#: Minimal config.json: enough for _hoist/_classify/_layer_view and for the
#: four fields cross_check compares against the fixture.
CONFIG = {
    "architectures": ["FakeForCausalLM"],
    "model_type": "fake",
    "num_hidden_layers": 4,
    "hidden_size": 512,
    "num_attention_heads": 8,
    "num_key_value_heads": 2,
    "max_position_embeddings": 131072,
}


def _fake_fetch(calls, *, resolved=None, payload=CONFIG):
    """Build a recording fetch stub. `resolved` None means "the pin held"."""

    def fetch(repo, filename, revision):
        calls.append((repo, filename, revision))
        return dict(payload), (resolved or revision), None

    return fetch


def test_every_fetch_uses_the_spec_pinned_sha_not_main():
    """The URL used to be resolve/main, so a force-push re-based every figure."""
    calls = []
    bundle = faf.collect(fetch=_fake_fetch(calls))

    roster = {k: v for k, v in EC2_DEPLOY_SPECS.items() if k != faf._SMOKE_KEY}
    assert len(bundle["facts"]) == len(roster) == 21
    assert calls, "collect() fetched nothing"
    assert not any(revision == "main" for _repo, _f, revision in calls)
    # Both files of every rung are fetched at that rung's own pinned SHA.
    by_repo = {}
    for repo, filename, revision in calls:
        by_repo.setdefault(repo, set()).add((filename, revision))
    for key, spec in roster.items():
        pinned = faf.spec_revision(spec)
        assert by_repo[spec["hf_model_id"]] == {
            ("config.json", pinned), ("generation_config.json", pinned)}
        assert bundle["facts"][key]["pinned_revision"] == pinned
        assert bundle["raw"][key]["pinned_revision"] == pinned
        assert bundle["facts"][key]["revision"] == pinned  # the fake resolved the pin


def test_spec_revision_refuses_an_unpinned_spec():
    """No fallback to a moving branch: an unpinned rung cannot be audited."""
    assert faf.spec_revision({"hf_model_id": "r", "vllm_args": ["--revision", "abc123"]}) == "abc123"
    with pytest.raises(ValueError):
        faf.spec_revision({"hf_model_id": "r", "vllm_args": ["--tp", "8"]})
    with pytest.raises(ValueError):
        faf.spec_revision({"hf_model_id": "r", "vllm_args": ["--revision"]})  # dangling
    # ...and every shipped spec is pinned, so the guard is not a live path.
    for spec in EC2_DEPLOY_SPECS.values():
        assert len(faf.spec_revision(spec)) == 40


def test_cross_check_reports_a_moved_pin():
    """pinned != resolved is the vendor-force-push signal the old check missed."""
    moved = faf.collect(fetch=_fake_fetch([], resolved="f" * 40))
    problems = faf.cross_check(moved["facts"])
    assert problems, "a moved pin must be reported"
    assert any("pin moved or was deleted upstream" in p for p in problems)
    a_key = sorted(moved["facts"])[0]
    assert any(p.startswith(f"{a_key}: pinned revision ") for p in problems)

    # A record with no resolved revision at all is also a problem, not a pass.
    held = faf.collect(fetch=_fake_fetch([]))
    held["facts"][a_key]["revision"] = None
    assert any("missing revision" in p for p in faf.cross_check(held["facts"]))


def test_check_runs_before_the_outputs_are_written(tmp_path, monkeypatch, capsys):
    """A failed cross-check must leave the previous audit trail untouched."""
    raw, facts = tmp_path / "arch_configs_raw.json", tmp_path / "arch_facts.json"
    monkeypatch.setattr(faf, "_RAW_PATH", raw)
    monkeypatch.setattr(faf, "_FACTS_PATH", facts)
    monkeypatch.setattr(faf, "_fetch", _fake_fetch([], resolved="f" * 40))
    monkeypatch.setattr(sys, "argv", ["fetch_arch_facts.py", "--check"])

    assert faf.main() == 1
    assert "CROSS-CHECK MISMATCHES" in capsys.readouterr().out
    assert not raw.exists() and not facts.exists()

    # ...and a clean run does write both.
    monkeypatch.setattr(faf, "_fetch", _fake_fetch([]))
    monkeypatch.setattr(sys, "argv", ["fetch_arch_facts.py"])
    assert faf.main() == 0
    assert json.loads(facts.read_text())["models"]
    assert json.loads(raw.read_text())
