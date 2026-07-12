# CategoryTheory.isLocallySurjective_iff_isIso   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Sites/Surjective.lean`  

**Ground-truth tail (from k):**
```lean
exact
  ⟨fun h => @isIso_of_reflects_iso _ _ _ _ _ _ (imageSheafι f) (sheafToPresheaf J _) h _, fun h =>
    @Functor.map_isIso _ _ _ _ _ _ (sheafToPresheaf J _) _ h⟩
```

**True premises at k:** `CategoryTheory.isIso_of_reflects_iso`, `CategoryTheory.GrothendieckTopology.imageSheafι`, `CategoryTheory.sheafToPresheaf`, `CategoryTheory.Functor.map_isIso`, `CategoryTheory.sheafToPresheaf`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-goedel | qwen3-lean-leannav | qwen3-lean-real |
| --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 50.7s, verify 0.1s, in=356, out=2282)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply is_iso_iff_of_fully_faithful Sheaf.forget_to_Presheaf
```

**lean_error:** tail step 1/1 ('apply is_iso_iff_of_fully_faithful Sheaf.forget_to_Presheaf'): unknown identifier 'is_iso_iff_of_fully_faithful'

### `stepk:1` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 5.7s, verify 0.1s, in=356, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 11.5s, verify 0.3s, in=356, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 9.8s, verify 0.1s, in=356, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 122.7s, verify 0.3s, in=1344, out=6331)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Iff.intro
· intro h
  apply Functor.map_isIso sheafToPresheaf
  exact h
· intro h
  apply isIso_of_reflects_iso _ sheafToPresheaf
  exact h
  infer_instance
```

**lean_error:** tail step 2/8 ('· intro h'): unsolved goals

### `hint:2` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 6.1s, verify 1.1s, in=1344, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← sheafToPresheaf.map_isIso, imageSheafι_val]
```

**lean_error:** tail step 1/1 ('rw [← sheafToPresheaf.map_isIso, imageSheafι_val]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 12.1s, verify 1.8s, in=1344, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← sheafToPresheaf.map_isIso, imageSheafι_val]
```

**lean_error:** tail step 1/1 ('rw [← sheafToPresheaf.map_isIso, imageSheafι_val]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 12.6s, verify 0.4s, in=1344, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← sheafToPresheaf.map_isIso, isLocallySurjective_iff_isIso]
```

**lean_error:** tail step 1/1 ('rw [← sheafToPresheaf.map_isIso, isLocallySurjective_iff_isIso]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 72.4s, verify 0.2s, in=1929, out=3478)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
split
  · apply Functor.map_isIso
  · apply isIso_of_reflects_iso _ sheafToPresheaf
```

**lean_error:** tail step 1/3 ('split'): tactic 'split' failed

### `hint:3` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 5.8s, verify 0.1s, in=1929, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:3` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 11.8s, verify 0.3s, in=1929, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← sheafToPresheaf_map_isIso, imageSheafι_val]
```

**lean_error:** tail step 1/1 ('rw [← sheafToPresheaf_map_isIso, imageSheafι_val]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 9.9s, verify 0.1s, in=1929, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 90.6s, verify 0.2s, in=1953, out=4380)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
split
  apply map_isIso
  apply isIso_of_reflects_iso (imageSheafι f) (sheafToPresheaf J (Type w))
```

**lean_error:** tail step 1/3 ('split'): tactic 'split' failed

### `noise:3` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 5.8s, verify 0.1s, in=1953, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `noise:3` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 13.9s, verify 0.7s, in=1953, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← sheafToPresheaf.map_isIso, imageSheafι_val]
```

**lean_error:** tail step 1/1 ('rw [← sheafToPresheaf.map_isIso, imageSheafι_val]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 9.8s, verify 0.1s, in=1953, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress
