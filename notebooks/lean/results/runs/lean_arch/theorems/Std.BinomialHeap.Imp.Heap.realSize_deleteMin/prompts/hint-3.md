## Current goal
```
⊢ m + HeapNode.realSize node + realSize next + 1 =
    realSize
        (merge le (HeapNode.toHeap { before := before, val := val, node := node, next := next }.node)
          ({ before := before, val := val, node := node, next := next }.before
            { before := before, val := val, node := node, next := next }.next)) +
      1
```

## Full tactic state
```
α : Type u_1
le : α → α → Bool
r : Nat
a : α
c : HeapNode α
s : Heap α
before : Heap α → Heap α
val : α
node : HeapNode α
next : Heap α
m : Nat
ih₁ : ∀ (s : Heap α), realSize (before s) = m + realSize s
ih₂ : HeapNode.realSize c + realSize s + 1 = m + HeapNode.realSize node + realSize next + 1
⊢ m + HeapNode.realSize node + realSize next + 1 =
    realSize
        (merge le (HeapNode.toHeap { before := before, val := val, node := node, next := next }.node)
          ({ before := before, val := val, node := node, next := next }.before
            { before := before, val := val, node := node, next := next }.next)) +
      1
```

## Proof so far (9 tactics)
```lean
cases s with cases eq | cons r a c s => ?_
have : (s.findMin le (cons r a c) ⟨id, a, c, s⟩).HasSize (c.realSize + s.realSize + 1) :=
  Heap.realSize_findMin (c.realSize + 1) (by simp) (Nat.add_right_comm ..) ⟨0, by simp⟩
revert this
match s.findMin le (cons r a c) ⟨id, a, c, s⟩ with
| { before, val, node, next } =>
  intro ⟨m, ih₁, ih₂⟩; dsimp only at ih₁ ih₂
  rw [realSize, Nat.add_right_comm, ih₂]
  simp only [realSize_merge, HeapNode.realSize_toHeap, ih₁, Nat.add_assoc, Nat.add_left_comm]
simp
simp
intro ⟨m, ih₁, ih₂⟩
dsimp only at ih₁ ih₂
rw [realSize, Nat.add_right_comm, ih₂]
```

## Theorem
`Std.BinomialHeap.Imp.Heap.realSize_deleteMin` in `.lake/packages/std/Std/Data/BinomialHeap/Basic.lean`

## Premises used in the next tactic
- `Std.BinomialHeap.Imp.Heap.realSize_merge`
- `Std.BinomialHeap.Imp.HeapNode.realSize_toHeap`
- `Nat.add_assoc`
- `Nat.add_left_comm`

## Premise signatures
### `Std.BinomialHeap.Imp.Heap.realSize_merge` (commanddeclaration)
```lean
theorem Heap.realSize_merge (le) (s₁ s₂ : Heap α) :
    (s₁.merge le s₂).realSize = s₁.realSize + s₂.realSize
```

### `Std.BinomialHeap.Imp.HeapNode.realSize_toHeap` (commanddeclaration)
```lean
theorem HeapNode.realSize_toHeap (s : HeapNode α) : s.toHeap.realSize = s.realSize
```

### `Nat.add_assoc` (commanddeclaration)
```lean
protected theorem add_assoc : ∀ (n m k : Nat), (n + m) + k = n + (m + k)
```

### `Nat.add_left_comm` (commanddeclaration)
```lean
protected theorem add_left_comm (n m k : Nat) : n + (m + k) = m + (n + k)
```

## Premise full source (with proof)
### `Std.BinomialHeap.Imp.Heap.realSize_merge` (commanddeclaration) at `.lake/packages/std/Std/Data/BinomialHeap/Basic.lean`
```lean
theorem Heap.realSize_merge (le) (s₁ s₂ : Heap α) :
    (s₁.merge le s₂).realSize = s₁.realSize + s₂.realSize := by
  unfold merge; split
  · simp
  · simp
  · next r₁ a₁ n₁ t₁ r₂ a₂ n₂ t₂ =>
    have IH₁ r a n := realSize_merge le t₁ (cons r a n t₂)
    have IH₂ r a n := realSize_merge le (cons r a n t₁) t₂
    have IH₃ := realSize_merge le t₁ t₂
    split; · simp [IH₁, Nat.add_assoc]
    split; · simp [IH₂, Nat.add_assoc, Nat.add_left_comm]
    split; simp only; rename_i a n eq
    have : n.realSize = n₁.realSize + 1 + n₂.realSize := by
      rw [combine] at eq; split at eq <;> cases eq <;>
        simp [Nat.add_assoc, Nat.add_left_comm, Nat.add_comm]
    split <;> split <;> simp [IH₁, IH₂, IH₃, this, Nat.add_assoc, Nat.add_left_comm]
termination_by s₁.length + s₂.length
```

### `Std.BinomialHeap.Imp.HeapNode.realSize_toHeap` (commanddeclaration) at `.lake/packages/std/Std/Data/BinomialHeap/Basic.lean`
```lean
theorem HeapNode.realSize_toHeap (s : HeapNode α) : s.toHeap.realSize = s.realSize := go s where
  go {n res} : ∀ s : HeapNode α, (toHeap.go s n res).realSize = s.realSize + res.realSize
  | .nil => (Nat.zero_add _).symm
  | .node a c s => by simp [toHeap.go, go, Nat.add_assoc, Nat.add_left_comm]
```

### `Nat.add_assoc` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem add_assoc : ∀ (n m k : Nat), (n + m) + k = n + (m + k)
  | _, _, 0      => rfl
  | n, m, succ k => congrArg succ (Nat.add_assoc n m k)
```

### `Nat.add_left_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem add_left_comm (n m k : Nat) : n + (m + k) = m + (n + k) := by
  rw [← Nat.add_assoc, Nat.add_comm n m, Nat.add_assoc]
```

## Transitive premise context (1-hop, 7/7 premises, ≈1484 tokens)
### `Nat.add_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem add_comm : ∀ (n m : Nat), n + m = m + n
  | n, 0   => Eq.symm (Nat.zero_add n)
  | n, m+1 => by
    have : succ (n + m) = succ (m + n) := by apply congrArg; apply Nat.add_comm
    rw [succ_add m n]
    apply this
```

### `Std.BinomialHeap.Imp.HeapNode` (commanddeclaration) at `.lake/packages/std/Std/Data/BinomialHeap/Basic.lean`
```lean
/--
A `HeapNode` is one of the internal nodes of the binomial heap.
It is always a perfect binary tree, with the depth of the tree stored in the `Heap`.
However the interpretation of the two pointers is different: we view the `child`
as going to the first child of this node, and `sibling` goes to the next sibling
of this tree. So it actually encodes a forest where each node has children
`node.child`, `node.child.sibling`, `node.child.sibling.sibling`, etc.

Each edge in this forest denotes a `le a b` relation that has been checked, so
the root is smaller than everything else under it.
-/
inductive HeapNode (α : Type u) where
  /-- An empty forest, which has depth `0`. -/
  | nil : HeapNode α
  /-- A forest of rank `r + 1` consists of a root `a`,
  a forest `child` of rank `r` elements greater than `a`,
  and another forest `sibling` of rank `r`. -/
  | node (a : α) (child sibling : HeapNode α) : HeapNode α
  deriving Repr

/--
The "real size" of the node, counting up how many values of type `α` are stored.
This is `O(n)` and is intended mainly for specification purposes.
For a well formed `HeapNode` the size is always `2^n - 1` where `n` is the depth.
-/
```

### `Lean.Meta.Match.SimpH.go` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Meta/Match/MatchEqs.lean`
```lean
partial def go : M Bool := do
  if (← isDone) then
    return true
  else if (← processNextEq) then
    go
  else
    return false
```

### `Nat.zero_add` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
@[simp] protected theorem zero_add : ∀ (n : Nat), 0 + n = n
  | 0   => rfl
  | n+1 => congrArg succ (Nat.zero_add n)
```

### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```

### `Nat` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
The type of natural numbers, starting at zero. It is defined as an
inductive type freely generated by "zero is a natural number" and
"the successor of a natural number is a natural number".

You can prove a theorem `P n` about `n : Nat` by `induction n`, which will
expect a proof of the theorem for `P 0`, and a proof of `P (succ i)` assuming
a proof of `P i`. The same method also works to define functions by recursion
on natural numbers: induction and recursion are two expressions of the same
operation from Lean's point of view.

```
open Nat
example (n : Nat) : n < succ n := by
  induction n with
  | zero =>
    show 0 < 1
    decide
  | succ i ih => -- ih : i < succ i
    show succ i < succ (succ i)
    exact Nat.succ_lt_succ ih
```

This type is special-cased by both the kernel and the compiler:
* The type of expressions contains "`Nat` literals" as a primitive constructor,
  and the kernel knows how to reduce zero/succ expressions to nat literals.
* If implemented naively, this type would represent a numeral `n` in unary as a
  linked list with `n` links, which is horribly inefficient. Instead, the
  runtime itself has a special representation for `Nat` which stores numbers up
  to 2^63 directly and larger numbers use an arbitrary precision "bignum"
  library (usually [GMP](https://gmplib.org/)).
-/
inductive Nat where
  /-- `Nat.zero`, normally written `0 : Nat`, is the smallest natural number.
  This is one of the two constructors of `Nat`. -/
  | zero : Nat
  /-- The successor function on natural numbers, `succ n = n + 1`.
  This is one of the two constructors of `Nat`. -/
  | succ (n : Nat) : Nat
```

### `congrArg` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Congruence in the function argument: if `a₁ = a₂` then `f a₁ = f a₂` for
any (nondependent) function `f`. This is more powerful than it might look at first, because
you can also use a lambda expression for `f` to prove that
`<something containing a₁> = <something containing a₂>`. This function is used
internally by tactics like `congr` and `simp` to apply equalities inside
subterms.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
theorem congrArg {α : Sort u} {β : Sort v} {a₁ a₂ : α} (f : α → β) (h : Eq a₁ a₂) : Eq (f a₁) (f a₂) :=
  h ▸ rfl

/--
Congruence in both function and argument. If `f₁ = f₂` and `a₁ = a₂` then
`f₁ a₁ = f₂ a₂`. This only works for nondependent functions; the theorem
statement is more complex in the dependent case.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
```
