# LinearMap.proj_comp_stdBasis   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/StdBasis.lean`  

**Ground-truth tail (from k):**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

**True premises at k:** `LinearMap.stdBasis_eq_pi_diag`, `LinearMap.proj_pi`

## Verdict matrix

| rung | llama-31-405b-base | llama-31-405b-lean-lora | nemotron-ultra-253b-base | nemotron-ultra-253b-lean-lora | qwen3-235b-a22b-base | qwen3-235b-a22b-lean-lora |
| --- | --- | --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | · | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ | ✘ | ✘ | · |
| `hint:3` | ✓ | ✓ | ✓ | ✓ | ✓ | · |
| `noise:3` | ✓ | ✓ | ✓ | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=308, out=48)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x,
rw [stdBasis_apply, LinearMap.comp_apply, proj_apply],
by_cases h : x = j,
simp only [h, if_true, eq_self_iff_true],
simp only [if_false, h],
```

**lean_error:** tail step 1/5 ('ext x,'): <stdin>:1:5: expected end of input

### `stepk:1` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=308, out=32)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← @comp_stdBasis R _ _ _ _ _ _ _ _ _ i j, stdBasis_same, LinearMap.comp_id]
```

**lean_error:** tail step 1/1 ('rw [← @comp_stdBasis R _ _ _ _ _ _ _ _ _ i j, stdBasis_same, LinearMap.comp_id]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.3s, in=297, out=82)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply LinearMap.ext
intro x
apply funext
intro k
simp [LinearMap.comp_apply, LinearMap.proj_apply, LinearMap.stdBasis_apply]
```

**lean_error:** tail step 3/5 ('apply funext'): tactic 'apply' failed, failed to unify

### `stepk:1` · nemotron-ultra-253b-lean-lora · rollout 0 → **incomplete**  (gen 1.2s, verify 0.3s, in=288, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply LinearMap.ext
intros
simp [stdBasis, proj, LinearMap.comp_apply, diag]
```

**final state (truncated):**
```
case h
R : Type u_1
ι : Type u_2
inst✝³ : Semiring R
φ : ι → Type u_3
inst✝² : (i : ι) → AddCommMonoid (φ i)
...
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 89.5s, verify 0.2s, in=285, out=5961)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
split_ifs
  simp [stdBasis_same, LinearMap.id_apply]
  simp [stdBasis_ne, LinearMap.zero_apply]
```

**lean_error:** tail step 2/4 ('split_ifs'): tactic 'split_ifs' failed, no if-then-else conditions to split

### `stepk:1` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=285, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.2s, verify 0.2s, in=687, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
rw [proj_pi]
```

### `hint:2` · llama-31-405b-lean-lora · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=687, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.2s, in=676, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
apply proj_pi
```

### `hint:2` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=667, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, LinearMap.comp_assoc]
apply LinearMap.proj_pi
```

**lean_error:** tail step 1/2 ('rw [stdBasis_eq_pi_diag, LinearMap.comp_assoc]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 27.1s, verify 0.1s, in=671, out=1634)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag j, proj_pi]
```

**lean_error:** tail step 1/1 ('rw [stdBasis_eq_pi_diag j, proj_pi]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 0.8s, verify 0.1s, in=671, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag]
```

**final state (truncated):**
```
R : Type u_1
ι : Type u_2
inst✝³ : Semiring R
φ : ι → Type u_3
inst✝² : (i : ι) → AddCommMonoid (φ i)
inst✝¹ : (i : ι) → Module R (φ i)
...
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.8s, verify 0.2s, in=1102, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
rw [proj_pi]
```

### `hint:3` · llama-31-405b-lean-lora · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=1102, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 4.7s, verify 0.2s, in=1091, out=348)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
rw [proj_pi]
```

### `hint:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **success**  (gen 0.8s, verify 0.2s, in=1082, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
apply proj_pi
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 46.3s, verify 0.1s, in=1089, out=2897)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 0.7s, verify 0.1s, in=1089, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag]
```

**final state (truncated):**
```
R : Type u_1
ι : Type u_2
inst✝³ : Semiring R
φ : ι → Type u_3
inst✝² : (i : ι) → AddCommMonoid (φ i)
inst✝¹ : (i : ι) → Module R (φ i)
...
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.0s, verify 0.2s, in=1126, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
rw [proj_pi]
```

### `noise:3` · llama-31-405b-lean-lora · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=1126, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.6s, verify 0.2s, in=1115, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
apply proj_pi
```

### `noise:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1106, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, LinearMap.comp_assoc, proj_pi, diag]
```

**lean_error:** tail step 1/1 ('rw [stdBasis_eq_pi_diag, LinearMap.comp_assoc, proj_pi, diag]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 41.3s, verify 0.1s, in=1113, out=2582)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag j], rw [proj_pi (diag j)]
```

**lean_error:** tail step 1/1 ('rw [stdBasis_eq_pi_diag j], rw [proj_pi (diag j)]'): <stdin>:1:26: expected end of input

### `noise:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 0.6s, verify 0.1s, in=1113, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag]
```

**final state (truncated):**
```
R : Type u_1
ι : Type u_2
inst✝³ : Semiring R
φ : ι → Type u_3
inst✝² : (i : ι) → AddCommMonoid (φ i)
inst✝¹ : (i : ι) → Module R (φ i)
...
```
