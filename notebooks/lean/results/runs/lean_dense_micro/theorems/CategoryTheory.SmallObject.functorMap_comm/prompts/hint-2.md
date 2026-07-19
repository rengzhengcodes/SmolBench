## Current goal
```
⊢ Sigma.ι (functorObjSrcFamily f πX) { i := i, t := t, b := b, w := w } ≫
      functorObjLeft f πX ≫ functorMapTgt f πX πY φ hφ =
    Sigma.ι (functorObjSrcFamily f πX) { i := i, t := t, b := b, w := w } ≫
      functorMapSrc f πX πY φ hφ ≫ functorObjLeft f πY
```

## Full tactic state
```
case h.mk
C : Type u
inst✝⁴ : Category.{v, u} C
I : Type w
A B : I → C
f : (i : I) → A i ⟶ B i
S X Y Z : C
πX : X ⟶ S
πY : Y ⟶ S
φ : X ⟶ Y
hφ : φ ≫ πY = πX
inst✝³ : HasColimitsOfShape (Discrete (FunctorObjIndex f πX)) C
inst✝² : HasColimitsOfShape (Discrete (FunctorObjIndex f πY)) C
inst✝¹ : HasPushout (functorObjTop f πX) (functorObjLeft f πX)
inst✝ : HasPushout (functorObjTop f πY) (functorObjLeft f πY)
i : I
t : A i ⟶ X
b : B i ⟶ S
w : t ≫ πX = f i ≫ b
⊢ Sigma.ι (functorObjSrcFamily f πX) { i := i, t := t, b := b, w := w } ≫
      functorObjLeft f πX ≫ functorMapTgt f πX πY φ hφ =
    Sigma.ι (functorObjSrcFamily f πX) { i := i, t := t, b := b, w := w } ≫
      functorMapSrc f πX πY φ hφ ≫ functorObjLeft f πY
```

## Proof so far (1 tactic)
```lean
ext ⟨i, t, b, w⟩
```

## Theorem
`CategoryTheory.SmallObject.functorMap_comm` in `Mathlib/CategoryTheory/SmallObject/Construction.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.ι_colimMap_assoc`
- `CategoryTheory.Discrete.natTrans_app`
- `CategoryTheory.Limits.ι_colimMap`
- `CategoryTheory.SmallObject.ι_functorMapTgt`
- `rfl`
- `CategoryTheory.SmallObject.ι_functorMapSrc_assoc`
- `rfl`

## Premise signatures
### `CategoryTheory.Limits.ι_colimMap_assoc`
_(not found in premise corpus)_

### `CategoryTheory.Discrete.natTrans_app`
_(not found in premise corpus)_

### `CategoryTheory.Limits.ι_colimMap` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem ι_colimMap {F G : J ⥤ C} [HasColimit F] [HasColimit G] (α : F ⟶ G) (j : J) :
    colimit.ι F j ≫ colimMap α = α.app j ≫ colimit.ι G j
```

### `CategoryTheory.SmallObject.ι_functorMapTgt` (lemma)
```lean
@[reassoc]
lemma ι_functorMapTgt (i : I) (t : A i ⟶ X) (b : B i ⟶ S) (w : t ≫ πX = f i ≫ b)
    (t' : A i ⟶ Y) (fac : t ≫ φ = t') :
    Sigma.ι _ (FunctorObjIndex.mk i t b w) ≫ functorMapTgt f πX πY φ hφ =
      Sigma.ι (functorObjTgtFamily f πY)
        (FunctorObjIndex.mk i t' b (by rw [← w, ← fac, assoc, hφ]))
```

### `rfl` (commanddeclaration)
```lean
@[match_pattern] def rfl {α : Sort u} {a : α} : Eq a a
```

### `CategoryTheory.SmallObject.ι_functorMapSrc_assoc`
_(not found in premise corpus)_

### `rfl` (commanddeclaration)
```lean
@[match_pattern] def rfl {α : Sort u} {a : α} : Eq a a
```

## Premise full source (with proof)
### `CategoryTheory.Limits.ι_colimMap_assoc`
_(not found in premise corpus)_

### `CategoryTheory.Discrete.natTrans_app`
_(not found in premise corpus)_

### `CategoryTheory.Limits.ι_colimMap` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/HasLimits.lean`
```lean
@[reassoc (attr := simp)]
theorem ι_colimMap {F G : J ⥤ C} [HasColimit F] [HasColimit G] (α : F ⟶ G) (j : J) :
    colimit.ι F j ≫ colimMap α = α.app j ≫ colimit.ι G j :=
  colimit.ι_desc _ j
```

### `CategoryTheory.SmallObject.ι_functorMapTgt` (lemma) at `Mathlib/CategoryTheory/SmallObject/Construction.lean`
```lean
@[reassoc]
lemma ι_functorMapTgt (i : I) (t : A i ⟶ X) (b : B i ⟶ S) (w : t ≫ πX = f i ≫ b)
    (t' : A i ⟶ Y) (fac : t ≫ φ = t') :
    Sigma.ι _ (FunctorObjIndex.mk i t b w) ≫ functorMapTgt f πX πY φ hφ =
      Sigma.ι (functorObjTgtFamily f πY)
        (FunctorObjIndex.mk i t' b (by rw [← w, ← fac, assoc, hφ])) := by
  subst fac
  simp [functorMapTgt]
```

### `rfl` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`rfl : a = a` is the unique constructor of the equality type. This is the
same as `Eq.refl` except that it takes `a` implicitly instead of explicitly.

This is a more powerful theorem than it may appear at first, because although
the statement of the theorem is `a = a`, Lean will allow anything that is
definitionally equal to that type. So, for instance, `2 + 2 = 4` is proven in
Lean by `rfl`, because both sides are the same up to definitional equality.
-/
@[match_pattern] def rfl {α : Sort u} {a : α} : Eq a a := Eq.refl a

/-- `id x = x`, as a `@[simp]` lemma. -/
```

### `CategoryTheory.SmallObject.ι_functorMapSrc_assoc`
_(not found in premise corpus)_

### `rfl` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`rfl : a = a` is the unique constructor of the equality type. This is the
same as `Eq.refl` except that it takes `a` implicitly instead of explicitly.

This is a more powerful theorem than it may appear at first, because although
the statement of the theorem is `a = a`, Lean will allow anything that is
definitionally equal to that type. So, for instance, `2 + 2 = 4` is proven in
Lean by `rfl`, because both sides are the same up to definitional equality.
-/
@[match_pattern] def rfl {α : Sort u} {a : α} : Eq a a := Eq.refl a

/-- `id x = x`, as a `@[simp]` lemma. -/
```
