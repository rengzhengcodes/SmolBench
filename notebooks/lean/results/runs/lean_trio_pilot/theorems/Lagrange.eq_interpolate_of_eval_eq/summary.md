# Lagrange.eq_interpolate_of_eval_eq   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Lagrange.lean`  

**Ground-truth tail (from k):**
```lean
exact interpolate_eq_of_values_eq_on _ _ eval_f
```

**True premises at k:** `Lagrange.interpolate_eq_of_values_eq_on`

## Verdict matrix

| rung | llama-31-405b-base | llama-31-405b-lean-lora | nemotron-ultra-253b-base | nemotron-ultra-253b-lean-lora | qwen3-235b-a22b-base | qwen3-235b-a22b-lean-lora |
| --- | --- | --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | ✘ | ✓ | ✓ | ✘ |
| `hint:3` | ✓ | ✘ | ✓ | ✓ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✓ | ✓ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.6s, in=339, out=31)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
apply funext
intro i
rw eval_f i (Finset.mem_coe.mpr (Finset.mem_univ i))
```

**lean_error:** tail step 2/4 ('apply funext'): ambiguous term, use fully qualified name, possible interpretations [@funext, @Polynomial.funext]

### `stepk:1` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=339, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr with i hi using eval_f i hi
```

**lean_error:** tail step 1/1 ('congr with i hi using eval_f i hi'): <stdin>:1:16: expected end of input

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=328, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
exact funext (λ i, eval_f i (finset.mem_univ _))
```

**lean_error:** tail step 2/2 ('exact funext (λ i, eval_f i (finset.mem_univ _))'): <stdin>:1:17: expected '↦', '=>'

### `stepk:1` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=319, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
exact funext (λ i, eval_f i (Finset.mem_univ _))
```

**lean_error:** tail step 2/2 ('exact funext (λ i, eval_f i (Finset.mem_univ _))'): <stdin>:1:17: expected '↦', '=>'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 129.0s, verify 0.1s, in=317, out=6952)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply interpolate_congr
exact eval_f
```

**lean_error:** tail step 1/2 ('apply interpolate_congr'): unknown identifier 'interpolate_congr'

### `stepk:1` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 1.8s, verify 0.1s, in=317, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
```

**final state (truncated):**
```
case h.e_6.h
F : Type u_1
inst✝¹ : Field F
ι : Type u_2
inst✝ : DecidableEq ι
s t : Finset ι
...
```

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=574, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine' Lagrange.interpolate_eq_of_values_eq_on (fun i hi => _)
exact eval_f _ hi
```

**lean_error:** tail step 1/2 ("refine' Lagrange.interpolate_eq_of_values_eq_on (fun i hi => _)"): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=574, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact interpolate_eq_of_values_eq_on eval_f
```

**lean_error:** tail step 1/1 ('exact interpolate_eq_of_values_eq_on eval_f'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.3s, in=563, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply interpolate_eq_of_values_eq_on
intro i hi
exact (eval_f i hi).symm
```

**lean_error:** tail step 3/3 ('exact (eval_f i hi).symm'): type mismatch

### `hint:2` · nemotron-ultra-253b-lean-lora · rollout 0 → **success**  (gen 1.0s, verify 0.2s, in=554, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply interpolate_eq_of_values_eq_on
exact eval_f
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 9.6s, verify 0.2s, in=552, out=488)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply interpolate_eq_of_values_eq_on
exact eval_f
```

### `hint:2` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=552, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact interpolate_eq_of_values_eq_on fun i => eval_f i
```

**lean_error:** tail step 1/1 ('exact interpolate_eq_of_values_eq_on fun i => eval_f i'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.9s, verify 0.3s, in=1564, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Lagrange.interpolate_eq_of_values_eq_on
exact eval_f
```

### `hint:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1564, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact interpolate_eq_of_values_eq_on eval_f
```

**lean_error:** tail step 1/1 ('exact interpolate_eq_of_values_eq_on eval_f'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.3s, in=1553, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply interpolate_eq_of_values_eq_on
intro i hi
rw [eval_f i hi]
```

### `hint:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **success**  (gen 1.1s, verify 0.2s, in=1544, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply interpolate_eq_of_values_eq_on
exact eval_f
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 92.4s, verify 0.2s, in=1550, out=4829)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply interpolate_eq_of_values_eq_on (fun i hi => (eval_f i hi).symm)
```

**lean_error:** tail step 1/1 ('apply interpolate_eq_of_values_eq_on (fun i hi => (eval_f i hi).symm)'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 2.1s, verify 0.1s, in=1550, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact interpolate_eq_of_values_eq_on fun i hi => eval_f i hi
```

**lean_error:** tail step 1/1 ('exact interpolate_eq_of_values_eq_on fun i hi => eval_f i hi'): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1593, out=10)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact interpolate_eq_of_values_eq_on eval_f
```

**lean_error:** tail step 1/1 ('exact interpolate_eq_of_values_eq_on eval_f'): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1593, out=10)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact interpolate_eq_of_values_eq_on eval_f
```

**lean_error:** tail step 1/1 ('exact interpolate_eq_of_values_eq_on eval_f'): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.0s, verify 0.3s, in=1582, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply interpolate_eq_of_values_eq_on
intro i hi
rw [eval_f i hi]
```

### `noise:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **success**  (gen 0.7s, verify 0.2s, in=1573, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply interpolate_eq_of_values_eq_on
exact eval_f
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 8.7s, verify 0.2s, in=1574, out=430)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply interpolate_eq_of_values_eq_on
exact eval_f
```

### `noise:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=1574, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact interpolate_eq_of_values_eq_on fun i => eval_f i
```

**lean_error:** tail step 1/1 ('exact interpolate_eq_of_values_eq_on fun i => eval_f i'): typeclass instance problem is stuck, it is often due to metavariables
