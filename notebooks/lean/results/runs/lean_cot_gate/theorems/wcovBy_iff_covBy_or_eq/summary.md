# wcovBy_iff_covBy_or_eq   (k=0, 1 tactics total)

file: `Mathlib/Order/Cover.lean`  

**Ground-truth tail (from k):**
```lean
rw [le_antisymm_iff, wcovBy_iff_covBy_or_le_and_le]
```

**True premises at k:** `le_antisymm_iff`, `wcovBy_iff_covBy_or_le_and_le`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ · ✘ · |
| `hint:2` | ✓ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ ✓ |
| `noise:3` | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.7s, verify 0.1s, in=229, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [covBy, or_comm]
```

**lean_error:** tail step 1/1 ('simp [covBy, or_comm]'): unknown identifier 'covBy'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.8s, verify 0.1s, in=229, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [CovBy, or_comm]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝ : PartialOrder α
a b c : α
⊢ a ⩿ b ↔ a = b ∨ a < b ∧ ∀ ⦃c : α⦄, a < c → ¬c < b
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.9s, verify 0.1s, in=229, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Covby, not_lt]
```

**lean_error:** tail step 1/1 ('simp [Covby, not_lt]'): unknown identifier 'Covby'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 0.9s, verify 0.1s, in=229, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [CovBy, or_comm]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝ : PartialOrder α
a b c : α
⊢ a ⩿ b ↔ a = b ∨ a < b ∧ ∀ ⦃c : α⦄, a < c → ¬c < b
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=644, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.2s, verify 0.1s, in=644, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.6s, verify 0.1s, in=644, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.7s, verify 0.1s, in=644, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=786, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.4s, verify 0.1s, in=786, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.5s, verify 0.1s, in=786, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.6s, verify 0.1s, in=786, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=810, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.2s, verify 0.1s, in=810, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.8s, verify 0.1s, in=810, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.7s, verify 0.1s, in=810, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [wcovBy_iff_covBy_or_le_and_le, le_antisymm_iff]
```
