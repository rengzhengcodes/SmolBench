## Current goal
```
⊢ swapAt! a i v = (a[i], set a { val := i, isLt := h } v)
```

## Full tactic state
```
α : Type u_1
a : Array α
i : Nat
v : α
h : i < size a
⊢ swapAt! a i v = (a[i], set a { val := i, isLt := h } v)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Array.swapAt!_def` in `.lake/packages/std/Std/Data/Array/Lemmas.lean`

## Premises used in the next tactic
- `Array.swapAt!`

## Premise signatures
### `Array.swapAt!` (commanddeclaration)
```lean
@[inline]
def swapAt! (a : Array α) (i : Nat) (v : α) : α × Array α
```

## Premise full source (with proof)
### `Array.swapAt!` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Array/Basic.lean`
```lean
@[inline]
def swapAt! (a : Array α) (i : Nat) (v : α) : α × Array α :=
  if h : i < a.size then
    swapAt a ⟨i, h⟩ v
  else
    have : Inhabited α := ⟨v⟩
    panic! ("index " ++ toString i ++ " out of bounds")
```
