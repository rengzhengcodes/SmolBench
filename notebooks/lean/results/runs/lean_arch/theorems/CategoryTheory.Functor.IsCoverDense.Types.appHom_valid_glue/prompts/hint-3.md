## Current goal
```
⊢ (appHom α X ≫ ℱ'.val.map f) a✝ = (ℱ.map f ≫ α.app (op Y)) a✝
```

## Full tactic state
```
case h
C : Type u_1
inst✝⁵ : Category.{u_6, u_1} C
D : Type u_2
inst✝⁴ : Category.{u_5, u_2} D
E : Type u_3
inst✝³ : Category.{?u.46606, u_3} E
J : GrothendieckTopology C
K : GrothendieckTopology D
L : GrothendieckTopology E
A : Type u_4
inst✝² : Category.{?u.46658, u_4} A
G : C ⥤ D
inst✝¹ : IsCoverDense G K
inst✝ : Full G
ℱ : Dᵒᵖ ⥤ Type v
ℱ' : SheafOfTypes K
α : G.op ⋙ ℱ ⟶ G.op ⋙ ℱ'.val
X : D
Y : C
f : op X ⟶ op (G.obj Y)
a✝ : ℱ.obj (op X)
⊢ (appHom α X ≫ ℱ'.val.map f) a✝ = (ℱ.map f ≫ α.app (op Y)) a✝
```

## Proof so far (1 tactic)
```lean
ext
```

## Theorem
`CategoryTheory.Functor.IsCoverDense.Types.appHom_valid_glue` in `Mathlib/CategoryTheory/Sites/DenseSubsite.lean`

## Premises used in the next tactic
- `CategoryTheory.Functor.IsCoverDense.Types.appHom_restrict`

## Premise signatures
### `CategoryTheory.Functor.IsCoverDense.Types.appHom_restrict` (commanddeclaration)
```lean
@[simp]
theorem appHom_restrict {X : D} {Y : C} (f : op X ⟶ op (G.obj Y)) (x) :
    ℱ'.val.map f (appHom α X x) = α.app (op Y) (ℱ.map f x)
```

## Premise full source (with proof)
### `CategoryTheory.Functor.IsCoverDense.Types.appHom_restrict` (commanddeclaration) at `Mathlib/CategoryTheory/Sites/DenseSubsite.lean`
```lean
@[simp]
theorem appHom_restrict {X : D} {Y : C} (f : op X ⟶ op (G.obj Y)) (x) :
    ℱ'.val.map f (appHom α X x) = α.app (op Y) (ℱ.map f x) :=
  ((ℱ'.cond _ (G.is_cover_of_isCoverDense _ X)).valid_glue
      (pushforwardFamily_compatible α x) f.unop
          (Presieve.in_coverByImage G f.unop)).trans (pushforwardFamily_apply _ _ _)
```

## Transitive premise context (1-hop, 5/5 premises, ≈1217 tokens)
### `cond` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`cond b x y` is the same as `if b then x else y`, but optimized for a
boolean condition. It can also be written as `bif b then x else y`.
This is `@[macro_inline]` because `x` and `y` should not
be eagerly evaluated (see `ite`).
-/
@[macro_inline] def cond {α : Type u} (c : Bool) (x y : α) : α :=
  match c with
  | true  => x
  | false => y

/--
`or x y`, or `x || y`, is the boolean "or" operation (not to be confused
with `Or : Prop → Prop → Prop`, which is the propositional connective).
It is `@[macro_inline]` because it has C-like short-circuiting behavior:
if `x` is true then `y` is not evaluated.
-/
```

### `CategoryTheory.Presieve.IsSheafFor.valid_glue` (commanddeclaration) at `Mathlib/CategoryTheory/Sites/IsSheafFor.lean`
```lean
@[simp]
theorem IsSheafFor.valid_glue (t : IsSheafFor P R) {x : FamilyOfElements P R} (hx : x.Compatible)
    (f : Y ⟶ X) (Hf : R f) : P.map f.op (t.amalgamate x hx) = x f Hf :=
  t.isAmalgamation hx f Hf
```

### `CategoryTheory.Functor.IsCoverDense.Types.pushforwardFamily_compatible` (commanddeclaration) at `Mathlib/CategoryTheory/Sites/DenseSubsite.lean`
```lean
/-- (Implementation). The `pushforwardFamily` defined is compatible. -/
theorem pushforwardFamily_compatible {X} (x : ℱ.obj (op X)) :
    (pushforwardFamily α x).Compatible := by
  intro Y₁ Y₂ Z g₁ g₂ f₁ f₂ h₁ h₂ e
  apply IsCoverDense.ext G
  intro Y f
  simp only [pushforwardFamily, ← FunctorToTypes.map_comp_apply, ← op_comp]
  change (ℱ.map _ ≫ α.app (op _) ≫ ℱ'.val.map _) _ = (ℱ.map _ ≫ α.app (op _) ≫ ℱ'.val.map _) _
  rw [← G.image_preimage (f ≫ g₁ ≫ _)]
  rw [← G.image_preimage (f ≫ g₂ ≫ _)]
  erw [← α.naturality (G.preimage _).op]
  erw [← α.naturality (G.preimage _).op]
  refine' congr_fun _ x
  -- Porting note: these next 3 tactics (simp, rw, simp) were just one big `simp only` in Lean 3
  -- but I can't get `simp` to do the `rw` line.
  simp only [Functor.comp_map, ← Category.assoc, Functor.op_map, Quiver.Hom.unop_op]
  rw [← ℱ.map_comp, ← ℱ.map_comp] -- `simp only [← ℱ.map_comp]` does nothing, even if I add
  -- the relevant explicit inputs
  simp only [← op_comp, G.image_preimage]
  congr 3
  simp [e]
```

### `trans` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem trans [IsTrans α r] {a b c : α} : a ≺ b → b ≺ c → a ≺ c :=
  IsTrans.trans _ _ _
```

### `CategoryTheory.Functor.IsCoverDense.Types.pushforwardFamily_apply` (commanddeclaration) at `Mathlib/CategoryTheory/Sites/DenseSubsite.lean`
```lean
@[simp]
theorem pushforwardFamily_apply {X} (x : ℱ.obj (op X)) {Y : C} (f : G.obj Y ⟶ X) :
    pushforwardFamily α x f (Presieve.in_coverByImage G f) = α.app (op Y) (ℱ.map f.op x) := by
  unfold pushforwardFamily
  -- Porting note: congr_fun was more powerful in Lean 3; I had to explicitly supply
  -- the type of the first input here even though it's obvious (there is a unique occurrence
  -- of x on each side of the equality)
  refine' congr_fun (_ :
    (fun t => ℱ'.val.map ((Nonempty.some (_ : coverByImage G X f)).lift.op)
      (α.app (op (Nonempty.some (_ : coverByImage G X f)).1)
        (ℱ.map ((Nonempty.some (_ : coverByImage G X f)).map.op) t))) =
    (fun t => α.app (op Y) (ℱ.map (f.op) t))) x
  rw [← G.image_preimage (Nonempty.some _ : Presieve.CoverByImageStructure _ _).lift]
  change ℱ.map _ ≫ α.app (op _) ≫ ℱ'.val.map _ = ℱ.map f.op ≫ α.app (op Y)
  erw [← α.naturality (G.preimage _).op]
  simp only [← Functor.map_comp, ← Category.assoc, Functor.comp_map, G.image_preimage, G.op_map,
    Quiver.Hom.unop_op, ← op_comp, Presieve.CoverByImageStructure.fac]
```
