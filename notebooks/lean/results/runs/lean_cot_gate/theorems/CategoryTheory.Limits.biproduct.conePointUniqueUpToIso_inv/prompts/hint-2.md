## Current goal
```
⊢ (ι f j ≫ (IsLimit.conePointUniqueUpToIso hb.isLimit (isLimit f)).inv) ≫ (Bicone.toCone b).π.app j' =
    (ι f j ≫ desc b.ι) ≫ (Bicone.toCone b).π.app j'
```

## Full tactic state
```
J : Type w
C : Type u
inst✝⁴ : Category.{v, u} C
inst✝³ : HasZeroMorphisms C
D : Type uD
inst✝² : Category.{uD', uD} D
inst✝¹ : HasZeroMorphisms D
f : J → C
inst✝ : HasBiproduct f
b : Bicone f
hb : Bicone.IsBilimit b
j : J
j' : Discrete J
⊢ (ι f j ≫ (IsLimit.conePointUniqueUpToIso hb.isLimit (isLimit f)).inv) ≫ (Bicone.toCone b).π.app j' =
    (ι f j ≫ desc b.ι) ≫ (Bicone.toCone b).π.app j'
```

## Proof so far (1 tactic)
```lean
refine' biproduct.hom_ext' _ _ fun j => hb.isLimit.hom_ext fun j' => _
```

## Theorem
`CategoryTheory.Limits.biproduct.conePointUniqueUpToIso_inv` in `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`

## Premises used in the next tactic
- `CategoryTheory.Category.assoc`
- `CategoryTheory.Limits.IsLimit.conePointUniqueUpToIso_inv_comp`
- `CategoryTheory.Limits.Bicone.toCone_π_app`
- `CategoryTheory.Limits.biproduct.bicone_π`
- `CategoryTheory.Limits.biproduct.ι_desc`
- `CategoryTheory.Limits.biproduct.ι_π`

## Premise signatures
### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Limits.IsLimit.conePointUniqueUpToIso_inv_comp` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem conePointUniqueUpToIso_inv_comp {s t : Cone F} (P : IsLimit s) (Q : IsLimit t) (j : J) :
    (conePointUniqueUpToIso P Q).inv ≫ s.π.app j = t.π.app j
```

### `CategoryTheory.Limits.Bicone.toCone_π_app` (commanddeclaration)
```lean
@[simp]
theorem toCone_π_app (B : Bicone F) (j : Discrete J) : B.toCone.π.app j = B.π j.as
```

### `CategoryTheory.Limits.biproduct.bicone_π` (commanddeclaration)
```lean
@[simp]
theorem biproduct.bicone_π (f : J → C) [HasBiproduct f] (b : J) :
    (biproduct.bicone f).π b = biproduct.π f b
```

### `CategoryTheory.Limits.biproduct.ι_desc` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem biproduct.ι_desc {f : J → C} [HasBiproduct f] {P : C} (p : ∀ b, f b ⟶ P) (j : J) :
    biproduct.ι f j ≫ biproduct.desc p = p j
```

### `CategoryTheory.Limits.biproduct.ι_π` (commanddeclaration)
```lean
@[reassoc]
theorem biproduct.ι_π [DecidableEq J] (f : J → C) [HasBiproduct f] (j j' : J) :
    biproduct.ι f j ≫ biproduct.π f j' = if h : j = j' then eqToHom (congr_arg f h) else 0
```

## Premise full source (with proof)
### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Limits.IsLimit.conePointUniqueUpToIso_inv_comp` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/IsLimit.lean`
```lean
@[reassoc (attr := simp)]
theorem conePointUniqueUpToIso_inv_comp {s t : Cone F} (P : IsLimit s) (Q : IsLimit t) (j : J) :
    (conePointUniqueUpToIso P Q).inv ≫ s.π.app j = t.π.app j :=
  (uniqueUpToIso P Q).inv.w _
```

### `CategoryTheory.Limits.Bicone.toCone_π_app` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`
```lean
@[simp]
theorem toCone_π_app (B : Bicone F) (j : Discrete J) : B.toCone.π.app j = B.π j.as := rfl
```

### `CategoryTheory.Limits.biproduct.bicone_π` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`
```lean
@[simp]
theorem biproduct.bicone_π (f : J → C) [HasBiproduct f] (b : J) :
    (biproduct.bicone f).π b = biproduct.π f b := rfl
```

### `CategoryTheory.Limits.biproduct.ι_desc` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`
```lean
@[reassoc (attr := simp)]
theorem biproduct.ι_desc {f : J → C} [HasBiproduct f] {P : C} (p : ∀ b, f b ⟶ P) (j : J) :
    biproduct.ι f j ≫ biproduct.desc p = p j := (biproduct.isColimit f).fac _ ⟨j⟩
```

### `CategoryTheory.Limits.biproduct.ι_π` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`
```lean
/-- Note that as this lemma has an `if` in the statement, we include a `DecidableEq` argument.
This means you may not be able to `simp` using this lemma unless you `open scoped Classical`. -/
@[reassoc]
theorem biproduct.ι_π [DecidableEq J] (f : J → C) [HasBiproduct f] (j j' : J) :
    biproduct.ι f j ≫ biproduct.π f j' = if h : j = j' then eqToHom (congr_arg f h) else 0 := by
  convert (biproduct.bicone f).ι_π j j'
```
