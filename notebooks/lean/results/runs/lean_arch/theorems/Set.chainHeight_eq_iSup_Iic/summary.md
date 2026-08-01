# Set.chainHeight_eq_iSup_Iic   (k=2, 3 tactics total)

file: `Mathlib/Order/Height.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 5.8s, in=340, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ofDual_inv_Ici, ofDual_inv_Iic]
congr with i
rw [ofDual_inv_inv]
```

**lean_error:** tail step 1/3 ('rw [ofDual_inv_Ici, ofDual_inv_Iic]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **success**  (gen 2.4s, verify 0.1s, in=308, out=156)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr 2
ext i
simp only [chainHeight, supₛ_image, iSup_image]
congr 2
ext c
simp only [mem_image, SetCoe.forall, mem_preimage, OrderIso.apply_symm_apply, mem_Iic, exists_prop]
constructor
rintro ⟨hc, hci⟩
exact ⟨ofDual ⁻¹' c, hc.image_ofDual, by simpa using hci⟩
rintro ⟨c, hc, hci⟩
exact ⟨c.map OrderIso.symm (ofDual : α ≃o αᵒᵈ), by simpa using hc, by simpa using hci⟩
simp_rw [← preimage_inter, ← preimage_Ici]
```

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 5.2s, verify 0.2s, in=329, out=330)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply le_antisymm
. intro i
  . intro h
  . simp only [mem_preimage, ofDual_eq]
  . intro h
  . simp only [mem_preimage, ofDual_eq]
  . rw [chainHeight_inter_Ici]
  . simp only [mem_preimage, ofDual_eq]
  . simp only [mem_preimage, ofDual_eq]
  . rw [chainHeight_inter_Iic]
  . simp only [mem_preimage, ofDual_eq]
  . apply le_antisymm
  . apply sup_le
  . intro i
    . intro h
    . simp only [mem_preimage, ofDual_eq]
    . intro h
    . simp only [mem_preimage, ofDual_eq]
    . rw [chainHeight_inter_Ici]
    . simp only [mem_preimage, ofDual_eq]
    .simp only [mem_preimage, ofDual_eq]
    .rw [chainHeight_inter_Iic]
    .simp only [mem_preimage, ofDual_eq]
  . apply sup_le
  . intro i
    . intro h
    . simp only [mem_preimage, ofDual_eq]
    . intro h
    . simp only [mem_preimage, ofDual_eq]
    . rw [chainHeight_inter_Ici]
    . simp only [mem_preimage, ofDual_eq]
    .simp only [mem_preimage, ofDual_eq]
    .rw [chainHeight_inter_Iic]
    .simp only [mem_preimage, ofDual_eq]
```

**lean_error:** tail step 2/34 ('. intro i'): unsolved goals
