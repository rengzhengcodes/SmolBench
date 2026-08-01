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

## Transitive premise context (1-hop, 3/3 premises, ≈308 tokens)
### `DecidableRel` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/-- A decidable relation. See `Decidable`. -/
abbrev DecidableRel {α : Sort u} (r : α → α → Prop) :=
  (a b : α) → Decidable (r a b)

/--
Asserts that `α` has decidable equality, that is, `a = b` is decidable
for all `a b : α`. See `Decidable`.
-/
```

### `Interval` (commanddeclaration) at `Mathlib/Order/Interval.lean`
```lean
/-- The closed intervals in an order.

We represent intervals either as `⊥` or a nonempty interval given by its endpoints `fst`, `snd`.
To convert intervals to the set of elements between these endpoints, use the coercion
`Interval α → Set α`. -/
@[reducible] -- Porting note: added reducible, it seems to help with coercions
def Interval (α : Type*) [LE α] :=
  WithBot (NonemptyInterval α) -- deriving Inhabited, LE, OrderBot
```

### `iInf` (commanddeclaration) at `Mathlib/Order/SetNotation.lean`
```lean
/-- Indexed infimum -/
def iInf [InfSet α] (s : ι → α) : α :=
  sInf (range s)
```
