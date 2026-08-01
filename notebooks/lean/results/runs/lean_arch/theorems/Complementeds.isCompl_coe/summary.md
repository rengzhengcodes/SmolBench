# Complementeds.isCompl_coe   (k=0, 1 tactics total)

file: `Mathlib/Order/Disjoint.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [isCompl_iff, disjoint_coe, codisjoint_coe]
```

**True premises at k:** `isCompl_iff`, `Complementeds.disjoint_coe`, `Complementeds.codisjoint_coe`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✓ |
| `hint:3` | ✘ | ✓ | ✓ |
| `noise:3` | ✘ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.2s, in=254, out=44)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  constructor
  · apply h.inf_eq
  · apply h.sup_eq
· intro h
  constructor
  · apply h.inf_eq
  · apply h.sup_eq
```

**lean_error:** tail step 2/9 ('· intro h'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=226, out=84)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← IsCompl.map (OrderIso.compl : α ≃o αᵒᵈ), IsCompl.compl_eq, IsCompl.compl_eq]
simp only [coe_compl, sup_compl_eq_top, inf_compl_eq_bot]
simp only [sup_eq_top_iff, inf_eq_bot_iff, ← compl_sup, ← compl_inf, compl_bot, compl_top]
```

**lean_error:** tail step 1/3 ('rw [← IsCompl.map (OrderIso.compl : α ≃o αᵒᵈ), IsCompl.compl_eq, IsCompl.compl_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 95.3s, verify 0.1s, in=243, out=5921)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Complementeds.isCompl_iff_eq_comp
```

**lean_error:** tail step 1/1 ('exact Complementeds.isCompl_iff_eq_comp'): unknown constant 'Complementeds.isCompl_iff_eq_comp'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=775, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isCompl_iff, disjoint_coe, codisjoint_coe]
exact Iff.rfl
```

**lean_error:** tail step 2/2 ('exact Iff.rfl'): type mismatch

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.8s, verify 0.2s, in=733, out=35)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff]
simp_rw [← Complementeds.disjoint_coe, ← Complementeds.codisjoint_coe]
rfl
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=764, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff, disjoint_coe, codisjoint_coe]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=1505, out=38)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isCompl_iff, disjoint_iff, codisjoint_iff, Complementeds.disjoint_coe, Complementeds.codisjoint_coe, isCompl_iff]
```

**lean_error:** tail step 1/1 ('rw [isCompl_iff, disjoint_iff, codisjoint_iff, Complementeds.disjoint_coe, Complementeds.codisjoint_coe, isCompl_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 1.0s, verify 0.2s, in=1463, out=35)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff]
simp_rw [← Complementeds.disjoint_coe, ← Complementeds.codisjoint_coe]
rfl
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=1494, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff, disjoint_coe, codisjoint_coe]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=1535, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isCompl_iff, disjoint_coe, codisjoint_coe]
exact Iff.rfl
```

**lean_error:** tail step 2/2 ('exact Iff.rfl'): type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.2s, in=1579, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff]
simp only [Complementeds.codisjoint_coe, Complementeds.disjoint_coe]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=1524, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isCompl_iff, isCompl_iff, disjoint_coe, codisjoint_coe]
```
