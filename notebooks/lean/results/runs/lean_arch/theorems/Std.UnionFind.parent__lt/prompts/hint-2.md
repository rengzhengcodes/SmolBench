## Current goal
```
⊢ (Array.get self.arr i).parent < size self
```

## Full tactic state
```
self : UnionFind
i : Fin (size self)
⊢ (Array.get self.arr i).parent < size self
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Std.UnionFind.parent'_lt` in `.lake/packages/std/Std/Data/UnionFind/Basic.lean`

## Premises used in the next tactic
- `Std.UnionFind.parentD_eq`
- `Std.UnionFind.parentD_lt`
- `Fin.is_lt`
- `Array.data_length`

## Premise signatures
### `Std.UnionFind.parentD_eq` (commanddeclaration)
```lean
theorem parentD_eq {arr : Array UFNode} {i} : parentD arr i.1 = (arr.get i).parent
```

### `Std.UnionFind.parentD_lt`
_(not found in premise corpus)_

### `Fin.is_lt` (commanddeclaration)
```lean
@[simp] theorem is_lt (a : Fin n) : (a : Nat) < n
```

### `Array.data_length` (commanddeclaration)
```lean
@[simp] theorem data_length {l : Array α} : l.data.length = l.size
```

## Premise full source (with proof)
### `Std.UnionFind.parentD_eq` (commanddeclaration) at `.lake/packages/std/Std/Data/UnionFind/Basic.lean`
```lean
theorem parentD_eq {arr : Array UFNode} {i} : parentD arr i.1 = (arr.get i).parent := dif_pos _
```

### `Std.UnionFind.parentD_lt`
_(not found in premise corpus)_

### `Fin.is_lt` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Fin/Lemmas.lean`
```lean
@[simp] theorem is_lt (a : Fin n) : (a : Nat) < n := a.2
```

### `Array.data_length` (commanddeclaration) at `.lake/packages/std/Std/Data/Array/Lemmas.lean`
```lean
@[simp] theorem data_length {l : Array α} : l.data.length = l.size := rfl

/-- # mem -/
```
