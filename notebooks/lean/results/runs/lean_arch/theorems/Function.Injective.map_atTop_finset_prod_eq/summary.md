# Function.Injective.map_atTop_finset_prod_eq   (k=12, 13 tactics total)

file: `Mathlib/Order/Filter/AtTopBot.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨_, (image_subset_iff_subset_preimage _).1 ht, rfl⟩
```

**True premises at k:** `Finset.image_subset_iff_subset_preimage`, `rfl`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.1s, verify 0.1s, in=386, out=120)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨Finset.preimage t g, _⟩
simp
constructor
· exact subset_preimage g ht
· apply prod_bij
  · exact λ _ _ => id
  · exact λ _ _ => id
  · exact λ _ _ _ _ => id
  · exact λ x hx, (mem_preimage.mp hx).2
  · exact λ x hx, mem_preimage.mpr ⟨_, hx, rfl⟩
  · exact λ _ _ _ _ h, h
  · exact λ _ _ _ _ h, h
```

**lean_error:** tail step 1/12 ("refine' ⟨Finset.preimage t g, _⟩"): application type mismatch

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=353, out=60)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine ⟨Finset.preimage t g ⋯, fun x hx => Finset.mem_preimage.mpr <| ht <| Finset.mem_image_of_mem g hx, ?_⟩
rw [Finset.prod_preimage' g hg]
simp only [Function.comp_apply]
```

**lean_error:** tail step 1/3 ('refine ⟨Finset.preimage t g ⋯, fun x hx => Finset.mem_preimage.mpr <| ht <| Finset.mem_image_of_mem g hx, ?_⟩'): internal exception #7

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=375, out=85)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
choose u' using Finset.exists_subset_of_range_subset_image_preimage hg,
exact ⟨u', subset.trans (subset.refl s) u'.subset, _⟩,
rw [← Finset.prod_image_of_inj_on hg s, ← Finset.prod_image_of_inj_on hg u'],
simpa only [Finset.image_preimage, ht] using (u'.prop).2
```

**lean_error:** tail step 1/4 ("choose u' using Finset.exists_subset_of_range_subset_image_preimage hg,"): <stdin>:1:70: expected end of input

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1116, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Finset.image_subset_iff_subset_preimage (hg.injOn _)
exact rfl
```

**lean_error:** tail step 1/2 ('exact Finset.image_subset_iff_subset_preimage (hg.injOn _)'): type mismatch

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.4s, in=1083, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Finset.image_subset_iff_subset_preimage (hg.injOn _)]
exact ht
rfl
```

**lean_error:** tail step 1/3 ('rw [Finset.image_subset_iff_subset_preimage (hg.injOn _)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 5.7s, verify 0.2s, in=1105, out=320)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Finset.image_subset_iff_subset_preimage (hg.injOn _)
exact subset_preimage
```

**lean_error:** tail step 1/2 ('apply Finset.image_subset_iff_subset_preimage (hg.injOn _)'): tactic 'apply' failed, failed to unify

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.0s, verify 0.1s, in=2117, out=79)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Finset.image_subset_iff_subset_preimage (hg.injOn _)
exact rfl
exact subset_preimage _ _ 
exact prod_subset (subset_union_right _ _) fun y hy hyt => hf y (mt _ hyt)
exact fun ⟨x, rfl⟩ => ⟨x, ht (Finset.mem_preimage.2 <| hy.resolve_left hyt), rfl⟩
```

**lean_error:** tail step 1/5 ('exact Finset.image_subset_iff_subset_preimage (hg.injOn _)'): type mismatch

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=2092, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Finset.image_subset_iff_subset_preimage (hg.injOn _)]
exact ht
exact rfl
```

**lean_error:** tail step 1/3 ('rw [Finset.image_subset_iff_subset_preimage (hg.injOn _)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=2106, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Finset.image_subset_iff_subset_preimage (hg.injOn _)
exact subset_preimage
exact rfl
```

**lean_error:** tail step 1/3 ('apply Finset.image_subset_iff_subset_preimage (hg.injOn _)'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=2143, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Finset.image_subset_iff_subset_preimage (hg.injOn _)]
exact ⟨s, rfl, rfl⟩
```

**lean_error:** tail step 1/2 ('rw [Finset.image_subset_iff_subset_preimage (hg.injOn _)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=2225, out=32)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Finset.image_subset_iff_subset_preimage (hg.injOn _)]
exact ht
exact Finset.subset_union_left _ _
rfl
```

**lean_error:** tail step 1/4 ('rw [Finset.image_subset_iff_subset_preimage (hg.injOn _)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=2132, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Finset.image_subset_iff_subset_preimage (hg.injOn _)
exact rfl
```

**lean_error:** tail step 1/2 ('apply Finset.image_subset_iff_subset_preimage (hg.injOn _)'): tactic 'apply' failed, failed to unify
