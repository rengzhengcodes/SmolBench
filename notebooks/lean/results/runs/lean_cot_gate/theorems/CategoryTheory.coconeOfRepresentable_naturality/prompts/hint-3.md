## Current goal
```
⊢ ((coconeOfRepresentable P₁).ι.app j ≫ α).app T f =
    ((coconeOfRepresentable P₂).ι.app ((CategoryOfElements.map α).op.obj j)).app T f
```

## Full tactic state
```
case w.h.h
C : Type u₁
inst✝¹ : SmallCategory C
ℰ : Type u₂
inst✝ : Category.{u₁, u₂} ℰ
A : C ⥤ ℰ
P₁ P₂ : Cᵒᵖ ⥤ Type u₁
α : P₁ ⟶ P₂
j : (Functor.Elements P₁)ᵒᵖ
T : Cᵒᵖ
f : ((functorToRepresentables P₁).obj j).obj T
⊢ ((coconeOfRepresentable P₁).ι.app j ≫ α).app T f =
    ((coconeOfRepresentable P₂).ι.app ((CategoryOfElements.map α).op.obj j)).app T f
```

## Proof so far (1 tactic)
```lean
ext T f
```

## Theorem
`CategoryTheory.coconeOfRepresentable_naturality` in `Mathlib/CategoryTheory/Limits/Presheaf.lean`

## Premises used in the next tactic
- `CategoryTheory.coconeOfRepresentable_ι_app`
- `CategoryTheory.FunctorToTypes.naturality`

## Premise signatures
### `CategoryTheory.coconeOfRepresentable_ι_app` (commanddeclaration)
```lean
theorem coconeOfRepresentable_ι_app (P : Cᵒᵖ ⥤ Type u₁) (j : P.Elementsᵒᵖ) :
    (coconeOfRepresentable P).ι.app j = (yonedaSectionsSmall _ _).inv j.unop.2
```

### `CategoryTheory.FunctorToTypes.naturality` (commanddeclaration)
```lean
theorem naturality (f : X ⟶ Y) (x : F.obj X) : σ.app Y ((F.map f) x) = (G.map f) (σ.app X x)
```

## Premise full source (with proof)
### `CategoryTheory.coconeOfRepresentable_ι_app` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Presheaf.lean`
```lean
/-- An explicit formula for the legs of the cocone `coconeOfRepresentable`. -/
theorem coconeOfRepresentable_ι_app (P : Cᵒᵖ ⥤ Type u₁) (j : P.Elementsᵒᵖ) :
    (coconeOfRepresentable P).ι.app j = (yonedaSectionsSmall _ _).inv j.unop.2 :=
  colimit.ι_desc _ _
```

### `CategoryTheory.FunctorToTypes.naturality` (commanddeclaration) at `Mathlib/CategoryTheory/Types.lean`
```lean
theorem naturality (f : X ⟶ Y) (x : F.obj X) : σ.app Y ((F.map f) x) = (G.map f) (σ.app X x) :=
  congr_fun (σ.naturality f) x
```

## Transitive premise context (1-hop, 5/5 premises, ≈617 tokens)
### `Lean.Parser.Term.explicit` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Term.lean`
```lean
/--
`@x` disables automatic insertion of implicit parameters of the constant `x`.
`@e` for any term `e` also disables the insertion of implicit lambdas at this position.
-/
@[builtin_term_parser] def explicit := leading_parser
  "@" >> termParser maxPrec
/--
`.(e)` marks an "inaccessible pattern", which does not influence evaluation of the pattern match, but may be necessary for type-checking.
In contrast to regular patterns, `e` may be an arbitrary term of the appropriate type.
-/
```

### `FirstOrder.Language.Relations.formula` (commanddeclaration) at `Mathlib/ModelTheory/Syntax.lean`
```lean
/-- Applies a relation to terms as a bounded formula. -/
def Relations.formula (R : L.Relations n) (ts : Fin n → L.Term α) : L.Formula α :=
  R.boundedFormula fun i => (ts i).relabel Sum.inl
```

### `CategoryTheory.coconeOfRepresentable` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Presheaf.lean`
```lean
/-- This is a cocone with point `P` for the functor `functorToRepresentables P`. It is shown in
`colimitOfRepresentable P` that this cocone is a colimit: that is, we have exhibited an arbitrary
presheaf `P` as a colimit of representables.

The construction of [MM92], Chapter I, Section 5, Corollary 3.
-/
noncomputable def coconeOfRepresentable (P : Cᵒᵖ ⥤ Type u₁) : Cocone (functorToRepresentables P) :=
  Cocone.extend (colimit.cocone _) (extendAlongYonedaYoneda.hom.app P)
```

### `CategoryTheory.yonedaSectionsSmall` (commanddeclaration) at `Mathlib/CategoryTheory/Yoneda.lean`
```lean
/-- When `C` is a small category, we can restate the isomorphism from `yoneda_sections`
without having to change universes.
-/
def yonedaSectionsSmall {C : Type u₁} [SmallCategory C] (X : C) (F : Cᵒᵖ ⥤ Type u₁) :
    (yoneda.obj X ⟶ F) ≅ F.obj (op X) :=
  yonedaSections X F ≪≫ uliftTrivial _
```

### `congr_fun` (stdtacticaliasalias) at `.lake/packages/std/Std/Logic.lean`
```lean
alias congr_fun := congrFun
alias congr_fun₂ := congrFun₂
alias congr_fun₃ := congrFun₃
```
