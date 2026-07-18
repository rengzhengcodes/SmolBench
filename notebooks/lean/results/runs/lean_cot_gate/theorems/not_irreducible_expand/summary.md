# not_irreducible_expand   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/Perfect.lean`  

**Ground-truth tail (from k):**
```lean
exact not_irreducible_pow (Fact.out : p.Prime).ne_one
```

**True premises at k:** `not_irreducible_pow`, `Fact.out`, `Nat.Prime.ne_one`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✓ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✓ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 183.0s, verify 0.1s, in=327, out=8422)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
set g := map (RingEquiv.symm (frobeniusEquiv R p)) f
by_cases hunit : is_unit g
{ apply not_irreducible_of_is_unit (is_unit_pow p hunit) }
{ apply not_irreducible_of_reducible
  use [g, g ^ (p - 1)]
  split
  { rw pow_succ' }
  split
  { exact hunit }
  { apply mt is_unit_of_power hunit } }
```

**lean_error:** tail step 1/10 ('set g := map (RingEquiv.symm (frobeniusEquiv R p)) f'): typeclass instance problem is stuck, it is often due to metavariables

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 220.4s, verify 0.1s, in=327, out=10115)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h1 : 1 < p := Nat.prime.one_lt inst✝².1,
apply not_irreducible_pow _ h1
```

**lean_error:** tail step 1/2 ('have h1 : 1 < p := Nat.prime.one_lt inst✝².1,'): <stdin>:1:40: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 226.1s, verify 0.1s, in=327, out=10382)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
by_cases hg : IsUnit (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f),  
  exact not_irreducible_of_unit hg,  
  apply not_irreducible_of_reducible,  
  apply reducible_of_factor,  
  use [map (↑(RingEquiv.symm (frobeniusEquiv R p))) f, map (↑(RingEquiv.symm (frobeniusEquiv R p))) f ^ (p - 1)],  
  split,  
  exact hg,  
  intro hunit,  
  exact hg (is_unit_of_pow_is_unit (p - 1) hunit)
```

**lean_error:** tail step 1/9 ('by_cases hg : IsUnit (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f),'): <stdin>:1:69: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 277.8s, verify 0.1s, in=327, out=12876)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [map_pow]
apply not_irreducible_pow
exact Nat.succ_le_of_lt (by norm_num : 1 < p)
```

**lean_error:** tail step 1/3 ('rw [map_pow]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

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

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 57.0s, verify 0.1s, in=741, out=2590)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have hp : p ≠ 1 := Nat.Prime.ne_one (Fact.out inst✝²)
apply not_irreducible_pow hp
```

**lean_error:** tail step 1/2 ('have hp : p ≠ 1 := Nat.Prime.ne_one (Fact.out inst✝²)'): <stdin>:1:50: expected token

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 63.5s, verify 0.1s, in=741, out=2915)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have hp := Fact.out (Nat.Prime p) inst✝²
have hn := hp.ne_one
apply not_irreducible_pow hn
```

**lean_error:** tail step 1/3 ('have hp := Fact.out (Nat.Prime p) inst✝²'): <stdin>:1:38: expected end of input

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 78.2s, verify 0.1s, in=741, out=3631)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply not_irreducible_pow (Nat.Prime.ne_one (Fact.out inst✝²))
```

**lean_error:** tail step 1/1 ('apply not_irreducible_pow (Nat.Prime.ne_one (Fact.out inst✝²))'): <stdin>:1:58: expected token

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 79.9s, verify 0.2s, in=741, out=3706)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply not_irreducible_pow
exact Nat.Prime.ne_one inst✝².1
```

**lean_error:** tail step 2/2 ('exact Nat.Prime.ne_one inst✝².1'): <stdin>:1:27: expected end of input

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

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 27.9s, verify 0.2s, in=1444, out=934)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply not_irreducible_pow
exact Nat.Prime.ne_one (Fact.out inst✝²)
```

**lean_error:** tail step 2/2 ('exact Nat.Prime.ne_one (Fact.out inst✝²)'): <stdin>:1:37: expected token

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 38.3s, verify 0.3s, in=1444, out=458)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply not_irreducible_pow
apply Nat.Prime.ne_one
exact Fact.out inst✝²
```

**lean_error:** tail step 3/3 ('exact Fact.out inst✝²'): <stdin>:1:19: expected end of input

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 54.7s, verify 0.1s, in=1444, out=1578)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply not_irreducible_pow (Nat.Prime.ne_one (Fact.out inst✝²))
```

**lean_error:** tail step 1/1 ('apply not_irreducible_pow (Nat.Prime.ne_one (Fact.out inst✝²))'): <stdin>:1:58: expected token

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 90.7s, verify 0.1s, in=1444, out=2479)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact not_irreducible_pow (Nat.Prime.ne_one (Fact.out))
```

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

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 7.4s, verify 0.3s, in=1468, out=351)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply not_irreducible_pow
apply Nat.Prime.ne_one
exact Fact.out inst✝² 0
```

**lean_error:** tail step 3/3 ('exact Fact.out inst✝² 0'): <stdin>:1:19: expected end of input

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 19.0s, verify 0.2s, in=1468, out=887)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply not_irreducible_pow
exact Nat.Prime.ne_one inst✝²
```

**lean_error:** tail step 2/2 ('exact Nat.Prime.ne_one inst✝²'): <stdin>:1:27: expected end of input

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 48.7s, verify 0.1s, in=1468, out=2215)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply not_irreducible_pow (Nat.Prime.ne_one Fact.out)
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 80.0s, verify 0.2s, in=1468, out=3717)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply not_irreducible_pow
exact (Fact.out inst✝²).ne_one
```

**lean_error:** tail step 2/2 ('exact (Fact.out inst✝²).ne_one'): <stdin>:1:20: expected token

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
