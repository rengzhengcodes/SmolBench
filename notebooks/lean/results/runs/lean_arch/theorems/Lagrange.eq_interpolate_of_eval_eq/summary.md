# Lagrange.eq_interpolate_of_eval_eq   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Lagrange.lean`  

**Ground-truth tail (from k):**
```lean
exact interpolate_eq_of_values_eq_on _ _ eval_f
```

**True premises at k:** `Lagrange.interpolate_eq_of_values_eq_on`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.2s, in=339, out=31)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
apply funext
intro i
rw eval_f i (Finset.mem_coe.mpr (Finset.mem_univ i))
```

**lean_error:** tail step 2/4 ('apply funext'): ambiguous term, use fully qualified name, possible interpretations [@funext, @Polynomial.funext]

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.9s, in=313, out=42)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
funext i
rw [interpolate_apply]
rw [eval_f i]
· rw [interpolate_apply]
· exact hvs i.2
· exact hvs i.2
```

**lean_error:** tail step 3/7 ('rw [interpolate_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 49.2s, verify 0.1s, in=328, out=3131)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply interpolate_congr,
exact eval_f,
```

**lean_error:** tail step 1/2 ('apply interpolate_congr,'): <stdin>:1:23: expected end of input

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=574, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine' Lagrange.interpolate_eq_of_values_eq_on (fun i hi => _)
exact eval_f _ hi
```

**lean_error:** tail step 1/2 ("refine' Lagrange.interpolate_eq_of_values_eq_on (fun i hi => _)"): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.8s, verify 0.3s, in=537, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Lagrange.interpolate_eq_of_values_eq_on]
intro i hi
rw [eval_f i hi]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.3s, in=563, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply interpolate_eq_of_values_eq_on
intro i hi
exact (eval_f i hi).symm
```

**lean_error:** tail step 3/3 ('exact (eval_f i hi).symm'): type mismatch

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.5s, verify 0.3s, in=1564, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply interpolate_eq_of_values_eq_on
intro i hi
rw [eval_f _ hi]
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.3s, in=1515, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
congr
apply interpolate_eq_of_values_eq_on
intro i hi
exact eval_f i hi
```

**lean_error:** tail step 2/4 ('apply interpolate_eq_of_values_eq_on'): tactic 'apply' failed, failed to unify

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.0s, verify 0.3s, in=1553, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply interpolate_eq_of_values_eq_on
intro i hi
rw [eval_f i hi]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.6s, in=1593, out=10)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact interpolate_eq_of_values_eq_on eval_f
```

**lean_error:** tail step 1/1 ('exact interpolate_eq_of_values_eq_on eval_f'): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.2s, in=1670, out=7)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
congr
exact eval_f
```

**lean_error:** tail step 2/2 ('exact eval_f'): type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.3s, in=1582, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply interpolate_eq_of_values_eq_on
intro i hi
rw [eval_f i hi]
```
