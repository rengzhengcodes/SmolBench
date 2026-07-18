## Current goal
```
⊢ toRightDerivedZero' P F ≫
      HomologicalComplex.iCycles ((Functor.mapHomologicalComplex F (ComplexShape.up ℕ)).obj P.cocomplex) 0 =
    F.map (P.ι.f 0)
```

## Full tactic state
```
C : Type u
inst✝⁵ : Category.{v, u} C
D : Type u_1
inst✝⁴ : Category.{u_2, u_1} D
inst✝³ : Abelian C
inst✝² : HasInjectiveResolutions C
inst✝¹ : Abelian D
X : C
P : InjectiveResolution X
F : C ⥤ D
inst✝ : Functor.Additive F
⊢ toRightDerivedZero' P F ≫
      HomologicalComplex.iCycles ((Functor.mapHomologicalComplex F (ComplexShape.up ℕ)).obj P.cocomplex) 0 =
    F.map (P.ι.f 0)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.InjectiveResolution.toRightDerivedZero'_comp_iCycles` in `Mathlib/CategoryTheory/Abelian/RightDerived.lean`

## Premises used in the next tactic
- `CategoryTheory.InjectiveResolution.toRightDerivedZero'`

## Premise signatures
### `CategoryTheory.InjectiveResolution.toRightDerivedZero'` (commanddeclaration)
```lean
noncomputable def toRightDerivedZero' {X : C}
    (P : InjectiveResolution X) (F : C ⥤ D) [F.Additive] :
    F.obj X ⟶ ((F.mapHomologicalComplex _).obj P.cocomplex).cycles 0
```

## Premise full source (with proof)
### `CategoryTheory.InjectiveResolution.toRightDerivedZero'` (commanddeclaration) at `Mathlib/CategoryTheory/Abelian/RightDerived.lean`
```lean
/-- If `P : InjectiveResolution X` and `F` is an additive functor, this is
the canonical morphism from `F.obj X` to the cycles in degree `0` of
`(F.mapHomologicalComplex _).obj P.cocomplex`. -/
noncomputable def toRightDerivedZero' {X : C}
    (P : InjectiveResolution X) (F : C ⥤ D) [F.Additive] :
    F.obj X ⟶ ((F.mapHomologicalComplex _).obj P.cocomplex).cycles 0 :=
  HomologicalComplex.liftCycles _ (F.map (P.ι.f 0)) 1 (by simp) (by
    dsimp
    rw [← F.map_comp, HomologicalComplex.Hom.comm, HomologicalComplex.single_obj_d,
      zero_comp, F.map_zero])
```

## Transitive premise context (1-hop, 4/4 premises, ≈688 tokens)
### `CategoryTheory.InjectiveResolution` (commanddeclaration) at `Mathlib/CategoryTheory/Preadditive/InjectiveResolution.lean`
```lean
/--
An `InjectiveResolution Z` consists of a bundled `ℕ`-indexed cochain complex of injective objects,
along with a quasi-isomorphism from the complex consisting of just `Z` supported in degree `0`.
-/
-- @[nolint has_nonempty_instance]
structure InjectiveResolution (Z : C) where
  /-- the cochain complex involved in the resolution -/
  cocomplex : CochainComplex C ℕ
  /-- the cochain complex must be degreewise injective -/
  injective : ∀ n, Injective (cocomplex.X n) := by infer_instance
  /-- the cochain complex must have homology -/
  [hasHomology : ∀ i, cocomplex.HasHomology i]
  /-- the morphism from the single cochain complex with `Z` in degree `0` -/
  ι : (single₀ C).obj Z ⟶ cocomplex
  /-- the morphism from the single cochain complex with `Z` in degree `0` is a quasi-isomorphism -/
  quasiIso : QuasiIso ι := by infer_instance
```

### `HomologicalComplex.liftCycles` (commanddeclaration) at `Mathlib/Algebra/Homology/ShortComplex/HomologicalComplex.lean`
```lean
/-- The morphism to `K.cycles i` that is induced by a "cycle", i.e. a morphism
to `K.X i` whose postcomposition with the differential is zero. -/
noncomputable def liftCycles {A : C} (k : A ⟶ K.X i) (j : ι) (hj : c.next i = j)
    (hk : k ≫ K.d i j = 0) : A ⟶ K.cycles i :=
  (K.sc i).liftCycles k (by subst hj; exact hk)

/-- The morphism to `K.cycles i` that is induced by a "cycle", i.e. a morphism
to `K.X i` whose postcomposition with the differential is zero. -/
```

### `HomologicalComplex.Hom.comm` (commanddeclaration) at `Mathlib/Algebra/Homology/HomologicalComplex.lean`
```lean
@[reassoc (attr := simp)]
theorem Hom.comm {A B : HomologicalComplex V c} (f : A.Hom B) (i j : ι) :
    f.f i ≫ B.d i j = A.d i j ≫ f.f j := by
  by_cases hij : c.Rel i j
  · exact f.comm' i j hij
  · rw [A.shape i j hij, B.shape i j hij, comp_zero, zero_comp]
```

### `HomologicalComplex.single_obj_d` (lemma) at `Mathlib/Algebra/Homology/Single.lean`
```lean
@[simp]
lemma single_obj_d (j : ι) (A : V) (k l : ι) :
    ((single V c j).obj A).d k l = 0 := rfl
```
