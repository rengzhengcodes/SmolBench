## Current goal
```
⊢ 0 - 0 - (-b - a) = b + a
```

## Full tactic state
```
C : Type u
inst✝¹ : Category.{v, u} C
inst✝ : NonPreadditiveAbelian C
X Y : C
a b : X ⟶ Y
⊢ 0 - 0 - (-b - a) = b + a
```

## Proof so far (4 tactics)
```lean
rw [add_def]
conv_lhs => rw [← neg_neg a]
rw [neg_def, neg_def, neg_def, sub_sub_sub]
conv_lhs =>
  congr
  next => skip
  rw [← neg_def, neg_sub]
```

## Theorem
`CategoryTheory.NonPreadditiveAbelian.add_comm` in `Mathlib/CategoryTheory/Abelian/NonPreadditive.lean`

## Premises used in the next tactic
- `CategoryTheory.NonPreadditiveAbelian.sub_sub_sub`
- `CategoryTheory.NonPreadditiveAbelian.add_def`
- `CategoryTheory.NonPreadditiveAbelian.neg_def`
- `CategoryTheory.NonPreadditiveAbelian.neg_neg`
- `CategoryTheory.NonPreadditiveAbelian.neg_def`

## Premise signatures
### `CategoryTheory.NonPreadditiveAbelian.sub_sub_sub` (commanddeclaration)
```lean
theorem sub_sub_sub {X Y : C} (a b c d : X ⟶ Y) : a - c - (b - d) = a - b - (c - d)
```

### `CategoryTheory.NonPreadditiveAbelian.add_def` (commanddeclaration)
```lean
theorem add_def {X Y : C} (a b : X ⟶ Y) : a + b = a - -b
```

### `CategoryTheory.NonPreadditiveAbelian.neg_def` (commanddeclaration)
```lean
theorem neg_def {X Y : C} (a : X ⟶ Y) : -a = 0 - a
```

### `CategoryTheory.NonPreadditiveAbelian.neg_neg` (commanddeclaration)
```lean
theorem neg_neg {X Y : C} (a : X ⟶ Y) : - -a = a
```

### `CategoryTheory.NonPreadditiveAbelian.neg_def` (commanddeclaration)
```lean
theorem neg_def {X Y : C} (a : X ⟶ Y) : -a = 0 - a
```

## Premise full source (with proof)
### `CategoryTheory.NonPreadditiveAbelian.sub_sub_sub` (commanddeclaration) at `Mathlib/CategoryTheory/Abelian/NonPreadditive.lean`
```lean
theorem sub_sub_sub {X Y : C} (a b c d : X ⟶ Y) : a - c - (b - d) = a - b - (c - d) := by
  rw [sub_def, ← lift_sub_lift, sub_def, Category.assoc, σ_comp, prod.lift_map_assoc]; rfl
```

### `CategoryTheory.NonPreadditiveAbelian.add_def` (commanddeclaration) at `Mathlib/CategoryTheory/Abelian/NonPreadditive.lean`
```lean
theorem add_def {X Y : C} (a b : X ⟶ Y) : a + b = a - -b := rfl
```

### `CategoryTheory.NonPreadditiveAbelian.neg_def` (commanddeclaration) at `Mathlib/CategoryTheory/Abelian/NonPreadditive.lean`
```lean
theorem neg_def {X Y : C} (a : X ⟶ Y) : -a = 0 - a := rfl
```

### `CategoryTheory.NonPreadditiveAbelian.neg_neg` (commanddeclaration) at `Mathlib/CategoryTheory/Abelian/NonPreadditive.lean`
```lean
theorem neg_neg {X Y : C} (a : X ⟶ Y) : - -a = a := by
  rw [neg_def, neg_def]
  conv_lhs =>
    congr; rw [← sub_self a]
  rw [sub_sub_sub, sub_zero, sub_self, sub_zero]
```

### `CategoryTheory.NonPreadditiveAbelian.neg_def` (commanddeclaration) at `Mathlib/CategoryTheory/Abelian/NonPreadditive.lean`
```lean
theorem neg_def {X Y : C} (a : X ⟶ Y) : -a = 0 - a := rfl
```

## Transitive premise context (1-hop, 5/5 premises, ≈1795 tokens)
### `sub_def` (lemma) at `Mathlib/Data/UInt.lean`
```lean
      lemma sub_def (a b : $typeName) : a - b = ⟨a.val - b.val⟩ := rfl

      lemma mul_def (a b : $typeName) : a * b = ⟨a.val * b.val⟩ := rfl

      lemma mod_def (a b : $typeName) : a % b = ⟨a.val % b.val⟩ := rfl

      lemma add_def (a b : $typeName) : a + b = ⟨a.val + b.val⟩ := rfl

      lemma pow_def (a : $typeName) (n : ℕ) : a ^ n = ⟨a.val ^ n⟩ := rfl

      lemma nsmul_def (n : ℕ) (a : $typeName) : n • a = ⟨n • a.val⟩ := rfl

      lemma zsmul_def (z : ℤ) (a : $typeName) : z • a = ⟨z • a.val⟩ := rfl

      lemma natCast_def (n : ℕ) : (n : $typeName) = ⟨n⟩ := rfl

      lemma intCast_def (z : ℤ) : (z : $typeName) = ⟨z⟩ := rfl

      lemma eq_of_val_eq : ∀ {a b : $typeName}, a.val = b.val -> a = b
      | ⟨_⟩, ⟨_⟩, h => congrArg mk h

      lemma val_injective : Function.Injective val := @eq_of_val_eq

      lemma val_eq_of_eq : ∀ {a b : $typeName}, a = b -> a.val = b.val
      | ⟨_⟩, ⟨_⟩, h => congrArg val h

      @[simp] lemma mk_val_eq : ∀ (a : $typeName), mk a.val = a
      | ⟨_, _⟩ => rfl

      instance : CommRing $typeName :=
        Function.Injective.commRing val val_injective
          rfl rfl (fun _ _ => rfl) (fun _ _ => rfl) (fun _ => rfl) (fun _ _ => rfl)
          (fun _ _ => rfl) (fun _ _ => rfl) (fun _ _ => rfl) (fun _ => rfl) (fun _ => rfl)

    end $typeName
  ))
```

### `CategoryTheory.NonPreadditiveAbelian.lift_sub_lift` (commanddeclaration) at `Mathlib/CategoryTheory/Abelian/NonPreadditive.lean`
```lean
theorem lift_sub_lift {X Y : C} (a b c d : X ⟶ Y) :
    prod.lift a b - prod.lift c d = prod.lift (a - c) (b - d) := by
  simp only [sub_def]
  ext
  · rw [Category.assoc, σ_comp, prod.lift_map_assoc, prod.lift_fst, prod.lift_fst, prod.lift_fst]
  · rw [Category.assoc, σ_comp, prod.lift_map_assoc, prod.lift_snd, prod.lift_snd, prod.lift_snd]
```

### `add_def` (lemma) at `Mathlib/Data/UInt.lean`
```lean
      lemma add_def (a b : $typeName) : a + b = ⟨a.val + b.val⟩ := rfl

      lemma pow_def (a : $typeName) (n : ℕ) : a ^ n = ⟨a.val ^ n⟩ := rfl

      lemma nsmul_def (n : ℕ) (a : $typeName) : n • a = ⟨n • a.val⟩ := rfl

      lemma zsmul_def (z : ℤ) (a : $typeName) : z • a = ⟨z • a.val⟩ := rfl

      lemma natCast_def (n : ℕ) : (n : $typeName) = ⟨n⟩ := rfl

      lemma intCast_def (z : ℤ) : (z : $typeName) = ⟨z⟩ := rfl

      lemma eq_of_val_eq : ∀ {a b : $typeName}, a.val = b.val -> a = b
      | ⟨_⟩, ⟨_⟩, h => congrArg mk h

      lemma val_injective : Function.Injective val := @eq_of_val_eq

      lemma val_eq_of_eq : ∀ {a b : $typeName}, a = b -> a.val = b.val
      | ⟨_⟩, ⟨_⟩, h => congrArg val h

      @[simp] lemma mk_val_eq : ∀ (a : $typeName), mk a.val = a
      | ⟨_, _⟩ => rfl

      instance : CommRing $typeName :=
        Function.Injective.commRing val val_injective
          rfl rfl (fun _ _ => rfl) (fun _ _ => rfl) (fun _ => rfl) (fun _ _ => rfl)
          (fun _ _ => rfl) (fun _ _ => rfl) (fun _ _ => rfl) (fun _ => rfl) (fun _ => rfl)

    end $typeName
  ))
```

### `neg_def` (lemma) at `Mathlib/Data/UInt.lean`
```lean
      lemma neg_def (a : $typeName) : -a = ⟨-a.val⟩ := rfl

      lemma sub_def (a b : $typeName) : a - b = ⟨a.val - b.val⟩ := rfl

      lemma mul_def (a b : $typeName) : a * b = ⟨a.val * b.val⟩ := rfl

      lemma mod_def (a b : $typeName) : a % b = ⟨a.val % b.val⟩ := rfl

      lemma add_def (a b : $typeName) : a + b = ⟨a.val + b.val⟩ := rfl

      lemma pow_def (a : $typeName) (n : ℕ) : a ^ n = ⟨a.val ^ n⟩ := rfl

      lemma nsmul_def (n : ℕ) (a : $typeName) : n • a = ⟨n • a.val⟩ := rfl

      lemma zsmul_def (z : ℤ) (a : $typeName) : z • a = ⟨z • a.val⟩ := rfl

      lemma natCast_def (n : ℕ) : (n : $typeName) = ⟨n⟩ := rfl

      lemma intCast_def (z : ℤ) : (z : $typeName) = ⟨z⟩ := rfl

      lemma eq_of_val_eq : ∀ {a b : $typeName}, a.val = b.val -> a = b
      | ⟨_⟩, ⟨_⟩, h => congrArg mk h

      lemma val_injective : Function.Injective val := @eq_of_val_eq

      lemma val_eq_of_eq : ∀ {a b : $typeName}, a = b -> a.val = b.val
      | ⟨_⟩, ⟨_⟩, h => congrArg val h

      @[simp] lemma mk_val_eq : ∀ (a : $typeName), mk a.val = a
      | ⟨_, _⟩ => rfl

      instance : CommRing $typeName :=
        Function.Injective.commRing val val_injective
          rfl rfl (fun _ _ => rfl) (fun _ _ => rfl) (fun _ => rfl) (fun _ _ => rfl)
          (fun _ _ => rfl) (fun _ _ => rfl) (fun _ _ => rfl) (fun _ => rfl) (fun _ => rfl)

    end $typeName
  ))
```

### `congr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Congruence in both function and argument. If `f₁ = f₂` and `a₁ = a₂` then
`f₁ a₁ = f₂ a₂`. This only works for nondependent functions; the theorem
statement is more complex in the dependent case.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
theorem congr {α : Sort u} {β : Sort v} {f₁ f₂ : α → β} {a₁ a₂ : α} (h₁ : Eq f₁ f₂) (h₂ : Eq a₁ a₂) : Eq (f₁ a₁) (f₂ a₂) :=
  h₁ ▸ h₂ ▸ rfl

/-- Congruence in the function part of an application: If `f = g` then `f a = g a`. -/
```
