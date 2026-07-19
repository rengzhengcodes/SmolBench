## Current goal
```
⊢ restrictScalars F (extendScalars hi) = restrictScalars F (adjoin ↥M ↑E')
```

## Full tactic state
```
F : Type u
E : Type v
inst✝⁷ : Field F
inst✝⁶ : Field E
inst✝⁵ : Algebra F E
K : Type w
inst✝⁴ : Field K
inst✝³ : Algebra F K
inst✝² : Algebra E K
inst✝¹ : IsScalarTower F E K
S : Set K
inst✝ : IsPurelyInseparable F E
M : IntermediateField F K := adjoin F S
halg : Algebra.IsAlgebraic F ↥M
L : IntermediateField E K := adjoin E S
E' : IntermediateField F K := AlgHom.fieldRange (IsScalarTower.toAlgHom F E K)
j : E ≃ₐ[F] ↥E' := AlgEquiv.ofInjectiveField (IsScalarTower.toAlgHom F E K)
hi : M ≤ restrictScalars F L
i : ↥M →+* ↥L := Subsemiring.inclusion hi
this✝¹ : Algebra ↥M ↥L := RingHom.toAlgebra i
this✝ : SMul ↥M ↥L := Algebra.toSMul
this : IsScalarTower F ↥M ↥L
q : ℕ
h✝ : ExpChar F q
⊢ restrictScalars F (extendScalars hi) = restrictScalars F (adjoin ↥M ↑E')
```

## Proof so far (23 tactics)
```lean
set M := adjoin F S
set L := adjoin E S
let E' := (IsScalarTower.toAlgHom F E K).fieldRange
let j : E ≃ₐ[F] E' := AlgEquiv.ofInjectiveField (IsScalarTower.toAlgHom F E K)
have hi : M ≤ L.restrictScalars F := by
  rw [restrictScalars_adjoin_of_algEquiv (E := K) j rfl, restrictScalars_adjoin]
  exact adjoin.mono _ _ _ (Set.subset_union_right _ _)
let i : M →+* L := Subsemiring.inclusion hi
letI : Algebra M L := i.toAlgebra
letI : SMul M L := Algebra.toSMul
haveI : IsScalarTower F M L := IsScalarTower.of_algebraMap_eq (congrFun rfl)
haveI : IsPurelyInseparable M L := by
  change IsPurelyInseparable M (extendScalars hi)
  obtain ⟨q, _⟩ := ExpChar.exists F
  have : extendScalars hi = adjoin M (E' : Set K) := restrictScalars_injective F <| by
    conv_lhs => rw [extendScalars_restrictScalars, restrictScalars_adjoin_of_algEquiv
      (E := K) j rfl, ← adjoin_self F E', adjoin_adjoin_comm]
  rw [this, isPurelyInseparable_adjoin_iff_pow_mem _ _ q]
  rintro x ⟨y, hy⟩
  obtain ⟨n, z, hz⟩ := IsPurelyInseparable.pow_mem F q y
  refine ⟨n, algebraMap F M z, ?_⟩
  rw [← IsScalarTower.algebraMap_apply, IsScalarTower.algebraMap_apply F E K, hz, ← hy, map_pow,
    AlgHom.toRingHom_eq_coe, IsScalarTower.coe_toAlgHom]
have h := lift_sepDegree_mul_lift_sepDegree_of_isAlgebraic F E L
  (IsPurelyInseparable.isAlgebraic F E)
rw [IsPurelyInseparable.sepDegree_eq_one F E, Cardinal.lift_one, one_mul] at h
rw [Cardinal.lift_injective h, ← sepDegree_mul_sepDegree_of_isAlgebraic F M L halg,
  IsPurelyInseparable.sepDegree_eq_one M L, mul_one]
rw [restrictScalars_adjoin_of_algEquiv (E := K) j rfl, restrictScalars_adjoin]
exact adjoin.mono _ _ _ (Set.subset_union_right _ _)
change IsPurelyInseparable M (extendScalars hi)
obtain ⟨q, _⟩ := ExpChar.exists F
have : extendScalars hi = adjoin M (E' : Set K) := restrictScalars_injective F <| by
  conv_lhs => rw [extendScalars_restrictScalars, restrictScalars_adjoin_of_algEquiv
    (E := K) j rfl, ← adjoin_self F E', adjoin_adjoin_comm]
rw [this, isPurelyInseparable_adjoin_iff_pow_mem _ _ q]
rintro x ⟨y, hy⟩
obtain ⟨n, z, hz⟩ := IsPurelyInseparable.pow_mem F q y
refine ⟨n, algebraMap F M z, ?_⟩
rw [← IsScalarTower.algebraMap_apply, IsScalarTower.algebraMap_apply F E K, hz, ← hy, map_pow,
  AlgHom.toRingHom_eq_coe, IsScalarTower.coe_toAlgHom]
```

## Theorem
`IntermediateField.sepDegree_adjoin_eq_of_isAlgebraic_of_isPurelyInseparable` in `Mathlib/FieldTheory/PurelyInseparable.lean`

## Premises used in the next tactic
- `IntermediateField.extendScalars_restrictScalars`
- `IntermediateField.restrictScalars_adjoin_of_algEquiv`
- `rfl`
- `IntermediateField.adjoin_self`
- `IntermediateField.adjoin_adjoin_comm`

## Premise signatures
### `IntermediateField.extendScalars_restrictScalars` (commanddeclaration)
```lean
@[simp]
theorem extendScalars_restrictScalars : (extendScalars h).restrictScalars K = E
```

### `IntermediateField.restrictScalars_adjoin_of_algEquiv` (commanddeclaration)
```lean
theorem restrictScalars_adjoin_of_algEquiv
    {L L' : Type*} [Field L] [Field L']
    [Algebra F L] [Algebra L E] [Algebra F L'] [Algebra L' E]
    [IsScalarTower F L E] [IsScalarTower F L' E] (i : L ≃ₐ[F] L')
    (hi : algebraMap L E = (algebraMap L' E) ∘ i) (S : Set E) :
    (adjoin L S).restrictScalars F = (adjoin L' S).restrictScalars F
```

### `rfl` (commanddeclaration)
```lean
@[match_pattern] def rfl {α : Sort u} {a : α} : Eq a a
```

### `IntermediateField.adjoin_self` (commanddeclaration)
```lean
@[simp]
theorem adjoin_self (K : IntermediateField F E) :
    adjoin F K = K
```

### `IntermediateField.adjoin_adjoin_comm` (commanddeclaration)
```lean
theorem adjoin_adjoin_comm (T : Set E) :
    (adjoin (adjoin F S) T).restrictScalars F = (adjoin (adjoin F T) S).restrictScalars F
```

## Premise full source (with proof)
### `IntermediateField.extendScalars_restrictScalars` (commanddeclaration) at `Mathlib/FieldTheory/IntermediateField.lean`
```lean
@[simp]
theorem extendScalars_restrictScalars : (extendScalars h).restrictScalars K = E := rfl
```

### `IntermediateField.restrictScalars_adjoin_of_algEquiv` (commanddeclaration) at `Mathlib/FieldTheory/Adjoin.lean`
```lean
/-- If `E / L / F` and `E / L' / F` are two field extension towers, `L ≃ₐ[F] L'` is an isomorphism
compatible with `E / L` and `E / L'`, then for any subset `S` of `E`, `L(S)` and `L'(S)` are
equal as intermediate fields of `E / F`. -/
theorem restrictScalars_adjoin_of_algEquiv
    {L L' : Type*} [Field L] [Field L']
    [Algebra F L] [Algebra L E] [Algebra F L'] [Algebra L' E]
    [IsScalarTower F L E] [IsScalarTower F L' E] (i : L ≃ₐ[F] L')
    (hi : algebraMap L E = (algebraMap L' E) ∘ i) (S : Set E) :
    (adjoin L S).restrictScalars F = (adjoin L' S).restrictScalars F := by
  apply_fun toSubfield using (fun K K' h ↦ by
    ext x; change x ∈ K.toSubfield ↔ x ∈ K'.toSubfield; rw [h])
  change Subfield.closure _ = Subfield.closure _
  congr
  ext x
  exact ⟨fun ⟨y, h⟩ ↦ ⟨i y, by rw [← h, hi]; rfl⟩,
    fun ⟨y, h⟩ ↦ ⟨i.symm y, by rw [← h, hi, Function.comp_apply, AlgEquiv.apply_symm_apply]⟩⟩
```

### `rfl` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`rfl : a = a` is the unique constructor of the equality type. This is the
same as `Eq.refl` except that it takes `a` implicitly instead of explicitly.

This is a more powerful theorem than it may appear at first, because although
the statement of the theorem is `a = a`, Lean will allow anything that is
definitionally equal to that type. So, for instance, `2 + 2 = 4` is proven in
Lean by `rfl`, because both sides are the same up to definitional equality.
-/
@[match_pattern] def rfl {α : Sort u} {a : α} : Eq a a := Eq.refl a

/-- `id x = x`, as a `@[simp]` lemma. -/
```

### `IntermediateField.adjoin_self` (commanddeclaration) at `Mathlib/FieldTheory/Adjoin.lean`
```lean
@[simp]
theorem adjoin_self (K : IntermediateField F E) :
    adjoin F K = K := le_antisymm (adjoin_le_iff.2 fun _ ↦ id) (subset_adjoin F _)
```

### `IntermediateField.adjoin_adjoin_comm` (commanddeclaration) at `Mathlib/FieldTheory/Adjoin.lean`
```lean
/-- `F[S][T] = F[T][S]` -/
theorem adjoin_adjoin_comm (T : Set E) :
    (adjoin (adjoin F S) T).restrictScalars F = (adjoin (adjoin F T) S).restrictScalars F := by
  rw [adjoin_adjoin_left, adjoin_adjoin_left, Set.union_comm]
```

## Filler (hint:2 → hint:3 token-match, ≈2479 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident
