## Current goal
```
⊢ size (extract.loop as (min stop (size as) - start) start #[]) = min stop (size as) - start
```

## Full tactic state
```
α : Type u_1
as : Array α
start stop : Nat
⊢ size (extract.loop as (min stop (size as) - start) start #[]) = min stop (size as) - start
```

## Proof so far (1 tactic)
```lean
simp [extract]
```

## Theorem
`Array.size_extract` in `.lake/packages/std/Std/Data/Array/Lemmas.lean`

## Premises used in the next tactic
- `Array.size_extract_loop`
- `Array.size_empty`
- `Nat.zero_add`
- `Nat.sub_min_sub_right`
- `Nat.min_assoc`
- `Nat.min_self`

## Premise signatures
### `Array.size_extract_loop` (commanddeclaration)
```lean
theorem size_extract_loop (as bs : Array α) (size start : Nat) :
    (extract.loop as size start bs).size = bs.size + min size (as.size - start)
```

### `Array.size_empty` (commanddeclaration)
```lean
theorem size_empty : (#[] : Array α).size = 0
```

### `Nat.zero_add` (commanddeclaration)
```lean
@[simp] protected theorem zero_add : ∀ (n : Nat), 0 + n = n
```

### `Nat.sub_min_sub_right` (commanddeclaration)
```lean
protected theorem sub_min_sub_right : ∀ (a b c : Nat), min (a - c) (b - c) = min a b - c
```

### `Nat.min_assoc` (commanddeclaration)
```lean
protected theorem min_assoc : ∀ (a b c : Nat), min (min a b) c = min a (min b c)
```

### `Nat.min_self` (commanddeclaration)
```lean
@[simp] protected theorem min_self (a : Nat) : min a a = a
```

## Premise full source (with proof)
### `Array.size_extract_loop` (commanddeclaration) at `.lake/packages/std/Std/Data/Array/Lemmas.lean`
```lean
theorem size_extract_loop (as bs : Array α) (size start : Nat) :
    (extract.loop as size start bs).size = bs.size + min size (as.size - start) := by
  induction size using Nat.recAux generalizing start bs with
  | zero => rw [extract_loop_zero, Nat.zero_min, Nat.add_zero]
  | succ size ih =>
    if h : start < as.size then
      rw [extract_loop_succ (h:=h), ih, size_push, Nat.add_assoc, ←Nat.add_min_add_left,
        Nat.sub_succ, Nat.one_add, Nat.one_add, Nat.succ_pred_eq_of_pos (Nat.sub_pos_of_lt h)]
    else
      have h := Nat.le_of_not_gt h
      rw [extract_loop_of_ge (h:=h), Nat.sub_eq_zero_of_le h, Nat.min_zero, Nat.add_zero]
```

### `Array.size_empty` (commanddeclaration) at `.lake/packages/std/Std/Data/Array/Lemmas.lean`
```lean
theorem size_empty : (#[] : Array α).size = 0 := rfl
```

### `Nat.zero_add` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
@[simp] protected theorem zero_add : ∀ (n : Nat), 0 + n = n
  | 0   => rfl
  | n+1 => congrArg succ (Nat.zero_add n)
```

### `Nat.sub_min_sub_right` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Lemmas.lean`
```lean
protected theorem sub_min_sub_right : ∀ (a b c : Nat), min (a - c) (b - c) = min a b - c
  | _, _, 0 => rfl
  | _, _, _+1 => Eq.trans (Nat.pred_min_pred ..) <| congrArg _ (Nat.sub_min_sub_right ..)
```

### `Nat.min_assoc` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Lemmas.lean`
```lean
protected theorem min_assoc : ∀ (a b c : Nat), min (min a b) c = min a (min b c)
  | 0, _, _ => by rw [Nat.zero_min, Nat.zero_min, Nat.zero_min]
  | _, 0, _ => by rw [Nat.zero_min, Nat.min_zero, Nat.zero_min]
  | _, _, 0 => by rw [Nat.min_zero, Nat.min_zero, Nat.min_zero]
  | _+1, _+1, _+1 => by simp only [Nat.succ_min_succ]; exact congrArg succ <| Nat.min_assoc ..
```

### `Nat.min_self` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Lemmas.lean`
```lean
@[simp] protected theorem min_self (a : Nat) : min a a = a := Nat.min_eq_left (Nat.le_refl _)
```

## Transitive premise context (1-hop, 26/26 premises, ≈3288 tokens)
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

### `PNat.XgcdType.start` (commanddeclaration) at `Mathlib/Data/PNat/Xgcd.lean`
```lean
/-- The following function provides the starting point for
 our algorithm.  We will apply an iterative reduction process
 to it, which will produce a system satisfying IsReduced.
 The gcd can be read off from this final system.
-/
def start (a b : ℕ+) : XgcdType :=
  ⟨0, 0, 0, 0, a - 1, b - 1⟩
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

### `Nat.recAux` (commanddeclaration) at `.lake/packages/std/Std/Data/Nat/Basic.lean`
```lean
/--
  Recursor identical to `Nat.rec` but uses notations `0` for `Nat.zero` and `·+1` for `Nat.succ`
-/
@[elab_as_elim]
protected def recAux {motive : Nat → Sort _}
    (zero : motive 0) (succ : ∀ n, motive n → motive (n+1)) : (t : Nat) → motive t
  | 0 => zero
  | _+1 => succ _ (Nat.recAux zero succ _)

/--
  Recursor identical to `Nat.recOn` but uses notations `0` for `Nat.zero` and `·+1` for `Nat.succ`
-/
```

### `Array.extract_loop_zero` (commanddeclaration) at `.lake/packages/std/Std/Data/Array/Lemmas.lean`
```lean
theorem extract_loop_zero (as bs : Array α) (start : Nat) : extract.loop as 0 start bs = bs := by
  rw [extract.loop]; split <;> rfl
```

### `Nat.zero_min` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Lemmas.lean`
```lean
@[simp] protected theorem zero_min (a) : min 0 a = 0 := Nat.min_eq_left (Nat.zero_le _)
```

### `Nat.add_zero` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
@[simp] protected theorem Nat.add_zero (n : Nat) : n + 0 = n := rfl
```

### `Array.extract_loop_succ` (commanddeclaration) at `.lake/packages/std/Std/Data/Array/Lemmas.lean`
```lean
theorem extract_loop_succ (as bs : Array α) (size start : Nat) (h : start < as.size) :
    extract.loop as (size+1) start bs = extract.loop as size (start+1) (bs.push as[start]) := by
  rw [extract.loop, dif_pos h]; rfl
```

### `Nat.add_assoc` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem add_assoc : ∀ (n m k : Nat), (n + m) + k = n + (m + k)
  | _, _, 0      => rfl
  | n, m, succ k => congrArg succ (Nat.add_assoc n m k)
```

### `Nat.add_min_add_left` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Lemmas.lean`
```lean
protected theorem add_min_add_left (a b c : Nat) : min (a + b) (a + c) = a + min b c := by
  repeat rw [Nat.add_comm a]
  exact Nat.add_min_add_right ..
```

### `Nat.sub_succ` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
theorem sub_succ (n m : Nat) : n - succ m = pred (n - m) := rfl
```

### `Nat.one_add` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Lemmas.lean`
```lean
theorem one_add (n) : 1 + n = succ n := Nat.add_comm ..
```

### `Nat.succ_pred_eq_of_pos` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
theorem succ_pred_eq_of_pos : ∀ {n}, 0 < n → succ (pred n) = n
  | _+1, _ => rfl

/-! # sub theorems -/
```

### `Nat.sub_pos_of_lt` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem sub_pos_of_lt (h : m < n) : 0 < n - m :=
  Nat.pos_iff_ne_zero.2 (Nat.sub_ne_zero_of_lt h)
```

### `Nat.le_of_not_gt` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem le_of_not_gt : ∀{a b : Nat}, ¬(b > a) → b ≤ a := Nat.ge_of_not_lt
```

### `Array.extract_loop_of_ge` (commanddeclaration) at `.lake/packages/std/Std/Data/Array/Lemmas.lean`
```lean
theorem extract_loop_of_ge (as bs : Array α) (size start : Nat) (h : start ≥ as.size) :
    extract.loop as size start bs = bs := by
  rw [extract.loop, dif_neg (Nat.not_lt_of_ge h)]
```

### `Nat.sub_eq_zero_of_le` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem sub_eq_zero_of_le {n m : Nat} (h : n ≤ m) : n - m = 0 := by
  match le.dest h with
  | ⟨k, hk⟩ => rw [← hk, Nat.sub_self_add]
```

### `Nat.min_zero` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Lemmas.lean`
```lean
@[simp] protected theorem min_zero (a) : min a 0 = 0 := Nat.min_eq_right (Nat.zero_le _)
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

### `Eq.trans` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Equality is transitive: if `a = b` and `b = c` then `a = c`.

Because this is in the `Eq` namespace, if you have variables or expressions
`h₁ : a = b` and `h₂ : b = c`, you can use `h₁.trans h₂ : a = c` as shorthand
for `Eq.trans h₁ h₂`.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
theorem Eq.trans {α : Sort u} {a b c : α} (h₁ : Eq a b) (h₂ : Eq b c) : Eq a c :=
  h₂ ▸ h₁

/--
Cast across a type equality. If `h : α = β` is an equality of types, and
`a : α`, then `a : β` will usually not typecheck directly, but this function
will allow you to work around this and embed `a` in type `β` as `cast h a : β`.

It is best to avoid this function if you can, because it is more complicated
to reason about terms containing casts, but if the types don't match up
definitionally sometimes there isn't anything better you can do.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
```

### `Nat.pred_min_pred` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Lemmas.lean`
```lean
protected theorem pred_min_pred : ∀ (x y), min (pred x) (pred y) = pred (min x y)
  | 0, _ => by simp only [Nat.pred_zero, Nat.zero_min]
  | _, 0 => by simp only [Nat.pred_zero, Nat.min_zero]
  | _+1, _+1 => by simp only [Nat.pred_succ, Nat.succ_min_succ]
```

### `min_assoc` (commanddeclaration) at `Mathlib/Init/Order/LinearOrder.lean`
```lean
theorem min_assoc (a b c : α) : min (min a b) c = min a (min b c) := by
  apply eq_min
  · apply le_trans; apply min_le_left; apply min_le_left
  · apply le_min; apply le_trans; apply min_le_left; apply min_le_right; apply min_le_right
  · intro d h₁ h₂; apply le_min; apply le_min h₁; apply le_trans h₂; apply min_le_left
    apply le_trans h₂; apply min_le_right
```

### `Nat.succ_min_succ` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Lemmas.lean`
```lean
theorem succ_min_succ (x y) : min (succ x) (succ y) = succ (min x y) := by
  cases Nat.le_total x y with
  | inl h => rw [Nat.min_eq_left h, Nat.min_eq_left (Nat.succ_le_succ h)]
  | inr h => rw [Nat.min_eq_right h, Nat.min_eq_right (Nat.succ_le_succ h)]
```

### `min_self` (commanddeclaration) at `Mathlib/Init/Order/LinearOrder.lean`
```lean
@[simp]
theorem min_self (a : α) : min a a = a := by simp [min_def]
```

### `Nat.min_eq_left` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/MinMax.lean`
```lean
protected theorem min_eq_left {a b : Nat} (h : a ≤ b) : min a b = a := if_pos h
```

### `Nat.le_refl` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
protected theorem Nat.le_refl (n : Nat) : LE.le n n :=
  Nat.le.refl
```
