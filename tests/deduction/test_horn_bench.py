# pylint: disable=redefined-outer-name
"""Generator invariants, certificates, checker behaviour and arm matching."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from smolbench.deduction.horn.checker import (
    certify,
    closure,
    designed_proof,
    on_path_heads,
    parse,
    verify,
)
from smolbench.deduction.horn.cli import build_theory, main as cli_main
from smolbench.deduction.horn.render import ARMS, Rendered, Tokenizer, arm_keys, render
from smolbench.deduction.horn.theory import Theory, generate

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def tok() -> Tokenizer:
    """Shared cl100k tokenizer."""
    return Tokenizer()


def test_generate_is_deterministic():
    """Same seed, same theory; different seed, different theory."""
    a, b = generate(7), generate(7)
    assert a.to_json() == b.to_json()
    assert generate(8).to_json() != a.to_json()


@pytest.mark.parametrize("seed", range(6))
def test_theory_invariants(seed):
    """One constant, a chain, open alternatives, on-path library, trees, every fact used."""
    th = generate(seed, m=3, height=3, n_extra=30)
    names = [r.head for r in th.rules.values()] + [b for r in th.rules.values() for b in r.body]
    assert th.constant not in names
    for r in th.rules.values():
        assert 1 <= len(r.body) <= 2 and len(set(r.body)) == len(r.body)
    assert len(th.links) == 3 and len(th.library) >= 3 + 20
    assert len(th.facts) == th.m + 1
    for lm in th.library:
        leaves = {lm.node_pred[p] for p in lm.nodes_at(lm.height)}
        assert leaves == set(lm.body)
        assert lm.role in ("chain", "open")
    heads = [lk.head for lk in th.links]
    assert th.goal == heads[-1]
    for i, lk in enumerate(th.links):
        if i:
            assert heads[i - 1] in lk.body
    assert all(lm.head in on_path_heads(th) for lm in th.library)
    derivable = closure(th.lemmas(), set(th.facts))
    assert all(all(b in derivable for b in lm.body) for lm in th.library)
    assert set(th.facts) <= {b for lm in th.links for b in lm.body}
    assert {r.kind for r in th.rules.values()} == {"lemma", "axiom"}
    assert len(th.tree(1)) == 2**th.height - 1
    assert th.tree(1)[0].head == th.links[0].head and th.tree(1)[0].depth == 0
    assert set(th.order) == set(th.rules)
    assert len(th.alternatives()) == th.n_extra


def test_per_lemma_depths():
    """Depth overrides change tree size per lemma and the max height."""
    th = generate(4, m=2, height=2, n_extra=3, depths={2: 4, 5: 3})
    assert [lm.height for lm in th.library][:5] == [2, 4, 2, 2, 3]
    assert th.max_height == 4
    assert len(th.tree(2)) == 15 and len(th.tree(1)) == 3


def test_roundtrip_json():
    """JSON round-trips."""
    th = generate(3, depths={1: 3})
    back = Theory.from_json(th.to_json())
    assert back.to_json() == th.to_json()


def test_from_json_loads_recorded_theories_and_rejects_retired_setups():
    """Files written before the setup was fixed load when they match it; others raise."""
    th = generate(2, m=3, n_extra=2)
    d = json.loads(th.to_json())
    d.update(open_frac=1.0, fact_height=0, fact_chain=0, deep_facts=[], constants=[th.constant])
    d["facts_by_const"] = {th.constant: list(th.facts)}
    d["rules"].append({"key": "sub1.0", "head": "x", "body": ["y"], "kind": "sublemma", "link": 1, "depth": 1})
    d["order"].append("sub1.0")
    back = Theory.from_json(json.dumps(d))
    assert back.to_json() == th.to_json()
    for bad in (
        {"fact_height": 2},
        {"open_frac": 0.25},
        {"constants": [th.constant, "zz"]},
        {"deep_facts": ["q"]},
    ):
        with pytest.raises(ValueError):
            Theory.from_json(json.dumps({**d, **bad}))
    d2 = json.loads(th.to_json())
    d2["library"][-1]["role"] = "blocked"
    with pytest.raises(ValueError):
        Theory.from_json(json.dumps(d2))


@pytest.mark.parametrize("seed", range(3))
@pytest.mark.parametrize("arm", ARMS)
def test_certificate_and_designed_proofs(seed, arm, tok):
    """Every arm certifies; the lemma route verifies; the tree route only in both."""
    th = generate(seed, m=4, height=2, n_extra=6, depths={2: 3})
    r = render(th, arm, tok)
    cert = certify(th, r)
    assert cert.ok, cert.reasons
    assert cert.min_steps == th.m == cert.designed_steps
    v = verify(th, r, "\n".join(designed_proof(th, "short")))
    assert v.verdict == "success" and v.route == "short" and v.steps == th.m
    v2 = verify(th, r, "\n".join(designed_proof(th, "long")))
    if arm == "both":
        assert v2.verdict == "success" and v2.route == "long"
    else:
        assert v2.verdict == "invalid_step"


def test_alternatives_give_second_routes():
    """Open alternatives add routes; the chain alone still proves the goal."""
    th = generate(11, m=4, height=2, n_extra=40)
    assert th.alternatives()
    for arm in ARMS:
        cert = certify(th, render(th, arm))
        assert cert.ok, (arm, cert.reasons)
    chain_only = [th.rules[Theory.lemma_key(i)] for i in range(1, th.m + 1)]
    assert th.goal in closure(chain_only, set(th.facts))
    # an alternative route into the goal that is not the chain
    alt = next(lm for lm in th.alternatives() if lm.head == th.goal)
    assert all(b in closure(th.lemmas(), set(th.facts)) for b in alt.body)


def test_checker_rejects_bad_proofs():
    """Wrong order, unknown rule content, unknown constant and short proofs fail."""
    th = generate(5, m=2, height=2)
    r = render(th, "lem")
    good = designed_proof(th)
    assert verify(th, r, "\n".join(good)).verdict == "success"
    assert verify(th, r, "\n".join(line + " by R1" for line in good)).verdict == "success"
    v = verify(th, r, "\n".join(reversed(good)))
    assert v.verdict == "invalid_step" and "premise" in v.reason
    bad = good[0].replace(f"derive {th.links[0].head}", "derive nonsense", 1)
    v = verify(th, r, bad)
    assert v.verdict == "invalid_step" and "no library rule" in v.reason
    assert verify(th, r, good[0]).verdict == "incomplete"
    other = good[0].replace(f"({th.constant})", "(zz)", 1)
    v = verify(th, r, other)
    assert v.verdict == "invalid_step" and "unknown constant" in v.reason
    # a tree axiom is not a lemma: applying one in lem is an invented rule
    ax = th.tree(1)[0]
    step = f"derive {ax.head}({th.constant}) from " + ", ".join(f"{b}({th.constant})" for b in ax.body)
    assert "no library rule" in verify(th, r, step).reason


def test_parse_tolerates_fences_numbering_and_prose():
    """Fences, numbering and prose are skipped; give up and empty are verdicts."""
    text = "Let me think.\n```\n1. derive a(c) from b(c), d(c)\nStep 2: derive e(c) from a(c) by R5.\n```\n"
    steps, gave_up, ignored = parse(text)
    assert [s.head for s in steps] == ["a(c)", "e(c)"]
    assert steps[0].body == ("b(c)", "d(c)") and steps[1].body == ("a(c)",)
    assert not gave_up and ignored == 1
    assert not parse("I give up.\n")[0] and parse("give up")[1]
    th = generate(1)
    r = render(th, "lem")
    assert verify(th, r, "no idea").verdict == "no_answer"
    assert verify(th, r, "give up").verdict == "given_up"
    assert verify(th, r, "", finish_reason="length").verdict == "length"


def test_bare_atoms_read_as_the_constant():
    """A dropped ``(c)`` is read as the theory's constant."""
    th = generate(3, m=2, height=2)
    r = render(th, "lem")
    bare = "\n".join(line.replace(f"({th.constant})", "") for line in designed_proof(th))
    assert verify(th, r, bare).verdict == "success"


@pytest.mark.parametrize("seed", range(3))
def test_controls_match_both(seed, tok):
    """pad and disc keep both's line count, token count and lemma positions."""
    th = generate(seed, m=4, height=2, n_extra=8, depths={3: 3, 6: 3})
    both = render(th, "both", tok)
    lem = render(th, "lem", tok)
    n_slots = len(th.tree_keys())
    assert both.n_rules == lem.n_rules + n_slots
    for arm in ("pad", "disc"):
        r = render(th, arm, tok)
        assert arm_keys(th, arm)[1] == set(th.tree_keys())
        assert r.prompt.count("\n") == both.prompt.count("\n")
        assert abs(r.n_tokens - both.n_tokens) <= n_slots
        for key, off in both.lemma_offsets.items():
            assert abs(r.lemma_offsets[key] - off) <= n_slots
        assert list(r.ids.values()) == list(lem.ids.values())
        assert render(th, arm, tok).prompt == r.prompt  # deterministic
    pad = render(th, "pad", tok)
    assert pad.filler_tokens > 0 and pad.n_rules == lem.n_rules and not pad.extra_rules
    r = render(th, "disc", tok)
    assert r.n_rules == both.n_rules and len(r.extra_rules) == n_slots


def test_disc_trees_keep_roots_but_cannot_be_entered(tok):
    """disc shows both's same-head root rules, yet no tree route is valid."""
    th = generate(3, m=3, height=2, n_extra=4)
    both = render(th, "both", tok)
    r = render(th, "disc", tok)
    roots_both = {
        (th.rules[k].head, frozenset(th.rules[k].body))
        for k in both.ids.values()
        if th.rules[k].kind == "axiom" and th.rules[k].depth == 0
    }
    roots_disc = {(d["head"], frozenset(d["body"])) for d in r.extra_rules if d["depth"] == 0}
    assert roots_both == roots_disc
    assert verify(th, r, "\n".join(designed_proof(th, "long"))).verdict == "invalid_step"
    assert verify(th, r, "\n".join(designed_proof(th, "short"))).verdict == "success"
    # a step through a disc root rule fails on its undischarged intermediates and
    # counts as an attempt to enter a tree
    d = next(d for d in r.extra_rules if d["depth"] == 0)
    c = th.constant
    step = f"derive {d['head']}({c}) from " + ", ".join(f"{b}({c})" for b in d["body"])
    v = verify(th, r, step)
    assert "premise not derived" in v.reason and v.route == "long"


def test_arms_are_fixed():
    """Only the five arms render; retired specs raise."""
    th = generate(1)
    for bad in ("lem:1", "both:1", "pad:2", "ax", "unf:1", "bothm", "padm", "deep", "dpad", "junk", "nope"):
        with pytest.raises(ValueError):
            render(th, bad)


def test_certify_flags_broken_instances(tok):
    """A tampered rendering fails certification."""
    th = generate(6, m=3, height=2, n_extra=4)
    r = render(th, "both", tok)
    # drop the last chain lemma and its tree: the goal is no longer derivable
    goal_keys = {k for k, ru in th.rules.items() if ru.link == th.m}
    r2 = Rendered.from_meta({**vars(r), "ids": {i: k for i, k in r.ids.items() if k not in goal_keys}})
    reasons = certify(th, r2).reasons
    assert any("goal not derivable" in s for s in reasons)
    # a control arm that leaks the trees
    r3 = Rendered.from_meta({**vars(render(th, "pad", tok)), "ids": r.ids})
    assert any("tree route is valid in pad" in s for s in certify(th, r3).reasons)


def test_build_theory_fixes_the_ratio(tok):
    """A rung has exactly 5 m alternatives, every tree at depth 2, and its size follows m."""
    sizes = {}
    for m in (3, 12, 48):
        th = build_theory(1, m=m)
        assert th.n_extra == 5 * m and len(th.library) == 6 * m
        assert {lm.height for lm in th.library} == {2}
        assert len(th.tree_keys()) == 3 * len(th.library)
        sizes[m] = render(th, "lem", tok).n_tokens
    assert sizes[3] < sizes[12] < sizes[48]
    th = build_theory(2, m=4, alt_per_lemma=0)
    assert th.n_extra == 0 and certify(th, render(th, "both", tok)).ok


@pytest.mark.parametrize("seed", range(4))
def test_generate_exact_n_extra(seed):
    """The alternative count is met exactly even when detours are drawn."""
    for n in (1, 5, 11, 60):
        assert generate(seed, m=4, n_extra=n).n_extra == n


def test_cli_render_and_check(tmp_path, tok):
    """The CLI renders the four arms, writes meta and theory, and checks an answer."""
    out = tmp_path / "rung"
    subprocess.run(
        [sys.executable, "-m", "smolbench.deduction.horn.cli", "render", "--seeds", "1",
         "--m", "3", "--out", str(out)],
        check=True, cwd=REPO_ROOT, capture_output=True,
    )
    sd = out / "s0001"
    assert sorted(p.name for p in sd.iterdir() if p.is_dir()) == sorted(ARMS)
    th = Theory.from_json((sd / "theory.json").read_text())
    meta = json.loads((sd / "both" / "meta.json").read_text())
    assert meta["certificate"]["ok"] and meta["certificate"]["min_steps"] == 3
    assert "max_steps" not in meta
    answer = tmp_path / "answer.md"
    answer.write_text("\n".join(designed_proof(th, "long")) + "\n")
    assert cli_main(["check", str(sd / "both"), str(answer)]) == 0
    assert cli_main(["check", str(sd / "disc"), str(answer)]) == 1
    # rendering a different theory into the same directory is refused
    with pytest.raises(RuntimeError):
        from smolbench.deduction.horn.cli import write_seed  # pylint: disable=import-outside-toplevel

        write_seed(out, generate(1, m=3, n_extra=1), ["lem"], tok=tok)
