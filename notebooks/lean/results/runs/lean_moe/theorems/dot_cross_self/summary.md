# dot_cross_self   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/CrossProduct.lean`  

**Ground-truth tail (from k):**
```lean
rw [← cross_anticomm, Matrix.dotProduct_neg, dot_self_cross, neg_zero]
```

**True premises at k:** `cross_anticomm`, `Matrix.dotProduct_neg`, `dot_self_cross`, `neg_zero`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | · | ✘ | ✓ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | · |
| `noise:3` | · | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 4.5s, verify 0.1s, in=288, out=993)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ w 0 * (crossProduct v) w 0 + w 1 * (crossProduct v) w 1 + w 2 * (crossProduct v) w 2 = 0
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 32.7s, verify 0.1s, in=233, out=4146)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [dotProduct_comm]
exact dotProduct_crossProduct_eq_zero_right v w
```

**lean_error:** tail step 2/2 ('exact dotProduct_crossProduct_eq_zero_right v w'): unknown identifier 'dotProduct_crossProduct_eq_zero_right'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.5s, verify 0.4s, in=233, out=660)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [crossProduct, dotProduct, Fin.sum_univ_succ]
ring
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.2s, verify 0.1s, in=824, out=1157)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [←cross_anticomm v w, Matrix.dotProduct_neg, dot_self_cross]
```

**lean_error:** tail step 1/1 ('simpa [←cross_anticomm v w, Matrix.dotProduct_neg, dot_self_cross]'): tactic 'assumption' failed

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 9.0s, verify 0.1s, in=797, out=1007)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [cross_anticomm]
rw [Matrix.dotProduct_neg]
rw [dot_self_cross]
simp
```

**lean_error:** tail step 1/4 ('rw [cross_anticomm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.9s, verify 0.1s, in=785, out=684)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← cross_anticomm v w]
rw [Matrix.dotProduct_neg]
rw [dot_self_cross]
simp
```

**lean_error:** tail step 1/4 ('rw [← cross_anticomm v w]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.7s, verify 0.1s, in=1710, out=2795)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [cross_anticomm, dotProduct_neg] using dot_self_cross w v
```

**lean_error:** tail step 1/1 ('simpa [cross_anticomm, dotProduct_neg] using dot_self_cross w v'): type mismatch

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 39.5s, verify 0.1s, in=1708, out=5086)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
calc
  w ⬝ᵥ (v ×₃ w) = w ⬝ᵥ (-(w ×₃ v)) := by
    have h : v ×₃ w = - (w ×₃ v) := by
      have h₁ : -(v ×₃ w) = w ×₃ v := cross_anticomm v w
      have h₂ : v ×₃ w = - (w ×₃ v) := by
        rw [← h₁]
        <;> simp [neg_neg]
      exact h₂
    rw [h]
  _ = - (w ⬝ᵥ (w ×₃ v)) := by rw [Matrix.dotProduct_neg]
  _ = -0 := by
    have h : w ⬝ᵥ (w ×₃ v) = 0 := dot_self_cross w v
    rw [h]
  _ = 0 := by simp
```

**lean_error:** tail step 1/14 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.3s, verify 0.2s, in=1686, out=504)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← cross_anticomm]
simp [Matrix.dotProduct_neg, dot_self_cross]
```

**final state (truncated):**
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ w 0 * (crossProduct v) w 0 + w 1 * (crossProduct v) w 1 + w 2 * (crossProduct v) w 2 = 0
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 4.1s, verify 0.1s, in=1633, out=901)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [cross_anticomm, dotProduct_neg, dot_self_cross]
```

**final state (truncated):**
```
R : Type u_1
inst✝ : CommRing R
v w : Fin 3 → R
⊢ w 0 * (crossProduct v) w 0 + w 1 * (crossProduct v) w 1 + w 2 * (crossProduct v) w 2 = 0
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 32.6s, verify 0.1s, in=1852, out=4147)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h : crossProduct v w = -(crossProduct w v) := by
  have h1 : -(crossProduct v w) = crossProduct w v := cross_anticomm v w
  have h2 : crossProduct v w = -(crossProduct w v) := by
    calc
      crossProduct v w = -(-(crossProduct v w)) := by ring
      _ = -(crossProduct w v) := by rw [h1]
  exact h2
calc
  w ⬝ᵥ crossProduct v w = w ⬝ᵥ (-(crossProduct w v)) := by rw [h]
  _ = -(w ⬝ᵥ crossProduct w v) := by rw [Matrix.dotProduct_neg]
  _ = -(0) := by rw [dot_self_cross w v]
  _ = 0 := by simp
```

**lean_error:** tail step 1/12 ('have h : crossProduct v w = -(crossProduct w v) := by'): <stdin>:1:53: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 10.8s, verify 0.5s, in=1686, out=1170)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← cross_anticomm w v]
rw [Matrix.dotProduct_neg]
rw [dot_self_cross]
simp
```
