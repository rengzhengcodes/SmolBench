## Current goal
```
⊢ IsLocalizedEquivalence Φ
```

## Full tactic state
```
C₁ : Type u₁
C₂ : Type u₂
C₃ : Type u₃
D₁ : Type u₄
D₂ : Type u₅
D₃ : Type u₆
inst✝⁸ : Category.{v₁, u₁} C₁
inst✝⁷ : Category.{v₂, u₂} C₂
inst✝⁶ : Category.{v₃, u₃} C₃
inst✝⁵ : Category.{v₄, u₄} D₁
inst✝⁴ : Category.{v₅, u₅} D₂
inst✝³ : Category.{v₆, u₅} D₂
W₁ : MorphismProperty C₁
W₂ : MorphismProperty C₂
W₃ : MorphismProperty C₃
Φ : LocalizerMorphism W₁ W₂
L₁ : C₁ ⥤ D₁
inst✝² : Functor.IsLocalization L₁ W₁
L₂ : C₂ ⥤ D₂
inst✝¹ : Functor.IsLocalization L₂ W₂
G : D₁ ⥤ D₂
inst✝ : Functor.IsLocalization (Φ.functor ⋙ L₂) W₁
this : CatCommSq Φ.functor (Φ.functor ⋙ L₂) L₂ (𝟭 D₂)
⊢ IsLocalizedEquivalence Φ
```

## Proof so far (1 tactic)
```lean
have : CatCommSq Φ.functor (Φ.functor ⋙ L₂) L₂ (𝟭 D₂) :=
  CatCommSq.mk (Functor.rightUnitor _).symm
```

## Theorem
`CategoryTheory.LocalizerMorphism.IsLocalizedEquivalence.of_isLocalization_of_isLocalization` in `Mathlib/CategoryTheory/Localization/LocalizerMorphism.lean`

## Premises used in the next tactic
- `CategoryTheory.LocalizerMorphism.IsLocalizedEquivalence.mk'`

## Premise signatures
### `CategoryTheory.LocalizerMorphism.IsLocalizedEquivalence.mk'` (lemma)
```lean
lemma IsLocalizedEquivalence.mk' [CatCommSq Φ.functor L₁ L₂ G] [IsEquivalence G] :
    Φ.IsLocalizedEquivalence where
  nonempty_isEquivalence
```

## Premise full source (with proof)
### `CategoryTheory.LocalizerMorphism.IsLocalizedEquivalence.mk'` (lemma) at `Mathlib/CategoryTheory/Localization/LocalizerMorphism.lean`
```lean
lemma IsLocalizedEquivalence.mk' [CatCommSq Φ.functor L₁ L₂ G] [IsEquivalence G] :
    Φ.IsLocalizedEquivalence where
  nonempty_isEquivalence := by
    rw [Φ.nonempty_isEquivalence_iff W₁.Q W₂.Q (Φ.localizedFunctor W₁.Q W₂.Q) L₁ L₂ G]
    exact ⟨inferInstance⟩

/-- If a `LocalizerMorphism` is a localized equivalence, then any compatible functor
between the localized categories is an equivalence. -/
```

## Transitive premise context (1-hop, 8/8 premises, ≈1267 tokens)
### `CategoryTheory.CatCommSq` (commanddeclaration) at `Mathlib/CategoryTheory/CatCommSq.lean`
```lean
/-- `CatCommSq T L R B` expresses that there is a 2-commutative square of functors, where
the functors `T`, `L`, `R` and `B` are respectively the left, top, right and bottom functors
of the square. -/
@[ext]
class CatCommSq where
  /-- the isomorphism corresponding to a 2-commutative diagram -/
  iso' : T ⋙ R ≅ L ⋙ B
```

### `CategoryTheory.IsEquivalence` (commanddeclaration) at `Mathlib/CategoryTheory/Equivalence.lean`
```lean
/-- A functor that is part of a (half) adjoint equivalence -/
class IsEquivalence (F : C ⥤ D) where mk' ::
  /-- The inverse functor to `F` -/
  inverse : D ⥤ C
  /-- Composition `F ⋙ inverse` is isomorphic to the identity. -/
  unitIso : 𝟭 C ≅ F ⋙ inverse
  /-- Composition `inverse ⋙ F` is isomorphic to the identity. -/
  counitIso : inverse ⋙ F ≅ 𝟭 D
  /-- The natural isomorphisms are inverse. -/
  functor_unitIso_comp :
    ∀ X : C,
      F.map ((unitIso.hom : 𝟭 C ⟶ F ⋙ inverse).app X) ≫ counitIso.hom.app (F.obj X) =
        𝟙 (F.obj X) := by
    aesop_cat
```

### `CategoryTheory.LocalizerMorphism.IsLocalizedEquivalence` (commanddeclaration) at `Mathlib/CategoryTheory/Localization/LocalizerMorphism.lean`
```lean
/-- Condition that a `LocalizerMorphism` induces an equivalence on the localized categories -/
class IsLocalizedEquivalence : Prop :=
  /-- the induced functor on the constructed localized categories is an equivalence -/
  nonempty_isEquivalence : Nonempty (IsEquivalence (Φ.localizedFunctor W₁.Q W₂.Q))
```

### `CategoryTheory.LocalizerMorphism.nonempty_isEquivalence_iff` (lemma) at `Mathlib/CategoryTheory/Localization/LocalizerMorphism.lean`
```lean
lemma nonempty_isEquivalence_iff : Nonempty (IsEquivalence G) ↔ Nonempty (IsEquivalence G') := by
  constructor
  · rintro ⟨e⟩
    exact ⟨Φ.isEquivalence_imp L₁ L₂ G L₁' L₂' G'⟩
  · rintro ⟨e'⟩
    exact ⟨Φ.isEquivalence_imp L₁' L₂' G' L₁ L₂ G⟩
```

### `CategoryTheory.LocalizerMorphism.localizedFunctor` (commanddeclaration) at `Mathlib/CategoryTheory/Localization/LocalizerMorphism.lean`
```lean
/-- When `Φ : LocalizerMorphism W₁ W₂` and that `L₁` and `L₂` are localization functors
for `W₁` and `W₂`, then `Φ.localizedFunctor L₁ L₂` is the induced functor on the
localized categories. --/
noncomputable def localizedFunctor : D₁ ⥤ D₂ :=
  lift (Φ.functor ⋙ L₂) (Φ.inverts _) L₁
```

### `inferInstance` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`inferInstance` synthesizes a value of any target type by typeclass
inference. This function has the same type signature as the identity
function, but the square brackets on the `[i : α]` argument means that it will
attempt to construct this argument by typeclass inference. (This will fail if
`α` is not a `class`.) Example:
```
#check (inferInstance : Inhabited Nat) -- Inhabited Nat

def foo : Inhabited (Nat × Nat) :=
  inferInstance

example : foo.default = (default, default) :=
  rfl
```
-/
abbrev inferInstance {α : Sort u} [i : α] : α := i
```

### `CategoryTheory.LocalizerMorphism` (commanddeclaration) at `Mathlib/CategoryTheory/Localization/LocalizerMorphism.lean`
```lean
/-- If `W₁ : MorphismProperty C₁` and `W₂ : MorphismProperty C₂`, a `LocalizerMorphism W₁ W₂`
is the datum of a functor `C₁ ⥤ C₂` which sends morphisms in `W₁` to morphisms in `W₂` -/
structure LocalizerMorphism where
  /-- a functor between the two categories -/
  functor : C₁ ⥤ C₂
  /-- the functor is compatible with the `MorphismProperty` -/
  map : W₁ ⊆ W₂.inverseImage functor
```

### `StructureGroupoid.compatible` (commanddeclaration) at `Mathlib/Geometry/Manifold/ChartedSpace.lean`
```lean
/-- Reformulate in the `StructureGroupoid` namespace the compatibility condition of charts in a
charted space admitting a structure groupoid, to make it more easily accessible with dot
notation. -/
theorem StructureGroupoid.compatible {H : Type*} [TopologicalSpace H] (G : StructureGroupoid H)
    {M : Type*} [TopologicalSpace M] [ChartedSpace H M] [HasGroupoid M G]
    {e e' : PartialHomeomorph M H} (he : e ∈ atlas H M) (he' : e' ∈ atlas H M) : e.symm ≫ₕ e' ∈ G :=
  HasGroupoid.compatible he he'
```
