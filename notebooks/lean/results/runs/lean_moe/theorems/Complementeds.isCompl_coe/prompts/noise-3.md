## Current goal
```
⊢ IsCompl ↑a ↑b ↔ IsCompl a b
```

## Full tactic state
```
α : Type u_1
inst✝¹ : DistribLattice α
inst✝ : BoundedOrder α
a b : Complementeds α
⊢ IsCompl ↑a ↑b ↔ IsCompl a b
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Complementeds.isCompl_coe` in `Mathlib/Order/Disjoint.lean`

## Premises used in the next tactic
- `isCompl_iff`
- `Complementeds.disjoint_coe`
- `Complementeds.codisjoint_coe`

## Premise signatures
### `isCompl_iff` (commanddeclaration)
```lean
theorem isCompl_iff [PartialOrder α] [BoundedOrder α] {a b : α} :
    IsCompl a b ↔ Disjoint a b ∧ Codisjoint a b
```

### `Complementeds.disjoint_coe` (commanddeclaration)
```lean
@[simp, norm_cast]
theorem disjoint_coe : Disjoint (a : α) b ↔ Disjoint a b
```

### `Complementeds.codisjoint_coe` (commanddeclaration)
```lean
@[simp, norm_cast]
theorem codisjoint_coe : Codisjoint (a : α) b ↔ Codisjoint a b
```

## Premise full source (with proof)
### `isCompl_iff` (commanddeclaration) at `Mathlib/Order/Disjoint.lean`
```lean
theorem isCompl_iff [PartialOrder α] [BoundedOrder α] {a b : α} :
    IsCompl a b ↔ Disjoint a b ∧ Codisjoint a b :=
  ⟨fun h ↦ ⟨h.1, h.2⟩, fun h ↦ ⟨h.1, h.2⟩⟩
```

### `Complementeds.disjoint_coe` (commanddeclaration) at `Mathlib/Order/Disjoint.lean`
```lean
@[simp, norm_cast]
theorem disjoint_coe : Disjoint (a : α) b ↔ Disjoint a b := by
  rw [disjoint_iff, disjoint_iff, ← coe_inf, ← coe_bot, coe_inj]
```

### `Complementeds.codisjoint_coe` (commanddeclaration) at `Mathlib/Order/Disjoint.lean`
```lean
@[simp, norm_cast]
theorem codisjoint_coe : Codisjoint (a : α) b ↔ Codisjoint a b := by
  rw [codisjoint_iff, codisjoint_iff, ← coe_sup, ← coe_top, coe_inj]
```

## Filler (hint:2 → hint:3 token-match, ≈737 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
