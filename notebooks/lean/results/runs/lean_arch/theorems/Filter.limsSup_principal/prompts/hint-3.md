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

## Transitive premise context (1-hop, 4/4 premises, ≈300 tokens)
### `BddAbove` (commanddeclaration) at `Mathlib/Order/Bounds/Basic.lean`
```lean
/-- A set is bounded above if there exists an upper bound. -/
def BddAbove (s : Set α) :=
  (upperBounds s).Nonempty
```

### `upperBounds` (commanddeclaration) at `Mathlib/Order/Bounds/Basic.lean`
```lean
/-- The set of upper bounds of a set. -/
def upperBounds (s : Set α) : Set α :=
  { x | ∀ ⦃a⦄, a ∈ s → a ≤ x }
```

### `isGLB_csInf` (commanddeclaration) at `Mathlib/Order/ConditionallyCompleteLattice/Basic.lean`
```lean
theorem isGLB_csInf (ne : s.Nonempty) (H : BddBelow s) : IsGLB s (sInf s) :=
  ⟨fun _ => csInf_le H, fun _ => le_csInf ne⟩
```

### `isLUB_csSup` (commanddeclaration) at `Mathlib/Order/ConditionallyCompleteLattice/Basic.lean`
```lean
theorem isLUB_csSup (ne : s.Nonempty) (H : BddAbove s) : IsLUB s (sSup s) :=
  ⟨fun _ => le_csSup H, fun _ => csSup_le ne⟩
```
