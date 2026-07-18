# not_irreducible_expand   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/Perfect.lean`  

**Ground-truth tail (from k):**
```lean
exact not_irreducible_pow (Fact.out : p.Prime).ne_one
```

**True premises at k:** `not_irreducible_pow`, `Fact.out`, `Nat.Prime.ne_one`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=327, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact map_irreducible_pow_frobenius R p f
```

**lean_error:** tail step 1/1 ('exact map_irreducible_pow_frobenius R p f'): unknown identifier 'map_irreducible_pow_frobenius'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=327, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact not_irreducible_pow _ one_lt_prime_iff.mp (Fact.out ‹_›).one_lt
```

**lean_error:** tail step 1/1 ('exact not_irreducible_pow _ one_lt_prime_iff.mp (Fact.out ‹_›).one_lt'): unknown identifier 'one_lt_prime_iff.mp'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.8s, verify 0.1s, in=327, out=37)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact irreducible_pow.mp (irreducible_map_iff frobeniusEquiv.symm).mpr (frobeniusEquiv _ p).injective
```

**lean_error:** tail step 1/1 ('exact irreducible_pow.mp (irreducible_map_iff frobeniusEquiv.symm).mpr (frobeniusEquiv _ p).injective'): unknown identifier 'irreducible_pow.mp'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=327, out=62)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (map (frobeniusEquiv R p).symm f).not_irreducible_pow _ one_lt_pow _ (Nat.pos_iff_ne_zero.mpr
  (pow_ne_zero _ (Nat.prime_iff.mpr ‹_›).ne_zero))
```

**lean_error:** tail step 1/2 ('exact (map (frobeniusEquiv R p).symm f).not_irreducible_pow _ one_lt_pow _ (Nat.pos_iff_ne_zero.mpr'): <stdin>:1:99: unexpected end of input; expected ')', ',' or ':'

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.0s, verify 0.1s, in=741, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact not_irreducible_pow (Fact.out ‹p.Prime›).ne_one
```

**lean_error:** tail step 1/1 ('exact not_irreducible_pow (Fact.out ‹p.Prime›).ne_one'): function expected at

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.1s, verify 0.1s, in=741, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact not_irreducible_pow (Nat.Prime.ne_one ‹_›)
```

**lean_error:** tail step 1/1 ('exact not_irreducible_pow (Nat.Prime.ne_one ‹_›)'): tactic 'assumption' failed

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=741, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out ‹Fact _›))
```

**lean_error:** tail step 1/1 ('exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out ‹Fact _›))'): function expected at

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.7s, verify 0.1s, in=741, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out ‹p.Prime›))
```

**lean_error:** tail step 1/1 ('exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out ‹p.Prime›))'): function expected at

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.9s, verify 0.1s, in=1444, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_irreducible_pow (Nat.Prime.ne_one ‹_›)
```

**lean_error:** tail step 1/1 ('exact not_irreducible_pow (Nat.Prime.ne_one ‹_›)'): tactic 'assumption' failed

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.0s, verify 0.1s, in=1444, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_irreducible_pow (Fact.out ‹p.Prime›).ne_one
```

**lean_error:** tail step 1/1 ('exact not_irreducible_pow (Fact.out ‹p.Prime›).ne_one'): function expected at

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.1s, verify 0.1s, in=1444, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out ‹_›))
```

**lean_error:** tail step 1/1 ('exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out ‹_›))'): function expected at

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=1444, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out ‹_›))
```

**lean_error:** tail step 1/1 ('exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out ‹_›))'): function expected at

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=1468, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact not_irreducible_pow (Nat.Prime.ne_one ‹_›)
```

**lean_error:** tail step 1/1 ('exact not_irreducible_pow (Nat.Prime.ne_one ‹_›)'): tactic 'assumption' failed

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.1s, in=1468, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact not_irreducible_pow (Fact.out ‹p.Prime›).ne_one
```

**lean_error:** tail step 1/1 ('exact not_irreducible_pow (Fact.out ‹p.Prime›).ne_one'): function expected at

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1468, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out ‹_›))
```

**lean_error:** tail step 1/1 ('exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out ‹_›))'): function expected at

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=1468, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out ‹_›))
```

**lean_error:** tail step 1/1 ('exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out ‹_›))'): function expected at
