## Current goal
```
⊢ (i + m) % n = (i + k) % n
```

## Full tactic state
```
m n k i : Int
H : m % n = k % n
⊢ (i + m) % n = (i + k) % n
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Int.add_emod_eq_add_emod_left` in `.lake/packages/std/Std/Data/Int/DivMod.lean`

## Premises used in the next tactic
- `Int.add_comm`
- `Int.add_emod_eq_add_emod_right`
- `Int.add_comm`

## Premise signatures
### `Int.add_comm` (commanddeclaration)
```lean
protected theorem add_comm : ∀ a b : Int, a + b = b + a
```

### `Int.add_emod_eq_add_emod_right` (commanddeclaration)
```lean
theorem add_emod_eq_add_emod_right {m n k : Int} (i : Int)
    (H : m % n = k % n) : (m + i) % n = (k + i) % n
```

### `Int.add_comm` (commanddeclaration)
```lean
protected theorem add_comm : ∀ a b : Int, a + b = b + a
```

## Premise full source (with proof)
### `Int.add_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Lemmas.lean`
```lean
protected theorem add_comm : ∀ a b : Int, a + b = b + a
  | ofNat n, ofNat m => by simp [Nat.add_comm]
  | ofNat _, -[_+1]  => rfl
  | -[_+1],  ofNat _ => rfl
  | -[_+1],  -[_+1]  => by simp [Nat.add_comm]
```

### `Int.add_emod_eq_add_emod_right` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/DivModLemmas.lean`
```lean
theorem add_emod_eq_add_emod_right {m n k : Int} (i : Int)
    (H : m % n = k % n) : (m + i) % n = (k + i) % n := by
  rw [← emod_add_emod, ← emod_add_emod k, H]
```

### `Int.add_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Lemmas.lean`
```lean
protected theorem add_comm : ∀ a b : Int, a + b = b + a
  | ofNat n, ofNat m => by simp [Nat.add_comm]
  | ofNat _, -[_+1]  => rfl
  | -[_+1],  ofNat _ => rfl
  | -[_+1],  -[_+1]  => by simp [Nat.add_comm]
```

## Filler (hint:2 → hint:3 token-match, ≈542 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu
