## Current goal
```
⊢ unitForward μ X (YonedaCollection.map₁ (restrictedYonedaObjMap₁ ε hε) p) = ε.app (op X) (unitForward η X p)
```

## Full tactic state
```
C : Type u
inst✝ : Category.{v, u} C
A F G : Cᵒᵖ ⥤ Type v
η : F ⟶ A
μ : G ⟶ A
ε : F ⟶ G
hε : ε ≫ μ = η
X : C
p : YonedaCollection (restrictedYonedaObj η) X
⊢ unitForward μ X (YonedaCollection.map₁ (restrictedYonedaObjMap₁ ε hε) p) = ε.app (op X) (unitForward η X p)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.OverPresheafAux.unitForward_naturality₁` in `Mathlib/CategoryTheory/Comma/Presheaf.lean`

## Premises used in the next tactic
- `CategoryTheory.OverPresheafAux.unitForward`

## Premise signatures
### `CategoryTheory.OverPresheafAux.unitForward` (commanddeclaration)
```lean
def unitForward {F : Cᵒᵖ ⥤ Type v} (η : F ⟶ A) (X : C) :
    YonedaCollection (restrictedYonedaObj η) X → F.obj (op X)
```

## Premise full source (with proof)
### `CategoryTheory.OverPresheafAux.unitForward` (commanddeclaration) at `Mathlib/CategoryTheory/Comma/Presheaf.lean`
```lean
/-- Forward direction of the unit. -/
def unitForward {F : Cᵒᵖ ⥤ Type v} (η : F ⟶ A) (X : C) :
    YonedaCollection (restrictedYonedaObj η) X → F.obj (op X) :=
  fun p => p.snd.val
```
