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

## Transitive premise context (1-hop, 6/6 premises, ≈1092 tokens)
### `Lean.Parser.Category.attr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Notation.lean`
```lean
/-- `attr` is a builtin syntax category for attributes.
Declarations can be annotated with attributes using the `@[...]` notation. -/
def attr : Category := {}

/-- `stx` is a builtin syntax category for syntax. This is the abbreviated
parser notation used inside `syntax` and `macro` declarations. -/
```

### `CategoryTheory.Limits.HasColimit` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/HasLimits.lean`
```lean
/-- `HasColimit F` represents the mere existence of a colimit for `F`. -/
class HasColimit (F : J ⥤ C) : Prop where mk' ::
  /-- There exists a colimit for `F` -/
  exists_colimit : Nonempty (ColimitCocone F)
```

### `CategoryTheory.Limits.colimMap` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/HasLimits.lean`
```lean
/-- Functoriality of colimits.

Usually this morphism should be accessed through `colim.map`,
but may be needed separately when you have specified colimits for the source and target functors,
but not necessarily for all functors of shape `J`.
-/
def colimMap {F G : J ⥤ C} [HasColimit F] [HasColimit G] (α : F ⟶ G) : colimit F ⟶ colimit G :=
  IsColimit.map (colimit.isColimit F) _ α
```

### `CategoryTheory.SmallObject.functorMapTgt` (commanddeclaration) at `Mathlib/CategoryTheory/SmallObject/Construction.lean`
```lean
/-- The canonical morphism `∐ functorObjTgtFamily f πX ⟶ ∐ functorObjTgtFamily f πY`
induced by a morphism in `φ : X ⟶ Y` such that `φ ≫ πX = πY`. -/
noncomputable def functorMapTgt :
    ∐ functorObjTgtFamily f πX ⟶ ∐ functorObjTgtFamily f πY :=
  Sigma.map' (fun x => FunctorObjIndex.mk x.i (x.t ≫ φ) x.b (by simp [hφ])) (fun _ => 𝟙 _)
```

### `CategoryTheory.SmallObject.functorObjTgtFamily` (commanddeclaration) at `Mathlib/CategoryTheory/SmallObject/Construction.lean`
```lean
/-- The family of objects `B x.i` parametrized by `x : FunctorObjIndex f πX`. -/
abbrev functorObjTgtFamily (x : FunctorObjIndex f πX) : C := B x.i

/-- The family of the morphisms `f x.i : A x.i ⟶ B x.i`
parametrized by `x : FunctorObjIndex f πX`. -/
```

### `Eq` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
The equality relation. It has one introduction rule, `Eq.refl`.
We use `a = b` as notation for `Eq a b`.
A fundamental property of equality is that it is an equivalence relation.
```
variable (α : Type) (a b c d : α)
variable (hab : a = b) (hcb : c = b) (hcd : c = d)

example : a = d :=
  Eq.trans (Eq.trans hab (Eq.symm hcb)) hcd
```
Equality is much more than an equivalence relation, however. It has the important property that every assertion
respects the equivalence, in the sense that we can substitute equal expressions without changing the truth value.
That is, given `h1 : a = b` and `h2 : p a`, we can construct a proof for `p b` using substitution: `Eq.subst h1 h2`.
Example:
```
example (α : Type) (a b : α) (p : α → Prop)
        (h1 : a = b) (h2 : p a) : p b :=
  Eq.subst h1 h2

example (α : Type) (a b : α) (p : α → Prop)
    (h1 : a = b) (h2 : p a) : p b :=
  h1 ▸ h2
```
The triangle in the second presentation is a macro built on top of `Eq.subst` and `Eq.symm`, and you can enter it by typing `\t`.
For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
inductive Eq : α → α → Prop where
  /-- `Eq.refl a : a = a` is reflexivity, the unique constructor of the
  equality type. See also `rfl`, which is usually used instead. -/
  | refl (a : α) : Eq a a

/-- Non-dependent recursor for the equality type. -/
```
