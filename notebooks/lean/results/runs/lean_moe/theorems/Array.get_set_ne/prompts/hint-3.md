## Current goal
```
⊢ (set a i v)[j] = a[j]
```

## Full tactic state
```
α : Type u_1
a : Array α
i : Fin (size a)
j : Nat
v : α
hj : j < size a
h : ↑i ≠ j
⊢ (set a i v)[j] = a[j]
```

## Proof so far (1 tactic)
```lean
simp [*]
```

## Theorem
`Array.get_set_ne` in `.lake/packages/std/Std/Data/Array/Lemmas.lean`

## Premises used in the next tactic
- `Array.set`
- `Array.getElem_eq_data_get`
- `List.get_set_ne`

## Premise signatures
### `Array.set` (commanddeclaration)
```lean
@[extern "lean_array_fset"]
def Array.set (a : Array α) (i : @& Fin a.size) (v : α) : Array α where
  data
```

### `Array.getElem_eq_data_get` (commanddeclaration)
```lean
theorem getElem_eq_data_get (a : Array α) (h : i < a.size) : a[i] = a.data.get ⟨i, h⟩
```

### `List.get_set_ne` (commanddeclaration)
```lean
@[simp] theorem get_set_ne (l : List α) {i j : Nat} (h : i ≠ j) (a : α)
    (hj : j < (l.set i a).length) :
    (l.set i a).get ⟨j, hj⟩ = l.get ⟨j, by simp at hj; exact hj⟩
```

## Premise full source (with proof)
### `Array.set` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Set an element in an array without bounds checks, using a `Fin` index.

This will perform the update destructively provided that `a` has a reference
count of 1 when called.
-/
@[extern "lean_array_fset"]
def Array.set (a : Array α) (i : @& Fin a.size) (v : α) : Array α where
  data := a.data.set i.val v

/--
Set an element in an array, or do nothing if the index is out of bounds.

This will perform the update destructively provided that `a` has a reference
count of 1 when called.
-/
```

### `Array.getElem_eq_data_get` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Array/Lemmas.lean`
```lean
theorem getElem_eq_data_get (a : Array α) (h : i < a.size) : a[i] = a.data.get ⟨i, h⟩ := by
  by_cases i < a.size <;> (try simp [*]) <;> rfl
```

### `List.get_set_ne` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/List/Lemmas.lean`
```lean
@[simp] theorem get_set_ne (l : List α) {i j : Nat} (h : i ≠ j) (a : α)
    (hj : j < (l.set i a).length) :
    (l.set i a).get ⟨j, hj⟩ = l.get ⟨j, by simp at hj; exact hj⟩ :=
  match l, i, j with
  | [], _, _ => by
    simp
  | _ :: _, 0, 0 => by
    contradiction
  | _ :: _, 0, _ + 1 => by
    simp
  | _ :: _, _ + 1, 0 => by
    simp
  | _ :: l, i + 1, j + 1 => by
    have g : i ≠ j := h ∘ congrArg (· + 1)
    simp [get_set_ne l g]
```

## Transitive premise context (1-hop, 10/10 premises, ≈1906 tokens)
### `Lean.Xml.Parser.element` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Data/Xml/Parser.lean`
```lean
  /-- https://www.w3.org/TR/xml/#NT-element -/
  partial def element : Parsec Element := do
    let elem ← Parser.elementPrefix
    EmptyElemTag elem <|> STag elem <*> content <* ETag
```

### `Fin` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`Fin n` is a natural number `i` with the constraint that `0 ≤ i < n`.
It is the "canonical type with `n` elements".
-/
structure Fin (n : Nat) where
  /-- If `i : Fin n`, then `i.val : ℕ` is the described number. It can also be
  written as `i.1` or just `i` when the target type is known. -/
  val  : Nat
  /-- If `i : Fin n`, then `i.2` is a proof that `i.1 < n`. -/
  isLt : LT.lt val n
```

### `when` (commanddeclaration) at `Mathlib/Init/Control/Combinators.lean`
```lean
def when {m : Type → Type} [Monad m] (c : Prop) [Decidable c] (t : m Unit) : m Unit :=
  ite c t (pure ())
```

### `Lean.Parser.Attr.extern` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Attr.lean`
```lean
@[builtin_attr_parser] def extern     := leading_parser
  nonReservedSymbol "extern" >> optional (ppSpace >> numLit) >> many (ppSpace >> externEntry)
```

### `Array` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`Array α` is the type of [dynamic arrays](https://en.wikipedia.org/wiki/Dynamic_array)
with elements from `α`. This type has special support in the runtime.

An array has a size and a capacity; the size is `Array.size` but the capacity
is not observable from Lean code. Arrays perform best when unshared; as long
as they are used "linearly" all updates will be performed destructively on the
array, so it has comparable performance to mutable arrays in imperative
programming languages.

From the point of view of proofs `Array α` is just a wrapper around `List α`.
-/
structure Array (α : Type u) where
  /--
  Converts a `List α` into an `Array α`.

  At runtime, this constructor is implemented by `List.toArray` and is O(n) in the length of the
  list.
  -/
  mk ::
  /--
  Converts a `Array α` into an `List α`.

  At runtime, this projection is implemented by `Array.toList` and is O(n) in the length of the
  array. -/
  data : List α
```

### `by_cases` (commanddeclaration) at `Mathlib/Logic/Basic.lean`
```lean
theorem by_cases {q : Prop} (hpq : p → q) (hnpq : ¬p → q) : q :=
if hp : p then hpq hp else hnpq hp
```

### `Lean.Meta.Simp.SimprocEntry.try` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Meta/Tactic/Simp/Simproc.lean`
```lean
def SimprocEntry.try (s : SimprocEntry) (numExtraArgs : Nat) (e : Expr) : SimpM Step := do
  let mut extraArgs := #[]
  let mut e := e
  for _ in [:numExtraArgs] do
    extraArgs := extraArgs.push e.appArg!
    e := e.appFn!
  extraArgs := extraArgs.reverse
  let s ← s.proc e
  s.addExtraArgs extraArgs
```

### `List` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`List α` is the type of ordered lists with elements of type `α`.
It is implemented as a linked list.

`List α` is isomorphic to `Array α`, but they are useful for different things:
* `List α` is easier for reasoning, and
  `Array α` is modeled as a wrapper around `List α`
* `List α` works well as a persistent data structure, when many copies of the
  tail are shared. When the value is not shared, `Array α` will have better
  performance because it can do destructive updates.
-/
inductive List (α : Type u) where
  /-- `[]` is the empty list. -/
  | nil : List α
  /-- If `a : α` and `l : List α`, then `cons a l`, or `a :: l`, is the
  list whose first element is `a` and with `l` as the rest of the list. -/
  | cons (head : α) (tail : List α) : List α
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
