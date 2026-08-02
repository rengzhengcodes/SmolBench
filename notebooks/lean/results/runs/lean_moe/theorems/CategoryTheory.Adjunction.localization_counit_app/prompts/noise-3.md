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

## Filler (hint:2 → hint:3 token-match, ≈681 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit
