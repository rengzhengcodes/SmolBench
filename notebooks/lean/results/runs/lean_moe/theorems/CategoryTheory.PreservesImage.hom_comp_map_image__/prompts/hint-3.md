## Current goal
```
⊢ (iso L f).hom ≫ L.map (image.ι f) = image.ι (L.map f)
```

## Full tactic state
```
A : Type u₁
B : Type u₂
inst✝⁷ : Category.{v₁, u₁} A
inst✝⁶ : Category.{v₂, u₂} B
inst✝⁵ : HasEqualizers A
inst✝⁴ : HasImages A
inst✝³ : StrongEpiCategory B
inst✝² : HasImages B
L : A ⥤ B
inst✝¹ : {X Y Z : A} → (f : X ⟶ Z) → (g : Y ⟶ Z) → PreservesLimit (cospan f g) L
inst✝ : {X Y Z : A} → (f : X ⟶ Y) → (g : X ⟶ Z) → PreservesColimit (span f g) L
X Y : A
f : X ⟶ Y
⊢ (iso L f).hom ≫ L.map (image.ι f) = image.ι (L.map f)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.PreservesImage.hom_comp_map_image_ι` in `Mathlib/CategoryTheory/Limits/Preserves/Shapes/Images.lean`

## Premises used in the next tactic
- `CategoryTheory.PreservesImage.iso_hom`
- `CategoryTheory.Limits.image.lift_fac`

## Premise signatures
### `CategoryTheory.PreservesImage.iso_hom`
_(not found in premise corpus)_

### `CategoryTheory.Limits.image.lift_fac` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem image.lift_fac (F' : MonoFactorisation f) : image.lift F' ≫ F'.m = image.ι f
```

## Premise full source (with proof)
### `CategoryTheory.PreservesImage.iso_hom`
_(not found in premise corpus)_

### `CategoryTheory.Limits.image.lift_fac` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Images.lean`
```lean
@[reassoc (attr := simp)]
theorem image.lift_fac (F' : MonoFactorisation f) : image.lift F' ≫ F'.m = image.ι f :=
  (Image.isImage f).lift_fac F'
```

## Transitive premise context (1-hop, 2/2 premises, ≈230 tokens)
### `Lean.Parser.Category.attr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Notation.lean`
```lean
/-- `attr` is a builtin syntax category for attributes.
Declarations can be annotated with attributes using the `@[...]` notation. -/
def attr : Category := {}

/-- `stx` is a builtin syntax category for syntax. This is the abbreviated
parser notation used inside `syntax` and `macro` declarations. -/
```

### `CategoryTheory.Limits.MonoFactorisation` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Images.lean`
```lean
/-- A factorisation of a morphism `f = e ≫ m`, with `m` monic. -/
structure MonoFactorisation (f : X ⟶ Y) where
  I : C -- Porting note: violates naming conventions but can't think a better replacement
  m : I ⟶ Y
  [m_mono : Mono m]
  e : X ⟶ I
  fac : e ≫ m = f := by aesop_cat
```
