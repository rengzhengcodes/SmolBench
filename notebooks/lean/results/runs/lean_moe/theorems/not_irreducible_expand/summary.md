# not_irreducible_expand   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/Perfect.lean`  

**Ground-truth tail (from k):**
```lean
exact not_irreducible_pow (Fact.out : p.Prime).ne_one
```

**True premises at k:** `not_irreducible_pow`, `Fact.out`, `Nat.Prime.ne_one`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 18.6s, verify 0.3s, in=407, out=5012)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intro h
let g := map (↑(RingEquiv.symm (frobeniusEquiv R p))) f
have hp : 0 < p := (Fact.out : Nat.Prime p).pos
have hfac := h.2 g (g ^ p.pred) (by
  simpa [pow_succ, Nat.succ_pred_eq_of_pos hp] using (pow_succ g p.pred))
have hunitg : IsUnit g :=
  by
    rcases hfac with hunit | hunit
    · exact hunit
    · exact (isUnit_of_pow (n:=p.pred) hunit)
have hunitpow : IsUnit (g ^ p) := (IsUnit.pow hunitg p)
exact h.1 hunitpow
```

**lean_error:** tail step 2/12 ('let g := map (↑(RingEquiv.symm (frobeniusEquiv R p))) f'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=856, out=418)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out _))
```

**lean_error:** tail step 1/1 ('exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out _))'): function expected at

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.1s, verify 0.2s, in=1606, out=669)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply not_irreducible_pow
exact (Nat.Prime.ne_one (Fact.out _))
```

**lean_error:** tail step 2/2 ('exact (Nat.Prime.ne_one (Fact.out _))'): function expected at

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.2s, in=1518, out=635)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply not_irreducible_pow
exact (Nat.Prime.ne_one (Fact.out _))
```

**lean_error:** tail step 2/2 ('exact (Nat.Prime.ne_one (Fact.out _))'): function expected at
