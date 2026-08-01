## Current goal
```
⊢ range (a + b) = range a ++ range' a b
```

## Full tactic state
```
a b : Nat
⊢ range (a + b) = range a ++ range' a b
```

## Proof so far (1 tactic)
```lean
rw [← range'_eq_map_range]
```

## Theorem
`List.range_add` in `.lake/packages/std/Std/Data/List/Lemmas.lean`

## Premises used in the next tactic
- `List.range_eq_range'`
- `Nat.add_comm`
- `List.range'_append_1`
- `Eq.symm`

## Premise signatures
### `List.range_eq_range'` (commanddeclaration)
```lean
theorem range_eq_range' (n : Nat) : range n = range' 0 n
```

### `Nat.add_comm` (commanddeclaration)
```lean
protected theorem add_comm : ∀ (n m : Nat), n + m = m + n
```

### `List.range'_append_1` (commanddeclaration)
```lean
@[simp] theorem range'_append_1 (s m n : Nat) :
    range' s m ++ range' (s + m) n = range' s (n + m)
```

### `Eq.symm` (commanddeclaration)
```lean
theorem Eq.symm {α : Sort u} {a b : α} (h : Eq a b) : Eq b a
```

## Premise full source (with proof)
### `List.range_eq_range'` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Lemmas.lean`
```lean
theorem range_eq_range' (n : Nat) : range n = range' 0 n :=
  (range_loop_range' n 0).trans <| by rw [Nat.zero_add]
```

### `Nat.add_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem add_comm : ∀ (n m : Nat), n + m = m + n
  | n, 0   => Eq.symm (Nat.zero_add n)
  | n, m+1 => by
    have : succ (n + m) = succ (m + n) := by apply congrArg; apply Nat.add_comm
    rw [succ_add m n]
    apply this
```

### `List.range'_append_1` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Lemmas.lean`
```lean
@[simp] theorem range'_append_1 (s m n : Nat) :
    range' s m ++ range' (s + m) n = range' s (n + m) := by simpa using range'_append s m n 1
```

### `Eq.symm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Equality is symmetric: if `a = b` then `b = a`.

Because this is in the `Eq` namespace, if you have a variable `h : a = b`,
`h.symm` can be used as shorthand for `Eq.symm h` as a proof of `b = a`.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
theorem Eq.symm {α : Sort u} {a b : α} (h : Eq a b) : Eq b a :=
  h ▸ rfl

/--
Equality is transitive: if `a = b` and `b = c` then `a = c`.

Because this is in the `Eq` namespace, if you have variables or expressions
`h₁ : a = b` and `h₂ : b = c`, you can use `h₁.trans h₂ : a = c` as shorthand
for `Eq.trans h₁ h₂`.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
```
