## Current goal
```
⊢ (localization adj L₁ W₁ L₂ W₂ G' F').unit.app (L₁.obj X₁) =
    L₁.map (adj.unit.app X₁) ≫
      (CatCommSq.iso F L₂ L₁ F').hom.app (G.obj X₁) ≫ F'.map ((CatCommSq.iso G L₁ L₂ G').hom.app X₁)
```

## Full tactic state
```
C₁ : Type u_1
C₂ : Type u_2
D₁ : Type u_3
D₂ : Type u_4
inst✝⁷ : Category.{u_6, u_1} C₁
inst✝⁶ : Category.{u_8, u_2} C₂
inst✝⁵ : Category.{u_5, u_3} D₁
inst✝⁴ : Category.{u_7, u_4} D₂
G : C₁ ⥤ C₂
F : C₂ ⥤ C₁
adj : G ⊣ F
L₁ : C₁ ⥤ D₁
W₁ : MorphismProperty C₁
inst✝³ : Functor.IsLocalization L₁ W₁
L₂ : C₂ ⥤ D₂
W₂ : MorphismProperty C₂
inst✝² : Functor.IsLocalization L₂ W₂
G' : D₁ ⥤ D₂
F' : D₂ ⥤ D₁
inst✝¹ : CatCommSq G L₁ L₂ G'
inst✝ : CatCommSq F L₂ L₁ F'
X₁ : C₁
⊢ (localization adj L₁ W₁ L₂ W₂ G' F').unit.app (L₁.obj X₁) =
    L₁.map (adj.unit.app X₁) ≫
      (CatCommSq.iso F L₂ L₁ F').hom.app (G.obj X₁) ≫ F'.map ((CatCommSq.iso G L₁ L₂ G').hom.app X₁)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.Adjunction.localization_unit_app` in `Mathlib/CategoryTheory/Localization/Adjunction.lean`

## Premises used in the next tactic
- `CategoryTheory.Adjunction.Localization.ε_app`

## Premise signatures
### `CategoryTheory.Adjunction.Localization.ε_app` (lemma)
```lean
lemma ε_app (X₁ : C₁) :
    (ε adj L₁ W₁ L₂ G' F').app (L₁.obj X₁) =
      L₁.map (adj.unit.app X₁) ≫ (CatCommSq.iso F L₂ L₁ F').hom.app (G.obj X₁) ≫
        F'.map ((CatCommSq.iso G L₁ L₂ G').hom.app X₁)
```

## Premise full source (with proof)
### `CategoryTheory.Adjunction.Localization.ε_app` (lemma) at `Mathlib/CategoryTheory/Localization/Adjunction.lean`
```lean
lemma ε_app (X₁ : C₁) :
    (ε adj L₁ W₁ L₂ G' F').app (L₁.obj X₁) =
      L₁.map (adj.unit.app X₁) ≫ (CatCommSq.iso F L₂ L₁ F').hom.app (G.obj X₁) ≫
        F'.map ((CatCommSq.iso G L₁ L₂ G').hom.app X₁) := by
  letI : Lifting L₁ W₁ ((G ⋙ F) ⋙ L₁) (G' ⋙ F') :=
    Lifting.mk (CatCommSq.hComp G F L₁ L₂ L₁ G' F').iso'.symm
  simp only [ε, liftNatTrans_app, Lifting.iso, Iso.symm,
    Functor.id_obj, Functor.comp_obj, Lifting.id_iso', Functor.rightUnitor_hom_app,
      whiskerRight_app, CatCommSq.hComp_iso'_hom_app, id_comp]

/-- Auxiliary definition of the counit morphism for the adjunction `Adjunction.localization` -/
```

## Transitive premise context (1-hop, 5/5 premises, ≈656 tokens)
### `adj` (commanddeclaration) at `Mathlib/Algebra/Category/MonCat/Adjunctions.lean`
```lean
/-- The free-forgetful adjunction for monoids. -/
def adj : free ⊣ forget MonCat.{u} :=
  Adjunction.mkOfHomEquiv
    { homEquiv := fun X G => FreeMonoid.lift.symm
      homEquiv_naturality_left_symm := fun _ _ => FreeMonoid.hom_eq (fun _ => rfl) }
```

### `Lean.Parser.Term.letI` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Term.lean`
```lean
/-- `letI` behaves like `let`, but inlines the value instead of producing a `let_fun` term. -/
@[builtin_term_parser] def «letI» := leading_parser
  withPosition ("letI " >> haveDecl) >> optSemicolon termParser
```

### `CategoryTheory.Localization.Lifting` (commanddeclaration) at `Mathlib/CategoryTheory/Localization/Predicate.lean`
```lean
/-- When `L : C ⥤ D` is a localization functor for `W : MorphismProperty C` and
`F : C ⥤ E` is a functor, we shall say that `F' : D ⥤ E` lifts `F` if the obvious diagram
is commutative up to an isomorphism. -/
class Lifting (W : MorphismProperty C) (F : C ⥤ E) (F' : D ⥤ E) where
  /-- the isomorphism relating the localization functor and the two other given functors -/
  iso' : L ⋙ F' ≅ F
```

### `CategoryTheory.Localization.liftNatTrans_app` (commanddeclaration) at `Mathlib/CategoryTheory/Localization/Predicate.lean`
```lean
@[simp]
theorem liftNatTrans_app (F₁ F₂ : C ⥤ E) (F₁' F₂' : D ⥤ E) [Lifting L W F₁ F₁'] [Lifting L W F₂ F₂']
    (τ : F₁ ⟶ F₂) (X : C) :
    (liftNatTrans L W F₁ F₂ F₁' F₂' τ).app (L.obj X) =
      (Lifting.iso L W F₁ F₁').hom.app X ≫ τ.app X ≫ (Lifting.iso L W F₂ F₂').inv.app X :=
  congr_app (Functor.image_preimage (whiskeringLeftFunctor' L W E) _) X
```

### `CategoryTheory.Monoidal.whiskerRight_app` (commanddeclaration) at `Mathlib/CategoryTheory/Monoidal/FunctorCategory.lean`
```lean
@[simp]
theorem whiskerRight_app {F G F' : C ⥤ D} {α : F ⟶ G} {X} :
    (α ▷ F').app X = α.app X ▷ F'.obj X :=
  rfl
```
