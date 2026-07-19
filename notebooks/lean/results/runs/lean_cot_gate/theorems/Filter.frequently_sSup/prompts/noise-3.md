## Current goal
```
⊢ (∃ᶠ (x : α) in sSup fs, p x) ↔ ∃ f ∈ fs, ∃ᶠ (x : α) in f, p x
```

## Full tactic state
```
α : Type u
β : Type v
γ : Type w
δ : Type u_1
ι : Sort x
p : α → Prop
fs : Set (Filter α)
⊢ (∃ᶠ (x : α) in sSup fs, p x) ↔ ∃ f ∈ fs, ∃ᶠ (x : α) in f, p x
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Filter.frequently_sSup` in `Mathlib/Order/Filter/Basic.lean`

## Premises used in the next tactic
- `Filter.Frequently`
- `Classical.not_forall`
- `Filter.eventually_sSup`
- `exists_prop`

## Premise signatures
### `Filter.Frequently` (commanddeclaration)
```lean
protected def Frequently (p : α → Prop) (f : Filter α) : Prop
```

### `Classical.not_forall` (commanddeclaration)
```lean
@[simp] theorem not_forall {p : α → Prop} : (¬∀ x, p x) ↔ ∃ x, ¬p x
```

### `Filter.eventually_sSup` (commanddeclaration)
```lean
@[simp]
theorem eventually_sSup {p : α → Prop} {fs : Set (Filter α)} :
    (∀ᶠ x in sSup fs, p x) ↔ ∀ f ∈ fs, ∀ᶠ x in f, p x
```

### `exists_prop` (commanddeclaration)
```lean
@[simp] theorem exists_prop : (∃ _h : a, b) ↔ a ∧ b
```

## Premise full source (with proof)
### `Filter.Frequently` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
/-- `f.Frequently p` or `∃ᶠ x in f, p x` mean that `{x | ¬p x} ∉ f`. E.g., `∃ᶠ x in atTop, p x`
means that there exist arbitrarily large `x` for which `p` holds true. -/
protected def Frequently (p : α → Prop) (f : Filter α) : Prop :=
  ¬∀ᶠ x in f, ¬p x
```

### `Classical.not_forall` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Classical.lean`
```lean
@[simp] theorem not_forall {p : α → Prop} : (¬∀ x, p x) ↔ ∃ x, ¬p x := Decidable.not_forall
```

### `Filter.eventually_sSup` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
@[simp]
theorem eventually_sSup {p : α → Prop} {fs : Set (Filter α)} :
    (∀ᶠ x in sSup fs, p x) ↔ ∀ f ∈ fs, ∀ᶠ x in f, p x :=
  Iff.rfl
```

### `exists_prop` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/PropLemmas.lean`
```lean
@[simp] theorem exists_prop : (∃ _h : a, b) ↔ a ∧ b :=
  ⟨fun ⟨hp, hq⟩ => ⟨hp, hq⟩, fun ⟨hp, hq⟩ => ⟨hp, hq⟩⟩
```

## Filler (hint:2 → hint:3 token-match, ≈582 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet,
