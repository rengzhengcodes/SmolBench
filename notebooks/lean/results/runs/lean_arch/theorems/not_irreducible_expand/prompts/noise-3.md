## Current goal
```
⊢ ¬Irreducible (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f ^ p)
```

## Full tactic state
```
R✝ : Type u_1
p✝ m n : ℕ
inst✝⁶ : CommSemiring R✝
inst✝⁵ : ExpChar R✝ p✝
inst✝⁴ : PerfectRing R✝ p✝
R : Type u_2
p : ℕ
inst✝³ : CommSemiring R
inst✝² : Fact (Nat.Prime p)
inst✝¹ : CharP R p
inst✝ : PerfectRing R p
f : R[X]
⊢ ¬Irreducible (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f ^ p)
```

## Proof so far (1 tactic)
```lean
rw [polynomial_expand_eq]
```

## Theorem
`not_irreducible_expand` in `Mathlib/FieldTheory/Perfect.lean`

## Premises used in the next tactic
- `not_irreducible_pow`
- `Fact.out`
- `Nat.Prime.ne_one`

## Premise signatures
### `not_irreducible_pow` (commanddeclaration)
```lean
theorem not_irreducible_pow {α} [Monoid α] {x : α} {n : ℕ} (hn : n ≠ 1) :
    ¬ Irreducible (x ^ n)
```

### `Fact.out`
_(not found in premise corpus)_

### `Nat.Prime.ne_one` (commanddeclaration)
```lean
theorem Prime.ne_one {p : ℕ} (hp : p.Prime) : p ≠ 1
```

## Premise full source (with proof)
### `not_irreducible_pow` (commanddeclaration) at `Mathlib/Algebra/Associated.lean`
```lean
theorem not_irreducible_pow {α} [Monoid α] {x : α} {n : ℕ} (hn : n ≠ 1) :
    ¬ Irreducible (x ^ n) := by
  cases n with
  | zero => simp
  | succ n =>
    intro ⟨h₁, h₂⟩
    have := h₂ _ _ (pow_succ _ _)
    rw [isUnit_pow_iff (Nat.succ_ne_succ.mp hn), or_self] at this
    exact h₁ (this.pow _)
```

### `Fact.out`
_(not found in premise corpus)_

### `Nat.Prime.ne_one` (commanddeclaration) at `Mathlib/Data/Nat/Prime.lean`
```lean
theorem Prime.ne_one {p : ℕ} (hp : p.Prime) : p ≠ 1 :=
  hp.one_lt.ne'
```

## Filler (hint:2 → hint:3 token-match, ≈701 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
