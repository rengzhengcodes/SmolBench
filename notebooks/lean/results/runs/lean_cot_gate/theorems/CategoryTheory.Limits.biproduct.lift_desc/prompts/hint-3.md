## Current goal
```
⊢ lift g ≫ desc h = ∑ j : J, g j ≫ h j
```

## Full tactic state
```
C : Type u
inst✝³ : Category.{v, u} C
inst✝² : Preadditive C
J : Type
inst✝¹ : Fintype J
f : J → C
inst✝ : HasBiproduct f
T U : C
g : (j : J) → T ⟶ f j
h : (j : J) → f j ⟶ U
⊢ lift g ≫ desc h = ∑ j : J, g j ≫ h j
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.Limits.biproduct.lift_desc` in `Mathlib/CategoryTheory/Preadditive/Biproducts.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.biproduct.lift_eq`
- `CategoryTheory.Limits.biproduct.desc_eq`
- `CategoryTheory.Preadditive.comp_sum`
- `CategoryTheory.Preadditive.sum_comp`
- `CategoryTheory.Limits.biproduct.ι_π_assoc`
- `CategoryTheory.comp_dite`
- `CategoryTheory.dite_comp`

## Premise signatures
### `CategoryTheory.Limits.biproduct.lift_eq` (commanddeclaration)
```lean
theorem biproduct.lift_eq {T : C} {g : ∀ j, T ⟶ f j} :
    biproduct.lift g = ∑ j, g j ≫ biproduct.ι f j
```

### `CategoryTheory.Limits.biproduct.desc_eq` (commanddeclaration)
```lean
theorem biproduct.desc_eq {T : C} {g : ∀ j, f j ⟶ T} :
    biproduct.desc g = ∑ j, biproduct.π f j ≫ g j
```

### `CategoryTheory.Preadditive.comp_sum` (commanddeclaration)
```lean
@[reassoc]
theorem comp_sum {P Q R : C} {J : Type*} (s : Finset J) (f : P ⟶ Q) (g : J → (Q ⟶ R)) :
    (f ≫ ∑ j in s, g j) = ∑ j in s, f ≫ g j
```

### `CategoryTheory.Preadditive.sum_comp` (commanddeclaration)
```lean
@[reassoc]
theorem sum_comp {P Q R : C} {J : Type*} (s : Finset J) (f : J → (P ⟶ Q)) (g : Q ⟶ R) :
    (∑ j in s, f j) ≫ g = ∑ j in s, f j ≫ g
```

### `CategoryTheory.Limits.biproduct.ι_π_assoc`
_(not found in premise corpus)_

### `CategoryTheory.comp_dite` (commanddeclaration)
```lean
theorem comp_dite {P : Prop} [Decidable P]
    {X Y Z : C} (f : X ⟶ Y) (g : P → (Y ⟶ Z)) (g' : ¬P → (Y ⟶ Z)) :
    (f ≫ if h : P then g h else g' h) = if h : P then f ≫ g h else f ≫ g' h
```

### `CategoryTheory.dite_comp` (commanddeclaration)
```lean
theorem dite_comp {P : Prop} [Decidable P]
    {X Y Z : C} (f : P → (X ⟶ Y)) (f' : ¬P → (X ⟶ Y)) (g : Y ⟶ Z) :
    (if h : P then f h else f' h) ≫ g = if h : P then f h ≫ g else f' h ≫ g
```

## Premise full source (with proof)
### `CategoryTheory.Limits.biproduct.lift_eq` (commanddeclaration) at `Mathlib/CategoryTheory/Preadditive/Biproducts.lean`
```lean
theorem biproduct.lift_eq {T : C} {g : ∀ j, T ⟶ f j} :
    biproduct.lift g = ∑ j, g j ≫ biproduct.ι f j := by
  ext j
  simp only [sum_comp, biproduct.ι_π, comp_dite, biproduct.lift_π, Category.assoc, comp_zero,
    Finset.sum_dite_eq', Finset.mem_univ, eqToHom_refl, Category.comp_id, if_true]
```

### `CategoryTheory.Limits.biproduct.desc_eq` (commanddeclaration) at `Mathlib/CategoryTheory/Preadditive/Biproducts.lean`
```lean
theorem biproduct.desc_eq {T : C} {g : ∀ j, f j ⟶ T} :
    biproduct.desc g = ∑ j, biproduct.π f j ≫ g j := by
  ext j
  simp [comp_sum, biproduct.ι_π_assoc, dite_comp]
```

### `CategoryTheory.Preadditive.comp_sum` (commanddeclaration) at `Mathlib/CategoryTheory/Preadditive/Basic.lean`
```lean
@[reassoc]
theorem comp_sum {P Q R : C} {J : Type*} (s : Finset J) (f : P ⟶ Q) (g : J → (Q ⟶ R)) :
    (f ≫ ∑ j in s, g j) = ∑ j in s, f ≫ g j :=
  map_sum (leftComp R f) _ _
```

### `CategoryTheory.Preadditive.sum_comp` (commanddeclaration) at `Mathlib/CategoryTheory/Preadditive/Basic.lean`
```lean
@[reassoc]
theorem sum_comp {P Q R : C} {J : Type*} (s : Finset J) (f : J → (P ⟶ Q)) (g : Q ⟶ R) :
    (∑ j in s, f j) ≫ g = ∑ j in s, f j ≫ g :=
  map_sum (rightComp P g) _ _
```

### `CategoryTheory.Limits.biproduct.ι_π_assoc`
_(not found in premise corpus)_

### `CategoryTheory.comp_dite` (commanddeclaration) at `Mathlib/CategoryTheory/Category/Basic.lean`
```lean
theorem comp_dite {P : Prop} [Decidable P]
    {X Y Z : C} (f : X ⟶ Y) (g : P → (Y ⟶ Z)) (g' : ¬P → (Y ⟶ Z)) :
    (f ≫ if h : P then g h else g' h) = if h : P then f ≫ g h else f ≫ g' h := by aesop
```

### `CategoryTheory.dite_comp` (commanddeclaration) at `Mathlib/CategoryTheory/Category/Basic.lean`
```lean
theorem dite_comp {P : Prop} [Decidable P]
    {X Y Z : C} (f : P → (X ⟶ Y)) (f' : ¬P → (X ⟶ Y)) (g : Y ⟶ Z) :
    (if h : P then f h else f' h) ≫ g = if h : P then f h ≫ g else f' h ≫ g := by aesop
```

## Transitive premise context (1-hop, 5/5 premises, ≈715 tokens)
### `Finset.mem_univ` (commanddeclaration) at `Mathlib/Data/Fintype/Basic.lean`
```lean
@[simp]
theorem mem_univ (x : α) : x ∈ (univ : Finset α) :=
  Fintype.complete x
```

### `CategoryTheory.eqToHom_refl` (commanddeclaration) at `Mathlib/CategoryTheory/EqToHom.lean`
```lean
@[simp]
theorem eqToHom_refl (X : C) (p : X = X) : eqToHom p = 𝟙 X :=
  rfl
```

### `if_true` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/ByCases.lean`
```lean
@[simp] theorem if_true {h : Decidable True} (t e : α) : ite True t e = t := if_pos trivial
```

### `Finset` (commanddeclaration) at `Mathlib/Data/Finset/Basic.lean`
```lean
/-- `Finset α` is the type of finite sets of elements of `α`. It is implemented
  as a multiset (a list up to permutation) which has no duplicate elements. -/
structure Finset (α : Type*) where
  /-- The underlying multiset -/
  val : Multiset α
  /-- `val` contains no duplicates -/
  nodup : Nodup val
```

### `Decidable` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`Decidable p` is a data-carrying class that supplies a proof that `p` is
either `true` or `false`. It is equivalent to `Bool` (and in fact it has the
same code generation as `Bool`) together with a proof that the `Bool` is
true iff `p` is.

`Decidable` instances are used to infer "computation strategies" for
propositions, so that you can have the convenience of writing propositions
inside `if` statements and executing them (which actually executes the inferred
decidability instance instead of the proposition, which has no code).

If a proposition `p` is `Decidable`, then `(by decide : p)` will prove it by
evaluating the decidability instance to `isTrue h` and returning `h`.

Because `Decidable` carries data,
when writing `@[simp]` lemmas which include a `Decidable` instance on the LHS,
it is best to use `{_ : Decidable p}` rather than `[Decidable p]`
so that non-canonical instances can be found via unification rather than
typeclass search.
-/
class inductive Decidable (p : Prop) where
  /-- Prove that `p` is decidable by supplying a proof of `¬p` -/
  | isFalse (h : Not p) : Decidable p
  /-- Prove that `p` is decidable by supplying a proof of `p` -/
  | isTrue (h : p) : Decidable p

/--
Convert a decidable proposition into a boolean value.

If `p : Prop` is decidable, then `decide p : Bool` is the boolean value
which is `true` if `p` is true and `false` if `p` is false.
-/
```
