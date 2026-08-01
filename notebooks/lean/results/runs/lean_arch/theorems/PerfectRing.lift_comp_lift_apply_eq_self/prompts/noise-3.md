## Current goal
```
⊢ (lift j i p) ((lift i j p) x) = x
```

## Full tactic state
```
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹² : CommRing K
inst✝¹¹ : CommRing L
inst✝¹⁰ : CommRing M
inst✝⁹ : CommRing N
i : K →+* L
j : K →+* M
k : K →+* N
f : L →+* M
g : L →+* N
p : ℕ
inst✝⁸ : ExpChar K p
inst✝⁷ : ExpChar L p
inst✝⁶ : ExpChar M p
inst✝⁵ : ExpChar N p
inst✝⁴ : PerfectRing M p
inst✝³ : IsPRadical i p
inst✝² : PerfectRing N p
inst✝¹ : IsPRadical j p
inst✝ : PerfectRing L p
x : L
⊢ (lift j i p) ((lift i j p) x) = x
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`PerfectRing.lift_comp_lift_apply_eq_self` in `Mathlib/FieldTheory/IsPerfectClosure.lean`

## Premises used in the next tactic
- `PerfectRing.lift_comp_lift_apply`
- `PerfectRing.lift_self_apply`

## Premise signatures
### `PerfectRing.lift_comp_lift_apply` (commanddeclaration)
```lean
@[simp]
theorem lift_comp_lift_apply (x : L) : lift j k p (lift i j p x) = lift i k p x
```

### `PerfectRing.lift_self_apply` (commanddeclaration)
```lean
theorem lift_self_apply [PerfectRing L p] (x : L) : lift i i p x = x
```

## Premise full source (with proof)
### `PerfectRing.lift_comp_lift_apply` (commanddeclaration) at `Mathlib/FieldTheory/IsPerfectClosure.lean`
```lean
@[simp]
theorem lift_comp_lift_apply (x : L) : lift j k p (lift i j p x) = lift i k p x :=
  congr($(lift_comp_lift i j k p) x)
```

### `PerfectRing.lift_self_apply` (commanddeclaration) at `Mathlib/FieldTheory/IsPerfectClosure.lean`
```lean
theorem lift_self_apply [PerfectRing L p] (x : L) : lift i i p x = x := liftAux_self_apply i p x
```

## Filler (hint:2 → hint:3 token-match, ≈490 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit,
