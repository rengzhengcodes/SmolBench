# LinearMap.proj_comp_stdBasis   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/StdBasis.lean`  

**Ground-truth tail (from k):**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

**True premises at k:** `LinearMap.stdBasis_eq_pi_diag`, `LinearMap.proj_pi`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-goedel | qwen3-lean-leannav | qwen3-lean-real |
| --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | · | · |
| `hint:3` | ✓ | ✓ | · | ✓ |
| `noise:3` | ✓ | · | · | · |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 125.2s, verify 0.2s, in=285, out=6860)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext r
rw [LinearMap.comp_apply, stdBasis_apply, proj_apply, Diag.apply]
split_ifs
· rfl
· rfl
```

**lean_error:** tail step 2/5 ('rw [LinearMap.comp_apply, stdBasis_apply, proj_apply, Diag.apply]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 6.3s, verify 0.4s, in=285, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [LinearMap.ext_iff, comp_apply, Function.diag_apply]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.ext_iff, comp_apply, Function.diag_apply]'): unknown identifier 'Function.diag_apply'

### `stepk:1` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=285, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=285, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 59.8s, verify 0.1s, in=671, out=3312)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:2` · qwen3-lean-goedel · rollout 0 → **success**  (gen 6.8s, verify 0.1s, in=671, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:2` · qwen3-lean-leannav · rollout 0 → **incomplete**  (gen 2.1s, verify 0.1s, in=671, out=14)

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

### `hint:2` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 0.9s, verify 0.1s, in=671, out=14)

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

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 32.3s, verify 0.2s, in=1089, out=1840)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
rw [proj_pi]
```

### `hint:3` · qwen3-lean-goedel · rollout 0 → **success**  (gen 6.3s, verify 0.1s, in=1089, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

### `hint:3` · qwen3-lean-leannav · rollout 0 → **incomplete**  (gen 2.2s, verify 0.8s, in=1089, out=14)

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

### `hint:3` · qwen3-lean-real · rollout 0 → **success**  (gen 1.5s, verify 0.1s, in=1089, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [stdBasis_eq_pi_diag, proj_pi]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 17.9s, verify 0.2s, in=1113, out=981)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
apply proj_pi
```

### `noise:3` · qwen3-lean-goedel · rollout 0 → **incomplete**  (gen 6.2s, verify 0.1s, in=1113, out=14)

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

### `noise:3` · qwen3-lean-leannav · rollout 0 → **incomplete**  (gen 3.0s, verify 0.1s, in=1113, out=14)

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

### `noise:3` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 1.0s, verify 0.5s, in=1113, out=14)

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
