## Current goal
```
⊢ sInf {a | ∀ x ∈ s, x ≤ a} = sSup s
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Type u_4
ι' : Type u_5
inst✝ : ConditionallyCompleteLattice α
s : Set α
h : BddAbove s
hs : Set.Nonempty s
⊢ sInf {a | ∀ x ∈ s, x ≤ a} = sSup s
```

## Proof so far (1 tactic)
```lean
simp only [limsSup, eventually_principal]
```

## Theorem
`Filter.limsSup_principal` in `Mathlib/Order/LiminfLimsup.lean`

## Premises used in the next tactic
- `csInf_upper_bounds_eq_csSup`

## Premise signatures
### `csInf_upper_bounds_eq_csSup` (commanddeclaration)
```lean
theorem csInf_upper_bounds_eq_csSup {s : Set α} (h : BddAbove s) (hs : s.Nonempty) :
    sInf (upperBounds s) = sSup s
```

## Premise full source (with proof)
### `csInf_upper_bounds_eq_csSup` (commanddeclaration) at `Mathlib/Order/ConditionallyCompleteLattice/Basic.lean`
```lean
theorem csInf_upper_bounds_eq_csSup {s : Set α} (h : BddAbove s) (hs : s.Nonempty) :
    sInf (upperBounds s) = sSup s :=
  (isGLB_csInf h <| hs.mono fun _ hx _ hy => hy hx).unique (isLUB_csSup hs h).isGLB
```

## Filler (hint:2 → hint:3 token-match, ≈324 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris
