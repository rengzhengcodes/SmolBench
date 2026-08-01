## Current goal
```
⊢ Equiv empty a b ↔ a = b
```

## Full tactic state
```
a b : Nat
⊢ Equiv empty a b ↔ a = b
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Std.UnionFind.equiv_empty` in `.lake/packages/std/Std/Data/UnionFind/Lemmas.lean`

## Premises used in the next tactic
- `Std.UnionFind.Equiv`

## Premise signatures
### `Std.UnionFind.Equiv` (commanddeclaration)
```lean
def Equiv (self : UnionFind) (a b : Nat) : Prop
```

## Premise full source (with proof)
### `Std.UnionFind.Equiv` (commanddeclaration) at `.lake/packages/std/Std/Data/UnionFind/Basic.lean`
```lean
/-- Equivalence relation from a `UnionFind` structure -/
def Equiv (self : UnionFind) (a b : Nat) : Prop := self.rootD a = self.rootD b
```
