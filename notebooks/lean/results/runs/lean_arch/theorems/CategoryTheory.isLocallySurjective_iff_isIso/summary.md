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

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.4s, in=383, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
rfl
```

**lean_error:** tail step 2/2 ('rfl'): type mismatch

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 1.3s, in=356, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← IsIso.isIso_iff_isIso_comp]
simp only [Sheaf.Hom.morphism_app]
rfl
```

**lean_error:** tail step 1/3 ('rw [← IsIso.isIso_iff_isIso_comp]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.3s, in=372, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Iff.intro
exact (IsIso.of_iso)
exact (IsIso.iso)
```

**lean_error:** tail step 2/3 ('exact (IsIso.of_iso)'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 5.9s, verify 0.2s, in=1375, out=106)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ (sheafToPresheaf J Type w)
exact isIso_of_reflects_iso _ (sheafToPresheaf J Type w)
constructor
intro h
apply CategoryTheory.Functor.map_isIso
exact h
intro h
apply isIso_of_reflects_iso
exact h
constructor
intro h
apply CategoryTheory.Functor.map_isIso
exact h
intro h
apply isIso_of_reflects_iso
exact h
```

**lean_error:** tail step 1/16 ('exact isIso_of_reflects_iso _ (sheafToPresheaf J Type w)'): type mismatch

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.2s, in=1346, out=39)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [IsIso_comp]
simp only [SheafToPresheaf.map_isIso, IsIso_comp, ← Category.assoc, IsIso.inv_hom_id_assoc]
rfl
```

**lean_error:** tail step 1/3 ('rw [IsIso_comp]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.5s, in=1364, out=42)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Iff.intro
exact isIso_of_reflects_iso _ sheafToPresheaf
exact isIso_of_reflects_iso _ sheafToPresheaf
```

**lean_error:** tail step 2/3 ('exact isIso_of_reflects_iso _ sheafToPresheaf'): type mismatch

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.9s, verify 0.7s, in=1955, out=68)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ (sheafToPresheaf J (Type w))
exact imageSheafι f
exact Functor.map_isIso (sheafToPresheaf J (Type w)) _
exact isIso_of_reflects_iso _ (sheafToPresheaf J (Type w))
```

**lean_error:** tail step 1/4 ('exact isIso_of_reflects_iso _ (sheafToPresheaf J (Type w))'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.2s, in=1915, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsIso_iff_isIso]
rfl
```

**lean_error:** tail step 1/2 ('rw [IsIso_iff_isIso]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.5s, in=1944, out=38)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Iff.intro
exact isIso_of_reflects_iso _ sheafToPresheaf
exact Functor.map_isIso sheafToPresheaf
```

**lean_error:** tail step 2/3 ('exact isIso_of_reflects_iso _ sheafToPresheaf'): type mismatch

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.2s, verify 0.1s, in=1981, out=47)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact isIso_of_reflects_iso _ (sheafToPresheaf J (Type w))
exact imageSheafι f
exact Functor.map_isIso (sheafToPresheaf J (Type w)) _
```

**lean_error:** tail step 1/3 ('exact isIso_of_reflects_iso _ (sheafToPresheaf J (Type w))'): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.9s, in=2018, out=60)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [IsIso_comp, ← Category.assoc, IsIso_comp]
simp only [SheafToPresheaf.map_comp, SheafToPresheaf.map_isIso, IsIso.inv_hom_id, comp_id,
  SheafToPresheaf.map_id]
rfl
```

**lean_error:** tail step 1/4 ('rw [IsIso_comp, ← Category.assoc, IsIso_comp]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 1.6s, in=1970, out=42)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Iff.intro
exact isIso_of_reflects_iso _ sheafToPresheaf
exact isIso_of_reflects_iso _ sheafToPresheaf
```

**lean_error:** tail step 2/3 ('exact isIso_of_reflects_iso _ sheafToPresheaf'): type mismatch
