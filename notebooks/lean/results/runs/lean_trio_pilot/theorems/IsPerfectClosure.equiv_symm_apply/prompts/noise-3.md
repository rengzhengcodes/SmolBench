## Current goal
```
⊢ (RingEquiv.symm (equiv i j p)) x = (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y)
```

## Full tactic state
```
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹¹ : CommRing K
inst✝¹⁰ : CommRing L
inst✝⁹ : CommRing M
inst✝⁸ : CommRing N
i : K →+* L
j : K →+* M
k : K →+* N
f : L →+* M
g : L →+* N
p : ℕ
inst✝⁷ : ExpChar K p
inst✝⁶ : ExpChar L p
inst✝⁵ : ExpChar M p
inst✝⁴ : ExpChar N p
inst✝³ : PerfectRing L p
inst✝² : IsPerfectClosure i p
inst✝¹ : PerfectRing M p
inst✝ : IsPerfectClosure j p
x : M
n : ℕ
y : K
h : j y = x ^ p ^ n
⊢ (RingEquiv.symm (equiv i j p)) x = (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`IsPerfectClosure.equiv_symm_apply` in `Mathlib/FieldTheory/IsPerfectClosure.lean`

## Premises used in the next tactic
- `IsPerfectClosure.equiv_symm`
- `IsPerfectClosure.equiv_apply`

## Premise signatures
### `IsPerfectClosure.equiv_symm` (commanddeclaration)
```lean
@[simp]
theorem equiv_symm : (equiv i j p).symm = equiv j i p
```

### `IsPerfectClosure.equiv_apply` (commanddeclaration)
```lean
theorem equiv_apply (x : L) (n : ℕ) (y : K) (h : i y = x ^ p ^ n) :
    equiv i j p x = (iterateFrobeniusEquiv M p n).symm (j y)
```

## Premise full source (with proof)
### `IsPerfectClosure.equiv_symm` (commanddeclaration) at `Mathlib/FieldTheory/IsPerfectClosure.lean`
```lean
@[simp]
theorem equiv_symm : (equiv i j p).symm = equiv j i p := rfl
```

### `IsPerfectClosure.equiv_apply` (commanddeclaration) at `Mathlib/FieldTheory/IsPerfectClosure.lean`
```lean
theorem equiv_apply (x : L) (n : ℕ) (y : K) (h : i y = x ^ p ^ n) :
    equiv i j p x = (iterateFrobeniusEquiv M p n).symm (j y) :=
  PerfectRing.liftAux_apply i j p _ _ _ h
```

## Filler (hint:2 → hint:3 token-match, ≈716 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat
