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

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 36.1s, verify 0.1s, in=356, out=1124)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply is_iso_iff_is_iso_val
```

**lean_error:** tail step 1/1 ('apply is_iso_iff_is_iso_val'): unknown identifier 'is_iso_iff_is_iso_val'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 90.6s, verify 0.1s, in=356, out=3180)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Sheaf.is_iso_iff_is_iso_val
```

**lean_error:** tail step 1/1 ('apply Sheaf.is_iso_iff_is_iso_val'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 139.1s, verify 0.1s, in=356, out=5091)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply isIso_iff_val_isIso
```

**lean_error:** tail step 1/1 ('apply isIso_iff_val_isIso'): unknown identifier 'isIso_iff_val_isIso'

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 161.7s, verify 0.1s, in=356, out=6084)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply is_iso_map_iff Sheaf_to_Presheaf
```

**lean_error:** tail step 1/1 ('apply is_iso_map_iff Sheaf_to_Presheaf'): unknown identifier 'is_iso_map_iff'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 4.9s, verify 0.2s, in=356, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 5.5s, verify 0.1s, in=356, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact isIso_iff_isIso_val _
```

**lean_error:** tail step 1/1 ('exact isIso_iff_isIso_val _'): unknown identifier 'isIso_iff_isIso_val'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 5.7s, verify 0.1s, in=356, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 5.8s, verify 0.2s, in=356, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 5.0s, verify 0.2s, in=356, out=176)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 5.6s, verify 0.2s, in=356, out=198)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 6.2s, verify 0.1s, in=356, out=220)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 6.6s, verify 0.2s, in=356, out=238)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [CategoryTheory.isIso_iff_isIso_ι, Iff.rfl]
```

**lean_error:** tail step 1/1 ('rw [CategoryTheory.isIso_iff_isIso_ι, Iff.rfl]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 7.1s, verify 0.1s, in=356, out=176)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 7.2s, verify 0.2s, in=356, out=254)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sheafify_isIso_iff]
```

**lean_error:** tail step 1/1 ('rw [sheafify_isIso_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 9.3s, verify 0.1s, in=356, out=247)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply isIso_iff_isIso_ι
```

**lean_error:** tail step 1/1 ('apply isIso_iff_isIso_ι'): unknown identifier 'isIso_iff_isIso_ι'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 75.5s, verify 0.2s, in=356, out=237)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [isIso_iff_isIso]
```

**lean_error:** tail step 1/1 ('rw [isIso_iff_isIso]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 164.0s, verify 0.2s, in=1344, out=6186)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
split
· apply Functor.map_isIso sheafToPresheaf
· apply isIso_of_reflects_iso _ sheafToPresheaf
```

**lean_error:** tail step 1/3 ('split'): tactic 'split' failed

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 167.3s, verify 0.2s, in=1344, out=6326)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
split
intro h
apply Functor.map_isIso sheafToPresheaf h
intro h
apply isIso_of_reflects_iso _ sheafToPresheaf h
```

**lean_error:** tail step 1/5 ('split'): tactic 'split' failed

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 182.1s, verify 0.2s, in=1344, out=7068)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
split
intro h
apply Functor.map_isIso sheafToPresheaf h
intro h
apply isIso_of_reflects_iso _ sheafToPresheaf h
```

**lean_error:** tail step 1/5 ('split'): tactic 'split' failed

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 226.7s, verify 0.2s, in=1344, out=7153)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
split
intro h
apply map_isIso sheafToPresheaf h
intro h
apply isIso_of_reflects_iso (imageSheafι f) sheafToPresheaf h
```

**lean_error:** tail step 1/5 ('split'): tactic 'split' failed

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 5.2s, verify 0.1s, in=1344, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 6.0s, verify 0.1s, in=1344, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact sheafToPresheaf.reflects_isomorphisms _
```

**lean_error:** tail step 1/1 ('exact sheafToPresheaf.reflects_isomorphisms _'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 7.1s, verify 0.2s, in=1344, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← sheafToPresheaf.map_isIso_iff, imageSheafι, sheafToPresheaf_map]
```

**lean_error:** tail step 1/1 ('rw [← sheafToPresheaf.map_isIso_iff, imageSheafι, sheafToPresheaf_map]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 7.3s, verify 0.1s, in=1344, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [isLocallySurjective_iff_isIso_imageSheafι, imageSheafι_val]
```

**lean_error:** tail step 1/1 ('simp only [isLocallySurjective_iff_isIso_imageSheafι, imageSheafι_val]'): unknown identifier 'isLocallySurjective_iff_isIso_imageSheafι'

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 7.9s, verify 0.3s, in=1344, out=269)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply isIso_of_reflects_iso
```

**lean_error:** tail step 1/1 ('apply isIso_of_reflects_iso'): tactic 'apply' failed, failed to unify

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 9.8s, verify 0.3s, in=1344, out=337)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply isIso_of_reflects_iso _ sheafToPresheaf <;> apply Functor.map_isIso
```

**lean_error:** tail step 1/1 ('apply isIso_of_reflects_iso _ sheafToPresheaf <;> apply Functor.map_isIso'): application type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 13.9s, verify 0.3s, in=1344, out=486)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨fun h => isIso_of_reflects_iso _ sheafToPresheaf, Functor.map_isIso⟩
```

**lean_error:** tail step 1/1 ('exact ⟨fun h => isIso_of_reflects_iso _ sheafToPresheaf, Functor.map_isIso⟩'): application type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 14.2s, verify 0.6s, in=1344, out=269)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ sheafToPresheaf
```

**lean_error:** tail step 1/1 ('exact isIso_of_reflects_iso _ sheafToPresheaf'): type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 17.4s, verify 0.1s, in=1344, out=386)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa only [sheafToPresheaf_map, imageSheafι] using isIso_of_reflects_iso (imageSheafι f)
  sheafToPresheaf (Functor.map_isIso _ _)
```

**lean_error:** tail step 1/2 ('simpa only [sheafToPresheaf_map, imageSheafι] using isIso_of_reflects_iso (imageSheafι f)'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 18.6s, verify 0.1s, in=1344, out=368)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨Functor.map_isIso _, isIso_of_reflects_iso _ _⟩
```

**lean_error:** tail step 1/1 ('exact ⟨Functor.map_isIso _, isIso_of_reflects_iso _ _⟩'): application type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 29.5s, verify 0.1s, in=1344, out=664)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa only [imageSheafι, isIso_of_reflects_iso, sheafToPresheaf,
  Functor.map_isIso, sheafToPresheaf]
```

**lean_error:** tail step 1/2 ('simpa only [imageSheafι, isIso_of_reflects_iso, sheafToPresheaf,'): <stdin>:1:64: unexpected end of input; expected '*' or '-'

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 80.5s, verify 0.1s, in=1344, out=457)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa only [← Functor.map_isIso, isIso_of_reflects_iso] using sheafToPresheaf.reflectsIsomorphisms
```

**lean_error:** tail step 1/1 ('simpa only [← Functor.map_isIso, isIso_of_reflects_iso] using sheafToPresheaf.reflectsIsomorphisms'): invalid '←' modifier in rewrite rule to 'True'

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 181.8s, verify 0.2s, in=1929, out=5924)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
split
apply Functor.map_isIso
apply isIso_of_reflects_iso _ sheafToPresheaf
```

**lean_error:** tail step 1/3 ('split'): tactic 'split' failed

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 203.3s, verify 0.2s, in=1929, out=4107)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
split
<;> [apply Functor.map_isIso, apply isIso_of_reflects_iso _ sheafToPresheaf]
```

**lean_error:** tail step 1/2 ('split'): tactic 'split' failed

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 206.3s, verify 0.2s, in=1929, out=5260)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
split
· apply Functor.map_isIso sheafToPresheaf
· apply isIso_of_reflects_iso _ sheafToPresheaf
```

**lean_error:** tail step 1/3 ('split'): tactic 'split' failed

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 255.4s, verify 0.2s, in=1929, out=8957)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
split
· intro h; apply Functor.map_isIso
· intro h; apply isIso_of_reflects_iso sheafToPresheaf h; infer_instance
```

**lean_error:** tail step 1/3 ('split'): tactic 'split' failed

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 6.6s, verify 0.3s, in=1929, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← Functor.map_isIso sheafToPresheaf]
```

**lean_error:** tail step 1/1 ('rw [← Functor.map_isIso sheafToPresheaf]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 6.9s, verify 0.2s, in=1929, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← sheafToPresheaf.map_isIso, imageSheafι]
```

**lean_error:** tail step 1/1 ('rw [← sheafToPresheaf.map_isIso, imageSheafι]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 7.4s, verify 0.4s, in=1929, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [← Functor.map_isIso sheafToPresheaf, imageSheafι]
```

**lean_error:** tail step 1/1 ('simp only [← Functor.map_isIso sheafToPresheaf, imageSheafι]'): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 82.9s, verify 0.2s, in=1929, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← sheafToPresheaf.map_isIso, imageSheafι, isIso_iff_isIso_toPresheaf]
```

**lean_error:** tail step 1/1 ('rw [← sheafToPresheaf.map_isIso, imageSheafι, isIso_iff_isIso_toPresheaf]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 29.7s, verify 0.3s, in=1929, out=285)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ sheafToPresheaf
```

**lean_error:** tail step 1/1 ('exact isIso_of_reflects_iso _ sheafToPresheaf'): type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 33.1s, verify 0.1s, in=1929, out=360)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [sheafToPresheaf.map_isIso, isIso_of_reflects_iso]
```

**lean_error:** tail step 1/1 ('simp only [sheafToPresheaf.map_isIso, isIso_of_reflects_iso]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 35.6s, verify 0.3s, in=1929, out=442)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [isIso_of_reflects_iso _ sheafToPresheaf, sheafToPresheaf]
```

**lean_error:** tail step 1/1 ('simp [isIso_of_reflects_iso _ sheafToPresheaf, sheafToPresheaf]'): application type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 40.1s, verify 0.1s, in=1929, out=627)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ sheafToPresheaf <;>
  simpa [sheafToPresheaf] using Functor.map_isIso sheafToPresheaf _
```

**lean_error:** tail step 1/2 ('exact isIso_of_reflects_iso _ sheafToPresheaf <;>'): <stdin>:1:49: unexpected end of input; expected '['

### `hint:3` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 42.3s, verify 0.1s, in=1929, out=462)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [CategoryTheory.isIso_of_reflects_iso, CategoryTheory.GrothendieckTopology.imageSheafι,
  CategoryTheory.sheafToPresheaf, CategoryTheory.Functor.map_isIso, CategoryTheory.sheafToPresheaf]
```

**lean_error:** tail step 1/2 ('simp [CategoryTheory.isIso_of_reflects_iso, CategoryTheory.GrothendieckTopology.imageSheafι,'): <stdin>:1:92: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 42.4s, verify 0.3s, in=1929, out=379)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [isIso_of_reflects_iso _ sheafToPresheaf, Functor.map_isIso, sheafToPresheaf]
```

**lean_error:** tail step 1/1 ('simp only [isIso_of_reflects_iso _ sheafToPresheaf, Functor.map_isIso, sheafToPresheaf]'): application type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 47.3s, verify 0.3s, in=1929, out=512)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact ⟨fun _ => isIso_of_reflects_iso _ sheafToPresheaf, map_isIso _⟩
```

**lean_error:** tail step 1/1 ('exact ⟨fun _ => isIso_of_reflects_iso _ sheafToPresheaf, map_isIso _⟩'): application type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 108.6s, verify 0.3s, in=1929, out=442)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← isIso_of_reflects_iso _ sheafToPresheaf, Functor.map_isIso]
```

**lean_error:** tail step 1/1 ('rw [← isIso_of_reflects_iso _ sheafToPresheaf, Functor.map_isIso]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 88.2s, verify 0.2s, in=1953, out=3090)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
split
· intro h
  exact Functor.map_isIso sheafToPresheaf h
· intro h
  apply isIso_of_reflects_iso (Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val))) sheafToPresheaf h
  infer_instance
```

**lean_error:** tail step 1/6 ('split'): tactic 'split' failed

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 112.8s, verify 0.2s, in=1953, out=4013)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
split
intro h
exact Functor.map_isIso sheafToPresheaf h
intro h
apply isIso_of_reflects_iso _ sheafToPresheaf h
```

**lean_error:** tail step 1/5 ('split'): tactic 'split' failed

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 147.0s, verify 0.2s, in=1953, out=5412)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
split
· intro h
  apply isIso_of_reflects_iso sheafToPresheaf
  exact h
· intro h
  apply map_isIso sheafToPresheaf
  exact h
```

**lean_error:** tail step 1/7 ('split'): tactic 'split' failed

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 161.8s, verify 0.2s, in=1953, out=6087)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
split
· intro h
  exact Functor.map_isIso sheafToPresheaf h
· intro h
  exact isIso_of_reflects_iso (imageSheafι f) sheafToPresheaf h
```

**lean_error:** tail step 1/5 ('split'): tactic 'split' failed

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 5.2s, verify 0.1s, in=1953, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 5.6s, verify 0.1s, in=1953, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact sheafToPresheaf.reflects_isIso
```

**lean_error:** tail step 1/1 ('exact sheafToPresheaf.reflects_isIso'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 6.1s, verify 0.2s, in=1953, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [sheafToPresheaf.map_isIso_iff, imageSheafι_val]
```

**lean_error:** tail step 1/1 ('rw [sheafToPresheaf.map_isIso_iff, imageSheafι_val]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 6.3s, verify 0.3s, in=1953, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [← Functor.map_isIso sheafToPresheaf, imageSheafι]
```

**lean_error:** tail step 1/1 ('simp only [← Functor.map_isIso sheafToPresheaf, imageSheafι]'): application type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 16.8s, verify 0.1s, in=1953, out=290)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using sheafToPresheaf.map_isIso _, isIso_of_reflects_iso _ sheafToPresheaf
```

**lean_error:** tail step 1/1 ('simpa using sheafToPresheaf.map_isIso _, isIso_of_reflects_iso _ sheafToPresheaf'): <stdin>:1:39: expected end of input

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 17.1s, verify 0.3s, in=1953, out=313)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ sheafToPresheaf
```

**lean_error:** tail step 1/1 ('exact isIso_of_reflects_iso _ sheafToPresheaf'): type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 19.5s, verify 0.3s, in=1953, out=396)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact ⟨fun h => isIso_of_reflects_iso _ sheafToPresheaf h, Functor.map_isIso _⟩
```

**lean_error:** tail step 1/1 ('exact ⟨fun h => isIso_of_reflects_iso _ sheafToPresheaf h, Functor.map_isIso _⟩'): application type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 21.1s, verify 0.1s, in=1953, out=351)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← imageSheafι, sheafToPresheaf.map_isIso, isIso_of_reflects_iso _ sheafToPresheaf,
  imageSheafι_val]
```

**lean_error:** tail step 1/2 ('rw [← imageSheafι, sheafToPresheaf.map_isIso, isIso_of_reflects_iso _ sheafToPresheaf,'): <stdin>:1:86: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 25.3s, verify 0.3s, in=1953, out=331)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply isIso_of_reflects_iso _ sheafToPresheaf
```

**lean_error:** tail step 1/1 ('apply isIso_of_reflects_iso _ sheafToPresheaf'): application type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 29.1s, verify 0.3s, in=1953, out=567)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply isIso_of_reflects_iso _ sheafToPresheaf <;> apply Functor.map_isIso
```

**lean_error:** tail step 1/1 ('apply isIso_of_reflects_iso _ sheafToPresheaf <;> apply Functor.map_isIso'): application type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 32.4s, verify 0.1s, in=1953, out=499)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact isIso_of_reflects_iso (Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val)))
  sheafToPresheaf sheafToPresheaf.reflects_isIsomorphisms
```

**lean_error:** tail step 1/2 ('exact isIso_of_reflects_iso (Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val)))'): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 32.9s, verify 0.2s, in=1953, out=429)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← sheafToPresheaf.map_isIso, isIso_of_reflects_iso _ sheafToPresheaf]
```

**lean_error:** tail step 1/1 ('rw [← sheafToPresheaf.map_isIso, isIso_of_reflects_iso _ sheafToPresheaf]'): tactic 'rewrite' failed, equality or iff proof expected
