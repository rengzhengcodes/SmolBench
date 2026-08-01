# Polynomial.monic_generator_eq_minpoly   (k=5, 6 tactics total)

file: `Mathlib/LinearAlgebra/AnnihilatingPolynomial.lean`  

**Ground-truth tail (from k):**
```lean
apply monic_annIdealGenerator _ _ ((Associated.ne_zero_iff p_gen).mp h)
```

**True premises at k:** `Polynomial.monic_annIdealGenerator`, `Associated.ne_zero_iff`, `Iff.mp`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.8s, verify 0.1s, in=299, out=36)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw Associated.symm at p_gen,
cases p_gen with u hu,
rw ←hu at p_monic,
exact (monic_units_mul_iff _).mp p_monic
```

**lean_error:** tail step 1/4 ('rw Associated.symm at p_gen,'): <stdin>:1:3: expected '['

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=273, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← associated_iff_eq_right p_gen]
exact p_monic
```

**lean_error:** tail step 1/2 ('rw [← associated_iff_eq_right p_gen]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.3s, in=288, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Associated] at p_gen,
exact p_monic
```

**lean_error:** tail step 1/2 ('rw [Associated] at p_gen,'): <stdin>:1:24: expected end of input

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=792, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Polynomial.monic_annIdealGenerator a (Iff.mp (Associated.ne_zero_iff p_gen) h)
```

**lean_error:** tail step 1/1 ('exact Polynomial.monic_annIdealGenerator a (Iff.mp (Associated.ne_zero_iff p_gen) h)'): application type mismatch

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=759, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply monic_annIdealGenerator a
rw [← p_gen, Associated.ne_zero_iff]
exact h```
```

**lean_error:** tail step 1/3 ('apply monic_annIdealGenerator a'): application type mismatch

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=781, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Polynomial.monic_annIdealGenerator
apply mt (Associated.ne_zero_iff p_gen).mp
exact h
```

**lean_error:** tail step 2/3 ('apply mt (Associated.ne_zero_iff p_gen).mp'): tactic 'apply' failed, failed to unify

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 2.2s, in=1644, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Polynomial.monic_annIdealGenerator _ (Iff.mp (Associated.ne_zero_iff p_gen) h)
```

**lean_error:** tail step 1/1 ('apply Polynomial.monic_annIdealGenerator _ (Iff.mp (Associated.ne_zero_iff p_gen) h)'): tactic 'apply' failed, failed to unify

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.1s, in=1611, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply monic_annIdealGenerator a
rw [Ne.def, ← Associated.ne_zero_iff p_gen]
exact h
```

**lean_error:** tail step 1/3 ('apply monic_annIdealGenerator a'): application type mismatch

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.3s, in=1633, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Polynomial.monic_annIdealGenerator
apply Iff.mp
apply Associated.ne_zero_iff p_gen
exact h
```

**lean_error:** tail step 3/4 ('apply Associated.ne_zero_iff p_gen'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.6s, verify 0.2s, in=1669, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Polynomial.monic_annIdealGenerator a (Iff.mp (Associated.ne_zero_iff p_gen) h)
```

**lean_error:** tail step 1/1 ('exact Polynomial.monic_annIdealGenerator a (Iff.mp (Associated.ne_zero_iff p_gen) h)'): application type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 1.4s, in=1735, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply monic_annIdealGenerator a
rw [← Associated.ne_zero_iff p_gen, ← h]
trivial
```

**lean_error:** tail step 1/3 ('apply monic_annIdealGenerator a'): application type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=1658, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply monic_annIdealGenerator
refine (ne_zero_iff.mp (Associated.ne_zero_iff p_gen)).mpr h
```

**lean_error:** tail step 2/2 ('refine (ne_zero_iff.mp (Associated.ne_zero_iff p_gen)).mpr h'): unknown identifier 'ne_zero_iff.mp'
