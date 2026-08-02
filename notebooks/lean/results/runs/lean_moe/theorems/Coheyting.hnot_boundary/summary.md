# Coheyting.hnot_boundary   (k=0, 1 tactics total)

file: `Mathlib/Order/Heyting/Boundary.lean`  

**Ground-truth tail (from k):**
```lean
rw [boundary, hnot_inf_distrib, sup_hnot_self]
```

**True premises at k:** `Coheyting.boundary`, `hnot_inf_distrib`, `sup_hnot_self`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | · | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.0s, verify 0.1s, in=278, out=689)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **incomplete**  (gen 257.6s, verify 0.1s, in=224, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exfalso
```

**final state (truncated):**
```
α : Type u_1
inst✝ : CoheytingAlgebra α
a✝ b a : α
⊢ False
```

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 13.1s, verify 0.1s, in=221, out=1425)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [noti]
```

**lean_error:** tail step 1/1 ('simp [noti]'): unknown identifier 'noti'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.0s, verify 1.3s, in=751, out=850)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Coheyting.boundary, hnot_inf_distrib]
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 18.7s, verify 0.2s, in=706, out=2128)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [boundary]
rw [hnot_inf_distrib]
rw [sup_hnot_self]
rfl
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 22.9s, verify 0.1s, in=692, out=2560)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Coheyting.boundary, hnot_inf_distrib]
simp [sup_hnot_self]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.3s, verify 3.3s, in=1245, out=949)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold Coheyting.boundary
  rw [hnot_inf_distrib]
  simpa using sup_hnot_self (￢ a)
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 26.1s, verify 0.2s, in=1215, out=3058)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [boundary]
rw [hnot_inf_distrib]
rw [sup_hnot_self]
```

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.7s, verify 0.2s, in=1183, out=557)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [boundary]
rw [hnot_inf_distrib]
exact sup_hnot_self _
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 10.7s, verify 0.3s, in=1203, out=1373)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Coheyting.boundary, hnot_inf_distrib] using sup_hnot_self (￢ a)
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 22.6s, verify 0.2s, in=1294, out=2573)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Coheyting.boundary]
rw [hnot_inf_distrib]
rw [sup_hnot_self]
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 8.2s, verify 0.1s, in=1193, out=826)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [boundary, hnot_inf_distrib, sup_hnot_self]
```
