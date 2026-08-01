## Current goal
```
⊢ ∀ᶠ (x : α) in l, ∀ y ≤ f x, p y
```

## Full tactic state
```
ι : Type u_1
ι' : Type u_2
α✝ : Type u_3
β✝ : Type u_4
γ : Type u_5
α : Type u_6
β : Type u_7
inst✝ : Preorder β
l : Filter α
p : β → Prop
f : α → β
hf : Tendsto f l atBot
h_evtl : ∀ᶠ (x : β) in atBot, ∀ y ≤ x, p y
⊢ ∀ᶠ (x : α) in l, ∀ y ≤ f x, p y
```

## Proof so far (1 tactic)
```lean
rw [← Filter.eventually_forall_le_atBot] at h_evtl
```

## Theorem
`Filter.Tendsto.eventually_forall_le_atBot` in `Mathlib/Order/Filter/AtTopBot.lean`

## Premises used in the next tactic
- `Filter.Eventually.filter_mono`

## Premise signatures
### `Filter.Eventually.filter_mono` (commanddeclaration)
```lean
theorem Eventually.filter_mono {f₁ f₂ : Filter α} (h : f₁ ≤ f₂) {p : α → Prop}
    (hp : ∀ᶠ x in f₂, p x) : ∀ᶠ x in f₁, p x
```

## Premise full source (with proof)
### `Filter.Eventually.filter_mono` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
theorem Eventually.filter_mono {f₁ f₂ : Filter α} (h : f₁ ≤ f₂) {p : α → Prop}
    (hp : ∀ᶠ x in f₂, p x) : ∀ᶠ x in f₁, p x :=
  h hp
```

## Filler (hint:2 → hint:3 token-match, ≈250 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
