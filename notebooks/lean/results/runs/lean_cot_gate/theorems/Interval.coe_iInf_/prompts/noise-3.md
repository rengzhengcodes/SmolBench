## Current goal
```
⊢ ↑(⨅ i, ⨅ j, f i j) = ⋂ i, ⋂ j, ↑(f i j)
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
δ : Type u_4
ι : Sort u_5
κ : ι → Sort u_6
inst✝¹ : CompleteLattice α
inst✝ : DecidableRel fun x x_1 => x ≤ x_1
f : (i : ι) → κ i → Interval α
⊢ ↑(⨅ i, ⨅ j, f i j) = ⋂ i, ⋂ j, ↑(f i j)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Interval.coe_iInf₂` in `Mathlib/Order/Interval.lean`

## Premises used in the next tactic
- `Interval.coe_iInf`

## Premise signatures
### `Interval.coe_iInf` (commanddeclaration)
```lean
@[simp, norm_cast]
theorem coe_iInf [@DecidableRel α (· ≤ ·)] (f : ι → Interval α) :
    ↑(⨅ i, f i) = ⋂ i, (f i : Set α)
```

## Premise full source (with proof)
### `Interval.coe_iInf` (commanddeclaration) at `Mathlib/Order/Interval.lean`
```lean
@[simp, norm_cast]
theorem coe_iInf [@DecidableRel α (· ≤ ·)] (f : ι → Interval α) :
    ↑(⨅ i, f i) = ⋂ i, (f i : Set α) := by simp [iInf]
```

## Filler (hint:2 → hint:3 token-match, ≈331 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
