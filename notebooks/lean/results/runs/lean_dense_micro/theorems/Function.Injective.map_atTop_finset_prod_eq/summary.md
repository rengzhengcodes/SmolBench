# Function.Injective.map_atTop_finset_prod_eq   (k=12, 13 tactics total)

file: `Mathlib/Order/Filter/AtTopBot.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨_, (image_subset_iff_subset_preimage _).1 ht, rfl⟩
```

**True premises at k:** `Finset.image_subset_iff_subset_preimage`, `rfl`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 | llama-lean-fenced-micro-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✓ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.9s, verify 0.1s, in=386, out=45)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine ⟨Finset.preimage t g, _⟩
constructor
· exact Finset.subset_preimage g ht
· simp only [Finset.prod_preimage, Finset.mem_preimage, hf]
```

**lean_error:** tail step 1/4 ('refine ⟨Finset.preimage t g, _⟩'): internal exception #7

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 2.1s, verify 0.1s, in=386, out=54)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use s ∪ᵢ Finset.preimage t g
split
simp
rw [Finset.prod_union, Finset.prod_image]
simp [Finset.preimage_image_eq _ hg]
simp [hf]
simp [Finset.prod_const_one]
```

**lean_error:** tail step 1/7 ('use s ∪ᵢ Finset.preimage t g'): <stdin>:1:7: expected token

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.1s, in=386, out=81)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨Finset.preimage t g, _⟩
simp
constructor
· exact subset_preimage_image _ _
· refine' Finset.prod_subset _ _ _
  · intro x hx
    simp
  · intro x hx
    simp
  · intro x hx hgx
    exact hf _ (not_mem_range_of_mem_preimage _ _ _ hgx)
```

**lean_error:** tail step 1/11 ("refine' ⟨Finset.preimage t g, _⟩"): application type mismatch

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 2.6s, verify 0.1s, in=386, out=87)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine ⟨Finset.preimage t g, _⟩
simp only [Finset.subset_preimage_iff, ht, Finset.image_subset_iff]
refine prod_congr rfl _
intros x hx
rw [Finset.mem_preimage] at hx
cases hx
rw [hf]
rw [Finset.mem_image] at hx
obtain ⟨x', hx', rfl⟩ := hx
exact hx'
```

**lean_error:** tail step 1/10 ('refine ⟨Finset.preimage t g, _⟩'): internal exception #7

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.0s, verify 0.1s, in=386, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨s, Finset.Subset.refl _, rfl⟩
```

**lean_error:** tail step 1/1 ('exact ⟨s, Finset.Subset.refl _, rfl⟩'): application type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=386, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨s, subset.rfl, (prod_finset_preimage_of_mem _ ht).symm⟩
```

**lean_error:** tail step 1/1 ('exact ⟨s, subset.rfl, (prod_finset_preimage_of_mem _ ht).symm⟩'): unknown identifier 'subset.rfl'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=386, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨s, Finset.Subset.refl _, (prod_finset_preimage_of_not_mem_support _ _ _).symm⟩
```

**lean_error:** tail step 1/1 ('exact ⟨s, Finset.Subset.refl _, (prod_finset_preimage_of_not_mem_support _ _ _).symm⟩'): unknown identifier 'prod_finset_preimage_of_not_mem_support'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=386, out=30)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨Finset.preimage t g s, Finset.subset_preimage _ _, (prod_preimage _ _ _).symm⟩
```

**lean_error:** tail step 1/1 ('exact ⟨Finset.preimage t g s, Finset.subset_preimage _ _, (prod_preimage _ _ _).symm⟩'): application type mismatch

### `stepk:1` · llama-lean-fenced-micro-r128 · rollout 2 → **lean_error**  (gen 10.7s, verify 0.1s, in=386, out=240)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨Finset.preimage t g _, Finset.subset_preimage _, rfl⟩
```

**lean_error:** tail step 1/1 ('exact ⟨Finset.preimage t g _, Finset.subset_preimage _, rfl⟩'): unknown constant 'Finset.subset_preimage'

### `stepk:1` · llama-lean-fenced-micro-r128 · rollout 3 → **lean_error**  (gen 11.8s, verify 0.2s, in=386, out=270)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨preimage t g, ht.image_subset_iff.1, rfl⟩
```

**lean_error:** tail step 1/1 ('exact ⟨preimage t g, ht.image_subset_iff.1, rfl⟩'): overloaded, errors 

### `stepk:1` · llama-lean-fenced-micro-r128 · rollout 1 → **lean_error**  (gen 12.4s, verify 0.1s, in=386, out=283)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨Finset.subset_preimage_iff.2 ht, rfl⟩
```

**lean_error:** tail step 1/1 ('exact ⟨Finset.subset_preimage_iff.2 ht, rfl⟩'): unknown constant 'Finset.subset_preimage_iff'

### `stepk:1` · llama-lean-fenced-micro-r128 · rollout 0 → **lean_error**  (gen 15.6s, verify 0.1s, in=386, out=375)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨Finset.preimage t g, _, rfl⟩
```

**lean_error:** tail step 1/1 ('exact ⟨Finset.preimage t g, _, rfl⟩'): internal exception #7

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1116, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Finset.image_subset_iff_subset_preimage (hg.injOn _)
exact rfl
```

**lean_error:** tail step 1/2 ('exact Finset.image_subset_iff_subset_preimage (hg.injOn _)'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.3s, verify 0.1s, in=1116, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (image_subset_iff_subset_preimage (hg.injOn _)).2 ht
exact rfl
```

**lean_error:** tail step 1/2 ('exact (image_subset_iff_subset_preimage (hg.injOn _)).2 ht'): application type mismatch

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=1116, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (Finset.image_subset_iff_subset_preimage (hg.injOn _)).mp ht,
exact rfl
```

**lean_error:** tail step 1/2 ('exact (Finset.image_subset_iff_subset_preimage (hg.injOn _)).mp ht,'): <stdin>:1:66: expected end of input

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 2.0s, verify 0.1s, in=1116, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Finset.image_subset_iff_subset_preimage (hg.injOn _)
exact rfl
```

**lean_error:** tail step 1/2 ('exact Finset.image_subset_iff_subset_preimage (hg.injOn _)'): type mismatch

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=1116, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨t.preimage g (hg.injOn _), Finset.image_subset_iff_subset_preimage _⟩
```

**lean_error:** tail step 1/1 ('exact ⟨t.preimage g (hg.injOn _), Finset.image_subset_iff_subset_preimage _⟩'): application type mismatch

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=1116, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨t.preimage g (hg.injOn _), Finset.image_subset_iff_subset_preimage.1 ht, rfl⟩
```

**lean_error:** tail step 1/1 ('exact ⟨t.preimage g (hg.injOn _), Finset.image_subset_iff_subset_preimage.1 ht, rfl⟩'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 2.3s, verify 0.1s, in=1116, out=49)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact
  ⟨t.preimage g (hg.injOn _), s.subset_preimage fun _ _ => rfl,
    (prod_subset (Finset.image_subset_iff_subset_preimage.2 ht) _).symm⟩
```

**lean_error:** tail step 1/3 ('exact'): <stdin>:1:5: unexpected end of input

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 7.0s, verify 0.1s, in=1116, out=170)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨s.preimage g (hg.injOn _), fun t ht => ⟨t.image g ∪ s, Finset.subset_union_right _ _, (prod_subset (subset_union_left _ _) fun y hy hyt => hf y (mt (fun h => Exists.cases_on h fun a ha => ⟨a, ht (Finset.mem_preimage.2 (hy.resolve_left hyt)), rfl⟩) hyt)).symm⟩, fun t ht => ⟨t.preimage g (hg.injOn _), fun u htu => ⟨u.image g, (Finset.image_subset_iff_subset_preimage fun x hx y hy => hg (Finset.mem_image.1 hx).2 (Finset.mem_image.1 hy).2).2 htu, rfl⟩, rfl⟩, rfl⟩
```

**lean_error:** tail step 1/1 ('exact ⟨s.preimage g (hg.injOn _), fun t ht => ⟨t.image g ∪ s, Finset.subset_union_right _ _, (prod_subset (subset_union_left _ _) fun y hy hyt => hf y (mt (fun h => Exists.cases_on h fun a ha => ⟨a, ht (Finset.mem_preimage.2 (hy.resolve_left hyt)), rfl⟩) hyt)).symm⟩, fun t ht => ⟨t.p

### `hint:2` · llama-lean-fenced-micro-r128 · rollout 0 → **success**  (gen 11.2s, verify 0.1s, in=1116, out=255)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨t.preimage g (hg.injOn _), (Finset.image_subset_iff_subset_preimage _).1 ht, rfl⟩
```

### `hint:2` · llama-lean-fenced-micro-r128 · rollout 2 → **lean_error**  (gen 13.6s, verify 0.1s, in=1116, out=308)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨t.preimage g (hg.injOn _), (image_subset_iff_subset_preimage.1 ht).1, rfl⟩
```

**lean_error:** tail step 1/1 ('exact ⟨t.preimage g (hg.injOn _), (image_subset_iff_subset_preimage.1 ht).1, rfl⟩'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · llama-lean-fenced-micro-r128 · rollout 1 → **lean_error**  (gen 14.7s, verify 0.2s, in=1116, out=348)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨t.preimage g (hg.injOn _), Finset.image_subset_iff_subset_preimage.1 ht rfl⟩
```

**lean_error:** tail step 1/1 ('exact ⟨t.preimage g (hg.injOn _), Finset.image_subset_iff_subset_preimage.1 ht rfl⟩'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · llama-lean-fenced-micro-r128 · rollout 3 → **lean_error**  (gen 15.3s, verify 0.1s, in=1116, out=366)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨t.preimage g hg, ht, rfl⟩
```

**lean_error:** tail step 1/1 ('exact ⟨t.preimage g hg, ht, rfl⟩'): application type mismatch
