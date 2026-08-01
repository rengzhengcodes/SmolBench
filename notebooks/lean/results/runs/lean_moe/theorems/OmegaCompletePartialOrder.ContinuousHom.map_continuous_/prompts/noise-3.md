## Current goal
```
⊢ Continuous' fun x => pure ∘ f
```

## Full tactic state
```
α : Type u
α' : Type u_1
β✝ : Type v
β' : Type u_2
γ✝ : Type u_3
φ : Type u_4
inst✝⁵ : OmegaCompletePartialOrder α
inst✝⁴ : OmegaCompletePartialOrder β✝
inst✝³ : OmegaCompletePartialOrder γ✝
inst✝² : OmegaCompletePartialOrder φ
inst✝¹ : OmegaCompletePartialOrder α'
inst✝ : OmegaCompletePartialOrder β'
β γ : Type v
f : β → γ
g : α → Part β
hg : Continuous' g
⊢ Continuous' fun x => pure ∘ f
```

## Proof so far (2 tactics)
```lean
simp only [map_eq_bind_pure_comp]
apply bind_continuous' _ _ hg
```

## Theorem
`OmegaCompletePartialOrder.ContinuousHom.map_continuous'` in `Mathlib/Order/OmegaCompletePartialOrder.lean`

## Premises used in the next tactic
- `OmegaCompletePartialOrder.const_continuous'`

## Premise signatures
### `OmegaCompletePartialOrder.const_continuous'` (commanddeclaration)
```lean
theorem const_continuous' (x : β) : Continuous' (Function.const α x)
```

## Premise full source (with proof)
### `OmegaCompletePartialOrder.const_continuous'` (commanddeclaration) at `Mathlib/Order/OmegaCompletePartialOrder.lean`
```lean
theorem const_continuous' (x : β) : Continuous' (Function.const α x) :=
  Continuous.of_bundled' (OrderHom.const α x) (continuous_const x)
```

## Filler (hint:2 → hint:3 token-match, ≈594 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et
