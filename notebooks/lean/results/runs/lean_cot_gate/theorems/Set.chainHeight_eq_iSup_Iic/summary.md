# Set.chainHeight_eq_iSup_Iic   (k=2, 3 tactics total)

file: `Mathlib/Order/Height.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✓ ✓ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 161.7s, verify 0.1s, in=311, out=7478)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [preimage_ofDual_set]
apply supr_congr rfl
intro i
rw [preimage_ofDual_inter, preimage_ofDual_Iic_eq_Ici, preimage_ofDual_set]
```

**lean_error:** tail step 1/4 ('rw [preimage_ofDual_set]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 210.7s, verify 0.1s, in=311, out=9707)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← preimage_ofDual_Ici, ← preimage_ofDual_Iic]
apply supr_congr rfl
intro i
rw [chainHeight_image_ofDual, chainHeight_image_ofDual]
```

**lean_error:** tail step 1/4 ('rw [← preimage_ofDual_Ici, ← preimage_ofDual_Iic]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 215.5s, verify 0.1s, in=311, out=9947)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply supr_congr
intro i hi
have : ofDual ⁻¹' s ∩ Ici i = ofDual ⁻¹' (s ∩ Iic (ofDual i)) := by
  ext x
  simp only [Set.mem_preimage, Set.mem_inter_iff, Set.mem_Ici, ofDual_apply]
  constructor
  · rintro ⟨h1, h2⟩
    rw [← Dual.le_iff_le] at h2
    exact ⟨h1, h2⟩
  · rintro ⟨h1, h2⟩
    rw [Dual.le_iff_le] at h2
    exact ⟨h1, h2⟩
rw [this]
rfl
```

**lean_error:** tail step 1/14 ('apply supr_congr'): unknown identifier 'supr_congr'

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 216.3s, verify 0.1s, in=311, out=9995)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply supr_congr
intro i
intro hi
rw [← preimage_ofDual_inter_Ici hi, ← preimage_Iic]
apply congr_arg
apply supr_comp (fun j ↦ chainHeight (ofDual ⁻¹' (s ∩ Iic j))) (fun i ↦ ofDual i)
intro j
exact ⟨toDual j, by simp [mem_preimage]⟩
```

**lean_error:** tail step 1/8 ('apply supr_congr'): unknown identifier 'supr_congr'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.3s, verify 0.1s, in=311, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.4s, verify 0.1s, in=311, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.5s, verify 0.1s, in=311, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [← ofDual_Iic, preimage_inter]
```

**lean_error:** tail step 1/1 ('simp_rw [← ofDual_Iic, preimage_inter]'): unknown identifier 'ofDual_Iic'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.6s, verify 0.1s, in=311, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [← preimage_inter_of_inverse ofDual toDual, dual_Ici]
```

**lean_error:** tail step 1/1 ('simp_rw [← preimage_inter_of_inverse ofDual toDual, dual_Ici]'): unknown identifier 'preimage_inter_of_inverse'
