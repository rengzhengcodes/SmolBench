## Current goal
```
⊢ (localization adj L₁ W₁ L₂ W₂ G' F').counit.app (L₂.obj X₂) =
    G'.map ((CatCommSq.iso F L₂ L₁ F').inv.app X₂) ≫
      (CatCommSq.iso G L₁ L₂ G').inv.app (F.obj X₂) ≫ L₂.map (adj.counit.app X₂)
```

## Full tactic state
```
C₁ : Type u_1
C₂ : Type u_2
D₁ : Type u_3
D₂ : Type u_4
inst✝⁷ : Category.{u_8, u_1} C₁
inst✝⁶ : Category.{u_7, u_2} C₂
inst✝⁵ : Category.{u_6, u_3} D₁
inst✝⁴ : Category.{u_5, u_4} D₂
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
X₂ : C₂
⊢ (localization adj L₁ W₁ L₂ W₂ G' F').counit.app (L₂.obj X₂) =
    G'.map ((CatCommSq.iso F L₂ L₁ F').inv.app X₂) ≫
      (CatCommSq.iso G L₁ L₂ G').inv.app (F.obj X₂) ≫ L₂.map (adj.counit.app X₂)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.Adjunction.localization_counit_app` in `Mathlib/CategoryTheory/Localization/Adjunction.lean`

## Premises used in the next tactic
- `CategoryTheory.Adjunction.Localization.η_app`

## Premise signatures
### `CategoryTheory.Adjunction.Localization.η_app` (lemma)
```lean
lemma η_app (X₂ : C₂) :
    (η adj L₁ L₂ W₂ G' F').app (L₂.obj X₂) =
      G'.map ((CatCommSq.iso F L₂ L₁ F').inv.app X₂) ≫
        (CatCommSq.iso G L₁ L₂ G').inv.app (F.obj X₂) ≫
        L₂.map (adj.counit.app X₂)
```

## Premise full source (with proof)
### `CategoryTheory.Adjunction.Localization.η_app` (lemma) at `Mathlib/CategoryTheory/Localization/Adjunction.lean`
```lean
lemma η_app (X₂ : C₂) :
    (η adj L₁ L₂ W₂ G' F').app (L₂.obj X₂) =
      G'.map ((CatCommSq.iso F L₂ L₁ F').inv.app X₂) ≫
        (CatCommSq.iso G L₁ L₂ G').inv.app (F.obj X₂) ≫
        L₂.map (adj.counit.app X₂) := by
  letI : Lifting L₂ W₂ ((F ⋙ G) ⋙ L₂) (F' ⋙ G') :=
    Lifting.mk (CatCommSq.hComp F G L₂ L₁ L₂ F' G').iso'.symm
  simp only [η, liftNatTrans_app, Lifting.iso, Iso.symm, CatCommSq.hComp_iso'_inv_app,
    whiskerRight_app, Lifting.id_iso', Functor.rightUnitor_inv_app, comp_id, assoc]
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
