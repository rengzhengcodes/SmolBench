## Current goal
```
⊢ (leftUnitor X).inv ≫ map (𝟙 (⊤_ C)) f = f ≫ (leftUnitor Y).inv
```

## Full tactic state
```
C : Type u
inst✝² : Category.{v, u} C
X Y : C
inst✝¹ : HasTerminal C
inst✝ : HasBinaryProducts C
f : X ⟶ Y
⊢ (leftUnitor X).inv ≫ map (𝟙 (⊤_ C)) f = f ≫ (leftUnitor Y).inv
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.Limits.prod.leftUnitor_inv_naturality` in `Mathlib/CategoryTheory/Limits/Shapes/BinaryProducts.lean`

## Premises used in the next tactic
- `CategoryTheory.Iso.inv_comp_eq`
- `CategoryTheory.Category.assoc`
- `CategoryTheory.Iso.eq_comp_inv`
- `CategoryTheory.Limits.prod.leftUnitor_hom_naturality`

## Premise signatures
### `CategoryTheory.Iso.inv_comp_eq` (commanddeclaration)
```lean
theorem inv_comp_eq (α : X ≅ Y) {f : X ⟶ Z} {g : Y ⟶ Z} : α.inv ≫ f = g ↔ f = α.hom ≫ g
```

### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Iso.eq_comp_inv` (commanddeclaration)
```lean
theorem eq_comp_inv (α : X ≅ Y) {f : Z ⟶ Y} {g : Z ⟶ X} : g = f ≫ α.inv ↔ g ≫ α.hom = f
```

### `CategoryTheory.Limits.prod.leftUnitor_hom_naturality` (commanddeclaration)
```lean
@[reassoc]
theorem prod.leftUnitor_hom_naturality [HasBinaryProducts C] (f : X ⟶ Y) :
    prod.map (𝟙 _) f ≫ (prod.leftUnitor Y).hom = (prod.leftUnitor X).hom ≫ f
```

## Premise full source (with proof)
### `CategoryTheory.Iso.inv_comp_eq` (commanddeclaration) at `Mathlib/CategoryTheory/Iso.lean`
```lean
theorem inv_comp_eq (α : X ≅ Y) {f : X ⟶ Z} {g : Y ⟶ Z} : α.inv ≫ f = g ↔ f = α.hom ≫ g :=
  ⟨fun H => by simp [H.symm], fun H => by simp [H]⟩
```

### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Iso.eq_comp_inv` (commanddeclaration) at `Mathlib/CategoryTheory/Iso.lean`
```lean
theorem eq_comp_inv (α : X ≅ Y) {f : Z ⟶ Y} {g : Z ⟶ X} : g = f ≫ α.inv ↔ g ≫ α.hom = f :=
  (comp_inv_eq α.symm).symm
```

### `CategoryTheory.Limits.prod.leftUnitor_hom_naturality` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/BinaryProducts.lean`
```lean
@[reassoc]
theorem prod.leftUnitor_hom_naturality [HasBinaryProducts C] (f : X ⟶ Y) :
    prod.map (𝟙 _) f ≫ (prod.leftUnitor Y).hom = (prod.leftUnitor X).hom ≫ f :=
  prod.map_snd _ _
```

## Transitive premise context (1-hop, 2/2 premises, ≈149 tokens)
### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```

### `CategoryTheory.Limits.HasBinaryProducts` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/BinaryProducts.lean`
```lean
/-- `HasBinaryProducts` represents a choice of product for every pair of objects.

See <https://stacks.math.columbia.edu/tag/001T>.
-/
abbrev HasBinaryProducts :=
  HasLimitsOfShape (Discrete WalkingPair) C
```
