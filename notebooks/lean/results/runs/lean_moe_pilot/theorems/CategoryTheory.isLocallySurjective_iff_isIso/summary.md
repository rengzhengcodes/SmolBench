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

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 14.6s, verify 0.3s, in=423, out=567)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  simpa using h
· intro h
  simpa using h
```

**lean_error:** tail step 2/5 ('· intro h'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 65.5s, verify 0.1s, in=372, out=5841)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor <;> intro h <;> exact h
```

**lean_error:** tail step 1/1 ('constructor <;> intro h <;> exact h'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 26.8s, verify 0.1s, in=370, out=415)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 21.6s, verify 0.3s, in=1466, out=2001)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
constructor
  · intro h
    haveI := h
    exact
      isIso_of_reflects_iso
        ({ val := Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val)) })
        (sheafToPresheaf (J:=J) (A:=Type w))
  · intro h
    haveI := h
    simpa using
      (inferInstance :
        IsIso
          ((sheafToPresheaf (J:=J) (A:=Type w)).map
            ({ val := Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val)) })))
```

**lean_error:** tail step 2/14 ('· intro h'): unsolved goals

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 99.6s, verify 0.1s, in=1458, out=9501)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
theorem CategoryTheory.isLocallySurjective_iff_isIso {C : Type v} [Category.{v, u} C] {J : GrothendieckTopology C} {A : Type u'} [Category.{v', u'} A] [ConcreteCategory A] {F G : Sheaf J (Type w)} (f : F ⟶ G) :
    IsO (Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val))) ↔
    IsO { val := Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val)) } := by
  have h_main : IsO (Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val))) ↔ IsO { val := Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val)) } := by
    constructor
    · -- Prove the forward direction: if the left side is an isomorphism, then the right side is an isomorphism.
      intro h
      -- Since the two sides are definitionally equal, we can directly use the hypothesis.
      exact h
    · -- Prove the reverse direction: if the right side is an isomorphism, then the left side is an isomorphism.
      intro h
      -- Since the two sides are definitionally equal, we can directly use the hypothesis.
      exact h
  -- Use the established equivalence to conclude the proof.
  exact h_main
```

**lean_error:** tail step 1/15 ("theorem CategoryTheory.isLocallySurjective_iff_isIso {C : Type v} [Category.{v, u} C] {J : GrothendieckTopology C} {A : Type u'} [Category.{v', u'} A] [ConcreteCategory A] {F G : Sheaf J (Type w)} (f : F ⟶ G) :"): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 27.4s, verify 0.1s, in=1416, out=461)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 20.2s, verify 0.8s, in=2080, out=1708)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
constructor
· intro h
  haveI := h
  exact
    (isIso_of_reflects_iso
      ({ val := Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val)) } : _)
      (sheafToPresheaf (J:=J) (A:=Type w)))
· intro h
  haveI := h
  simpa using
    (inferInstance :
      IsIso ((sheafToPresheaf (J:=J) (A:=Type w)).map
        ({ val := Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val)) } : _)))
```

**lean_error:** tail step 2/13 ('· intro h'): unsolved goals

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 83.6s, verify 0.3s, in=2084, out=7738)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
constructor
· intro h
  exact Functor.map_isIso sheafToPresheaf h
· intro h
  have h₁ : IsOso (sheafToPresheaf.map (imageSheafι f)) := by
    simpa [sheafToPresheaf.map] using h
  have h₂ : ReflectsIsomorphisms sheafToPresheaf :=
    sheafToPresheaf_full.reflectsIsomorphisms sheafToPresheaf_faithful
  exact CategoryTheory.isIso_of_reflects_iso (imageSheafι f) sheafToPresheaf h₁ h₂
```

**lean_error:** tail step 2/9 ('· intro h'): unsolved goals

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 90.4s, verify 0.1s, in=2020, out=2519)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 21.1s, verify 0.3s, in=2019, out=1862)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
constructor
· intro h
  haveI := h
  exact
    (isIso_of_reflects_iso
        (f := ({ val := Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val)) } : _))
        (sheafToPresheaf (J:=J) (A:=Type w)))
· intro h
  haveI := h
  infer_instance
```

**lean_error:** tail step 2/10 ('· intro h'): unsolved goals

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 301.0s, verify 0.1s, in=2176, out=32768)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h_faithful : Faithful (sheafToPresheaf : Sheaf J (Type w) ⥤ Presheaf J (Type w)) := by
  refine' fun F G f g h => _
  -- We need to show that f = g.
  -- Since the category of sheaves is a full subcategory of presheaves, the hom-set is the same.
  -- Thus, f and g are equal if their underlying presheaf morphisms are equal.
  -- We have h : sheafToPresheaf.map f = shefToPresheaf.map g, which is f.val = g.val.
  -- But in the category of sheaves, f and g are determined by their underlying presheaf morphisms.
  -- Therefore, f = g.
  -- We can use the fact that the coercion from sheaf to presheaf is injective on morphisms.
  -- Alternatively, we can use the extensionality principle for the category of sheaves.
  have h₁ : f.val = g.val := by simpa [sheafToPresheaf] using h
  -- Now, we need to show that f = g.
  -- Since the category of sheaves is a full subcategory of presheaves, the hom-set is the same.
  -- Thus, we can use the fact that the forgetful functor is injective on hom-sets.
  -- But perhaps we can use the following: the forgetful functor is the identity on hom-sets when the objects are fixed.
  -- Therefore, if f.val = g.val, then f = g.
  -- We can use the `ext` tactic to show that the morphisms are equal by showing that they are equal on all objects.
  -- However, since we are in a category, we can use the `ext` tactic to show that the morphisms are equal by showing that they are equal on all objects.
  -- But perhaps it's easier to use the fact that the forgetful functor is faithful by construction.
  -- Let's try to use the `congr_arg` tactic to show that if the underlying presheaf morphisms are equal, then the sheaf morphisms are equal.
  -- We can use the fact that the sheaf morphism structure is just the presheaf morphism structure.
  apply Eq.symm
  apply Eq.symm
  -- Now, we need to show that g = f.
  -- We can use the fact that their underlying presheaf morphisms are equal.
  -- But we need to be careful about the types.
  -- Instead, we can use the `ext` tactic to show that the morphisms are equal by showing that they are equal on all objects.
  -- However, since we are in a category, we can use the `ext` tactic to show that the morphisms are equal by showing that they are equal on all objects.
  -- But perhaps it's easier to use the fact that the forgetful functor is faithful by construction.
  <;> simp_all [sheafToPresheaf]
  <;> aesop
```

**lean_error:** tail step 1/31 ('have h_faithful : Faithful (sheafToPresheaf : Sheaf J (Type w) ⥤ Presheaf J (Type w)) := by'): <stdin>:1:91: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 45.9s, verify 0.7s, in=2031, out=1007)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
constructor
· intro h
  exact isIso_of_reflects_iso _ sheafToPresheaf h
· intro h
  exact Functor.map_isIso sheafToPresheaf _
```

**lean_error:** tail step 2/5 ('· intro h'): unsolved goals
