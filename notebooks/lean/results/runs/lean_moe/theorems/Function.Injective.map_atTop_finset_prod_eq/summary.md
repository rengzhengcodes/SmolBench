# Function.Injective.map_atTop_finset_prod_eq   (k=12, 13 tactics total)

file: `Mathlib/Order/Filter/AtTopBot.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨_, (image_subset_iff_subset_preimage _).1 ht, rfl⟩
```

**True premises at k:** `Finset.image_subset_iff_subset_preimage`, `rfl`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.8s, verify 0.1s, in=428, out=2188)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine ⟨Finset.preimage t g hg, ?_, ?_⟩
· intro x hx
  have hx' : g x ∈ Finset.image g s := by
    exact Finset.mem_image.mpr ⟨x, hx, rfl⟩
  have hx'' : g x ∈ t := ht hx'
  simpa [Finset.mem_preimage] using hx''
· rfl
```

**lean_error:** tail step 1/7 ('refine ⟨Finset.preimage t g hg, ?_, ?_⟩'): application type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 34.3s, verify 1.8s, in=1205, out=8228)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine' ⟨t.preimage g (hg.injOn _), ?_, ?_⟩
  · exact (image_subset_iff_subset_preimage (hg.injOn _)).1 ht
  · rfl
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 19.2s, verify 0.1s, in=2248, out=4434)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have hsub : s ⊆ t.preimage g (hg.injOn _) :=
  (Finset.image_subset_iff_subset_preimage (hg.injOn _)).1 ht
rfl
```

**lean_error:** tail step 1/3 ('have hsub : s ⊆ t.preimage g (hg.injOn _) :='): <stdin>:1:44: unexpected end of input

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 26.2s, verify 0.2s, in=2142, out=6208)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using rfl
```

**lean_error:** tail step 1/1 ('simpa using rfl'): type mismatch
