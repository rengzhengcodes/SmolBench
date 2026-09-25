"""Generator invariants, certificates, checker behaviour and pad alignment."""

from __future__ import annotations

import pytest

from smolbench.deduction.horn.checker import (
    certify,
    closure,
    designed_proof,
    on_path_heads,
    parse,
    verify,
)
from smolbench.deduction.horn.render import Tokenizer, arm_keys, parse_arm, render
from smolbench.deduction.horn.theory import Theory, generate

ARMS = [
    "lem",
    "unf:1",
    "unf:2",
    "ax",
    "both:1",
    "both:2",
    "both",
    "pad:1",
    "pad:2",
    "pad",
]


@pytest.fixture(scope="module")
def tok() -> Tokenizer:
    """Shared cl100k tokenizer."""
    return Tokenizer()


def test_generate_is_deterministic():
    """Same seed, same theory; different seed, different theory."""
    a, b = generate(7, n_constants=1), generate(7, n_constants=1)
    assert a.to_json() == b.to_json()
    assert generate(8, n_constants=1).to_json() != a.to_json()


@pytest.mark.parametrize("seed", range(6))
def test_theory_invariants(seed):
    """Names, bodies, chain, on-path library, roles and cut sizes are as designed."""
    th = generate(seed, m=3, height=3, n_extra=30, n_constants=3, open_frac=0.3)
    names = [r.head for r in th.rules.values()] + [
        b for r in th.rules.values() for b in r.body
    ]
    assert th.constant not in names
    for r in th.rules.values():
        assert 1 <= len(r.body) <= 2 and len(set(r.body)) == len(r.body)
    assert len(th.links) == 3 and len(th.library) >= 3 + 20
    for lm in th.library:
        leaves = {lm.node_pred[p] for p in lm.nodes_at(lm.height)}
        assert leaves == set(lm.body)
    heads = [lk.head for lk in th.links]
    assert th.goal == heads[-1]
    for i, lk in enumerate(th.links):
        if i:
            assert heads[i - 1] in lk.body
    anc = on_path_heads(th)
    assert all(lm.head in anc for lm in th.library)
    main = closure(list(th.rules.values()), set(th.facts))
    for lm in th.library:
        fires = all(b in main for b in lm.body)
        assert fires == (lm.role != "blocked"), (lm.index, lm.role)
    full = closure(list(th.rules.values()), set(th.facts_by_const[th.constants[1]]))
    assert all(
        all(b in full for b in lm.body) for lm in th.library
    )  # full decoy fires everything
    assert {r.kind for r in th.rules.values()} == {"lemma", "axiom", "sublemma"}
    assert len(th.cut(1, 0)) == 1
    assert len(th.cut(1, th.height)) == 2**th.height - 1
    assert len(th.cut(1, 99)) == 2**th.height - 1  # clamped to the lemma's height
    assert parse_arm("both:99", th.max_height) == ("both", th.max_height)


def test_per_lemma_depths():
    """Depth overrides change tree size per lemma and the max height."""
    th = generate(4, m=2, height=2, n_extra=3, n_constants=1, depths={2: 4, 5: 3})
    assert [lm.height for lm in th.library][:5] == [2, 4, 2, 2, 3]
    assert th.max_height == 4
    assert len(th.cut(2, 4)) == 15 and len(th.cut(1, 4)) == 3
    assert th.cut_steps(4) == 3 + 15


def test_roundtrip_json():
    """JSON round-trips."""
    th = generate(3, n_constants=3, depths={1: 3})
    back = Theory.from_json(th.to_json())
    assert back.to_json() == th.to_json()


@pytest.mark.parametrize("seed", range(3))
@pytest.mark.parametrize("arm", ARMS)
def test_certificate_and_designed_proofs(seed, arm, tok):
    """Every arm certifies with the designed step count and its routes verify."""
    th = generate(
        seed, m=4, height=2, n_extra=6, n_constants=3, open_frac=0.0, depths={2: 3}
    )
    r = render(th, arm, tok)
    cert = certify(th, r)
    assert cert.ok, cert.reasons
    kind, j = parse_arm(arm, th.max_height)
    if kind in ("lem", "both", "pad"):
        assert cert.min_steps == th.m
    else:
        assert cert.min_steps == th.cut_steps(j)
    route = "long" if kind == "unf" else "short"
    v = verify(th, r, "\n".join(designed_proof(th, r, route)))
    assert v.verdict == "success" and v.route == route
    if kind == "both":
        v2 = verify(th, r, "\n".join(designed_proof(th, r, "long")))
        assert v2.verdict == "success" and v2.route == "long"


def test_open_alternatives_give_second_routes():
    """With open alternatives every arm still certifies and the goal has more than one proof."""
    th = generate(11, m=4, height=2, n_extra=40, n_constants=3, open_frac=0.5)
    assert th.alternatives("open") and th.alternatives("blocked")
    for arm in ("lem", "both", "pad", "unf:1"):
        cert = certify(th, render(th, arm))
        assert cert.ok, (arm, cert.reasons)
    chain_only = [th.rules[Theory.lemma_key(i)] for i in range(1, th.m + 1)]
    assert th.goal in closure(chain_only, set(th.facts))


def test_checker_rejects_bad_proofs():
    """Wrong order, unknown rule content, dead end and short proofs fail."""
    th = generate(5, m=2, height=2)
    r = render(th, "lem")
    good = designed_proof(th, r)
    assert verify(th, r, "\n".join(good)).verdict == "success"
    assert (
        verify(th, r, "\n".join(line + " by R1" for line in good)).verdict == "success"
    )
    v = verify(th, r, "\n".join(reversed(good)))
    assert v.verdict == "invalid_step" and "premise" in v.reason
    bad = good[0].replace(f"derive {th.links[0].head}", "derive nonsense", 1)
    v = verify(th, r, bad)
    assert v.verdict == "invalid_step" and "no library rule" in v.reason
    assert verify(th, r, good[0]).verdict == "incomplete"


def test_parse_tolerates_fences_numbering_and_prose():
    """Fences, numbering and prose are skipped; give up and empty are verdicts."""
    text = "Let me think.\n```\n1. derive a(c) from b(c), d(c)\nStep 2: derive e(c) from a(c) by R5.\n```\n"
    steps, gave_up, ignored = parse(text)
    assert [s.head for s in steps] == ["a(c)", "e(c)"]
    assert steps[0].body == ("b(c)", "d(c)") and steps[1].body == ("a(c)",)
    assert not gave_up and ignored == 1
    assert not parse("I give up.\n")[0] and parse("give up")[1]
    th = generate(1, n_constants=1)
    r = render(th, "lem")
    assert verify(th, r, "no idea").verdict == "no_answer"
    assert verify(th, r, "give up").verdict == "given_up"
    assert verify(th, r, "", finish_reason="length").verdict == "length"


@pytest.mark.parametrize("seed", range(3))
def test_pad_matches_both_length_and_lemma_positions(seed, tok):
    """pad has both's token count and lemma token offsets, at full and partial depth."""
    th = generate(seed, m=4, height=2, n_extra=8, n_constants=3, depths={3: 3, 6: 3})
    for level in ("", ":1"):
        both = render(th, "both" + level, tok)
        pad = render(th, "pad" + level, tok)
        n_slots = both.n_rules - pad.n_rules
        assert n_slots > 0
        assert abs(both.n_tokens - pad.n_tokens) <= n_slots
        assert pad.filler_tokens > 0
        for key, off in both.lemma_offsets.items():
            assert abs(pad.lemma_offsets[key] - off) <= n_slots
        assert both.prompt.count("\n") == pad.prompt.count("\n")
    lem = render(th, "lem", tok)
    assert list(render(th, "pad", tok).ids.values()) == list(lem.ids.values())
    assert arm_keys(th, "pad")[1] == set(th.cut_keys(th.max_height))


def test_arm_parsing_errors():
    """Bad arm specs raise."""
    th = generate(1, n_constants=1)
    for bad in ("lem:1", "unf", "unf:0", "nope"):
        with pytest.raises(ValueError):
            render(th, bad)


@pytest.mark.parametrize("seed", range(3))
def test_multi_constant_blocked_certify(seed, tok):
    """Blocked alternatives never fire for the main constant; every arm certifies."""
    th = generate(seed, m=5, height=2, n_extra=20, n_constants=3, open_frac=0.0)
    assert len(th.constants) == 3 and th.alternatives("blocked")
    for arm in ("lem", "unf:1", "ax", "both", "pad"):
        r = render(th, arm, tok)
        cert = certify(th, r)
        assert cert.ok, (arm, cert.reasons)
        assert "## Facts" in r.prompt and all(
            f"({c})" in r.prompt for c in th.constants
        )
        assert "R1:" not in r.prompt


def test_multi_constant_checker():
    """A bare atom is invalid with several constants; a blocked step is rejected."""
    th = generate(2, m=3, height=2, n_extra=10, n_constants=2, open_frac=0.0)
    r = render(th, "lem")
    good = designed_proof(th, r)
    assert verify(th, r, "\n".join(good)).verdict == "success"
    bare = good[0].replace(f"({th.constant})", "")
    v = verify(th, r, bare)
    assert v.verdict == "invalid_step" and "needs a constant" in v.reason
    bl = th.alternatives("blocked")[0]
    line = f"derive {bl.head}({th.constant}) from {', '.join(f'{b}({th.constant})' for b in bl.body)}"
    v = verify(th, r, line)
    assert v.verdict == "invalid_step" and "premise" in v.reason


def test_bare_atoms_accepted_with_one_constant():
    """With one constant a dropped ``(c)`` is read as that constant."""
    th = generate(3, m=2, height=2, n_constants=1)
    r = render(th, "lem")
    bare = "\n".join(
        line.replace(f"({th.constant})", "") for line in designed_proof(th, r)
    )
    assert verify(th, r, bare).verdict == "success"


def test_step_budget():
    """A stated step budget rejects longer proofs as too_long and keeps the short one."""
    th = generate(6, m=3, height=2, n_extra=4, n_constants=1)
    r = render(th, "both", max_steps=3)
    assert "at most 3 steps" in r.prompt
    assert verify(th, r, "\n".join(designed_proof(th, r, "short"))).verdict == "success"
    v = verify(th, r, "\n".join(designed_proof(th, r, "long")))
    assert v.verdict == "too_long" and v.route == "long"
    r0 = render(th, "both")
    assert (
        verify(th, r0, "\n".join(designed_proof(th, r0, "long"))).verdict == "success"
    )


def test_main_only_arms():
    """bothm unfolds only chain and open lemmas; padm matches it."""
    th = generate(9, m=4, height=2, n_extra=30, n_constants=3, open_frac=0.3)
    tok = Tokenizer()
    b, bm = render(th, "both", tok), render(th, "bothm", tok)
    pm = render(th, "padm", tok)
    assert bm.n_rules < b.n_rules and abs(bm.n_tokens - pm.n_tokens) <= 4
    blocked = {lm.index for lm in th.library if lm.role == "blocked"}
    assert all(
        th.rules[k].link not in blocked or th.rules[k].kind == "lemma"
        for k in bm.ids.values()
    )
    assert certify(th, bm).ok and certify(th, pm).ok


@pytest.mark.parametrize("seed", range(3))
def test_junk_and_disc_match_both(seed, tok):
    """junk and disc keep both's line count, rule count, token count and lemma positions."""
    th = generate(seed, m=4, height=2, n_extra=8, n_constants=1, depths={3: 3, 6: 3})
    both = render(th, "both", tok)
    for arm in ("junk", "disc"):
        r = render(th, arm, tok)
        n_slots = len(arm_keys(th, arm)[1])
        assert n_slots > 0 and len(r.extra_rules) == n_slots
        assert r.n_rules == both.n_rules
        assert r.prompt.count("\n") == both.prompt.count("\n")
        assert abs(r.n_tokens - both.n_tokens) <= n_slots
        for key, off in both.lemma_offsets.items():
            assert abs(r.lemma_offsets[key] - off) <= n_slots
        assert certify(th, r).ok, certify(th, r).reasons
        assert render(th, arm, tok).prompt == r.prompt  # deterministic


def test_junk_rules_are_disjoint_and_inert(tok):
    """junk rules use no theory predicate and cannot be applied."""
    th = generate(2, m=4, height=2, n_extra=6, n_constants=1)
    r = render(th, "junk", tok)
    preds = {p for ru in th.rules.values() for p in (ru.head, *ru.body)} | set(th.facts)
    for d in r.extra_rules:
        assert d["kind"] == "junk"
        assert not ({d["head"], *d["body"]} & preds)
    d = r.extra_rules[0]
    c = th.constants[0]
    step = f"derive {d['head']}({c}) from " + ", ".join(f"{b}({c})" for b in d["body"])
    v = verify(th, r, step)
    assert v.verdict == "invalid_step" and "premise not derived" in v.reason
    assert verify(th, r, "\n".join(designed_proof(th, r, "short"))).route == "short"


def test_disc_trees_keep_roots_but_cannot_be_entered(tok):
    """disc shows both's same-head root rules, yet no tree route is valid."""
    th = generate(3, m=3, height=2, n_extra=4, n_constants=1)
    both = render(th, "both", tok)
    r = render(th, "disc", tok)
    roots_both = {
        (th.rules[k].head, frozenset(th.rules[k].body))
        for k in both.ids.values()
        if th.rules[k].kind == "axiom" and th.rules[k].depth == 0
    }
    roots_disc = {
        (d["head"], frozenset(d["body"])) for d in r.extra_rules if d["depth"] == 0
    }
    assert roots_both == roots_disc
    assert (
        verify(th, r, "\n".join(designed_proof(th, both, "long"))).verdict
        == "invalid_step"
    )
    assert verify(th, r, "\n".join(designed_proof(th, r, "short"))).verdict == "success"
    # a step through a disc root rule fails on its undischarged intermediates
    d = next(d for d in r.extra_rules if d["depth"] == 0)
    c = th.constants[0]
    step = f"derive {d['head']}({c}) from " + ", ".join(f"{b}({c})" for b in d["body"])
    assert "premise not derived" in verify(th, r, step).reason


def _fact_route(th: Theory, fact: str) -> list[str]:
    """Steps re-deriving ``fact`` from the deep facts through its tree and chains."""
    c = th.constants[0]
    steps: list[str] = []
    known = set(th.deep_facts)

    def derive(pred: str) -> None:
        if pred in known:
            return
        r = next(
            r
            for r in th.rules.values()
            if r.kind in ("factax", "factchain") and r.head == pred
        )
        for b in r.body:
            derive(b)
        steps.append(
            f"derive {pred}({c}) from " + ", ".join(f"{b}({c})" for b in r.body)
        )
        known.add(pred)

    derive(fact)
    return steps


@pytest.mark.parametrize("seed", range(3))
def test_deep_adds_routes_below_facts_without_new_candidates(seed, tok):
    """deep keeps every lemma-head candidate count, matches dpad, and its fact routes verify."""
    th = generate(
        seed, m=4, height=2, n_extra=6, n_constants=1, fact_height=2, fact_chain=3
    )
    assert th.deep_facts and set(th.deep_facts) <= set(th.facts)
    lem, deep, dpad = (render(th, a, tok) for a in ("lem", "deep", "dpad"))
    heads = [lm.head for lm in th.library]
    for h in heads + [th.goal]:
        n_lem = sum(th.rules[k].head == h for k in lem.ids.values())
        n_deep = sum(th.rules[k].head == h for k in deep.ids.values())
        assert n_lem == n_deep
    n_slots = len(th.fact_tree_keys())
    assert deep.n_rules == lem.n_rules + n_slots and n_slots > 0
    assert abs(deep.n_tokens - dpad.n_tokens) <= n_slots
    assert deep.prompt.count("\n") == dpad.prompt.count("\n")
    for key, off in deep.lemma_offsets.items():
        assert abs(dpad.lemma_offsets[key] - off) <= n_slots
    for arm in (lem, deep, dpad):
        assert certify(th, arm).ok, certify(th, arm).reasons
    # the short proof is valid in every arm; re-deriving a fact first is valid only in deep
    short = designed_proof(th, deep, "short")
    fact = th.library[0].body[-1]
    longer = _fact_route(th, fact) + short
    assert len(longer) > len(short)
    v = verify(th, deep, "\n".join(longer))
    assert v.verdict == "success" and v.route == "mixed", v.reason
    assert verify(th, dpad, "\n".join(longer)).verdict == "invalid_step"
    assert verify(th, dpad, "\n".join(short)).verdict == "success"
    assert render(th, "deep", tok).prompt == deep.prompt
    assert Theory.from_json(th.to_json()).deep_facts == th.deep_facts


def test_deep_needs_fact_trees():
    th = generate(0, m=3, height=2, n_extra=2, n_constants=1)
    with pytest.raises(ValueError):
        arm_keys(th, "deep")


@pytest.mark.parametrize("seed", range(3))
def test_every_given_fact_is_used(seed):
    """By default no given fact is idle: each one is a premise of some rule that fires."""
    th = generate(seed, m=5, height=2, n_extra=6, n_constants=1)
    used = {b for r in th.rules.values() for b in r.body}
    assert set(th.facts) <= used
    assert (
        len(
            generate(
                seed, m=5, height=2, n_extra=6, n_constants=1, n_unused_facts=2
            ).facts
        )
        == len(th.facts) + 2
    )
