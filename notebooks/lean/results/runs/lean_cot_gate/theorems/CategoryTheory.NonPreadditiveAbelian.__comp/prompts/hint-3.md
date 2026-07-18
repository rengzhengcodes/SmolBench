## Current goal
```
⊢ prod.lift (𝟙 X) 0 ≫ σ ≫ g = g
```

## Full tactic state
```
C : Type u
inst✝¹ : Category.{v, u} C
inst✝ : NonPreadditiveAbelian C
X Y : C
f : X ⟶ Y
g : (CokernelCofork.ofπ σ ⋯).pt ⟶ Y
hg : Cofork.π (CokernelCofork.ofπ σ ⋯) ≫ g = prod.map f f ≫ σ
⊢ prod.lift (𝟙 X) 0 ≫ σ ≫ g = g
```

## Proof so far (8 tactics)
```lean
obtain ⟨g, hg⟩ :=
  CokernelCofork.IsColimit.desc' isColimitσ (Limits.prod.map f f ≫ σ) (by
    rw [prod.diag_map_assoc, diag_σ, comp_zero])
suffices hfg : f = g by rw [← hg, Cofork.π_ofπ, hfg]
calc
  f = f ≫ prod.lift (𝟙 Y) 0 ≫ σ := by rw [lift_σ, Category.comp_id]
  _ = prod.lift (𝟙 X) 0 ≫ Limits.prod.map f f ≫ σ := by rw [lift_map_assoc]
  _ = prod.lift (𝟙 X) 0 ≫ σ ≫ g := by rw [← hg, CokernelCofork.π_ofπ]
  _ = g := by rw [← Category.assoc, lift_σ, Category.id_comp]
rw [prod.diag_map_assoc, diag_σ, comp_zero]
rw [← hg, Cofork.π_ofπ, hfg]
rw [lift_σ, Category.comp_id]
rw [lift_map_assoc]
rw [← hg, CokernelCofork.π_ofπ]
```

## Theorem
`CategoryTheory.NonPreadditiveAbelian.σ_comp` in `Mathlib/CategoryTheory/Abelian/NonPreadditive.lean`

## Premises used in the next tactic
- `CategoryTheory.Category.assoc`
- `CategoryTheory.NonPreadditiveAbelian.lift_σ`
- `CategoryTheory.Category.id_comp`

## Premise signatures
### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.NonPreadditiveAbelian.lift_σ` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem lift_σ {X : C} : prod.lift (𝟙 X) 0 ≫ σ = 𝟙 X
```

### `CategoryTheory.Category.id_comp`
_(not found in premise corpus)_

## Premise full source (with proof)
### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.NonPreadditiveAbelian.lift_σ` (commanddeclaration) at `Mathlib/CategoryTheory/Abelian/NonPreadditive.lean`
```lean
@[reassoc (attr := simp)]
theorem lift_σ {X : C} : prod.lift (𝟙 X) 0 ≫ σ = 𝟙 X := by rw [← Category.assoc, IsIso.hom_inv_id]
```

### `CategoryTheory.Category.id_comp`
_(not found in premise corpus)_

## Transitive premise context (1-hop, 1/1 premises, ≈99 tokens)
### `Lean.Parser.Category.attr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Notation.lean`
```lean
/-- `attr` is a builtin syntax category for attributes.
Declarations can be annotated with attributes using the `@[...]` notation. -/
def attr : Category := {}

/-- `stx` is a builtin syntax category for syntax. This is the abbreviated
parser notation used inside `syntax` and `macro` declarations. -/
```
