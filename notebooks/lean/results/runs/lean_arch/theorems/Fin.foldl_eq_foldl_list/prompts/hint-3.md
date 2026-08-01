## Current goal
```
⊢ foldl (n + 1) f x = List.foldl f x (list (n + 1))
```

## Full tactic state
```
case succ
α : Type u_1
n : Nat
ih : ∀ (f : α → Fin n → α) (x : α), foldl n f x = List.foldl f x (list n)
f : α → Fin (n + 1) → α
x : α
⊢ foldl (n + 1) f x = List.foldl f x (list (n + 1))
```

## Proof so far (2 tactics)
```lean
induction n using Nat.recAux generalizing x with
| zero => rfl
| succ n ih => rw [foldl_succ, ih, list_succ, List.foldl_cons, List.foldl_map]
rfl
```

## Theorem
`Fin.foldl_eq_foldl_list` in `.lake/packages/std/Std/Data/Fin/Lemmas.lean`

## Premises used in the next tactic
- `Fin.foldl_succ`
- `Fin.list_succ`
- `List.foldl_cons`
- `List.foldl_map`

## Premise signatures
### `Fin.foldl_succ` (commanddeclaration)
```lean
theorem foldl_succ (f : α → Fin (n+1) → α) (x) :
    foldl (n+1) f x = foldl n (fun x i => f x i.succ) (f x 0)
```

### `Fin.list_succ` (commanddeclaration)
```lean
theorem list_succ (n) : list (n+1) = 0 :: (list n).map Fin.succ
```

### `List.foldl_cons` (commanddeclaration)
```lean
@[simp] theorem foldl_cons (l : List α) (b : β) : (a :: l).foldl f b = l.foldl f (f b a)
```

### `List.foldl_map` (commanddeclaration)
```lean
theorem foldl_map (f : β₁ → β₂) (g : α → β₂ → α) (l : List β₁) (init : α) :
    (l.map f).foldl g init = l.foldl (fun x y => g x (f y)) init
```

## Premise full source (with proof)
### `Fin.foldl_succ` (commanddeclaration) at `.lake/packages/std/Std/Data/Fin/Lemmas.lean`
```lean
theorem foldl_succ (f : α → Fin (n+1) → α) (x) :
    foldl (n+1) f x = foldl n (fun x i => f x i.succ) (f x 0) := foldl_loop ..
```

### `Fin.list_succ` (commanddeclaration) at `.lake/packages/std/Std/Data/Fin/Lemmas.lean`
```lean
theorem list_succ (n) : list (n+1) = 0 :: (list n).map Fin.succ := by
  apply List.ext_get; simp; intro i; cases i <;> simp

/-! ### foldl -/
```

### `List.foldl_cons` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/List/Lemmas.lean`
```lean
@[simp] theorem foldl_cons (l : List α) (b : β) : (a :: l).foldl f b = l.foldl f (f b a) := rfl
```

### `List.foldl_map` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Lemmas.lean`
```lean
theorem foldl_map (f : β₁ → β₂) (g : α → β₂ → α) (l : List β₁) (init : α) :
    (l.map f).foldl g init = l.foldl (fun x y => g x (f y)) init := by
  induction l generalizing init <;> simp [*]
```

## Transitive premise context (1-hop, 7/7 premises, ≈1171 tokens)
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

### `foldl` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Fin/Fold.lean`
```lean
/-- Folds over `Fin n` from the left: `foldl 3 f x = f (f (f x 0) 1) 2`. -/
@[inline] def foldl (n) (f : α → Fin n → α) (init : α) : α := loop init 0 where
  /-- Inner loop for `Fin.foldl`. `Fin.foldl.loop n f x i = f (f (f x i) ...) (n-1)`  -/
  loop (x : α) (i : Nat) : α :=
    if h : i < n then loop (f x ⟨i, h⟩) (i+1) else x
  termination_by n - i

/-- Folds over `Fin n` from the right: `foldr 3 f x = f 0 (f 1 (f 2 x))`. -/
```

### `Fin.foldl_loop` (commanddeclaration) at `.lake/packages/std/Std/Data/Fin/Lemmas.lean`
```lean
theorem foldl_loop (f : α → Fin (n+1) → α) (x) (h : m < n+1) :
    foldl.loop (n+1) f x m = foldl.loop n (fun x i => f x i.succ) (f x ⟨m, h⟩) m := by
  if h' : m < n then
    rw [foldl_loop_lt _ _ h, foldl_loop_lt _ _ h', foldl_loop]; rfl
  else
    cases Nat.le_antisymm (Nat.le_of_lt_succ h) (Nat.not_lt.1 h')
    rw [foldl_loop_lt, foldl_loop_eq, foldl_loop_eq]
termination_by n - m
```

### `Fin.succ` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Fin/Basic.lean`
```lean
def succ : Fin n → Fin n.succ
  | ⟨i, h⟩ => ⟨i+1, Nat.succ_lt_succ h⟩
```

### `List.ext_get` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Lemmas.lean`
```lean
theorem ext_get {l₁ l₂ : List α} (hl : length l₁ = length l₂)
    (h : ∀ n h₁ h₂, get l₁ ⟨n, h₁⟩ = get l₂ ⟨n, h₂⟩) : l₁ = l₂ :=
  ext fun n =>
    if h₁ : n < length l₁ then by
      rw [get?_eq_get, get?_eq_get, h n h₁ (by rwa [← hl])]
    else by
      have h₁ := Nat.le_of_not_lt h₁
      rw [get?_len_le h₁, get?_len_le]; rwa [← hl]
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

### `init` (commanddeclaration) at `.lake/packages/proofwidgets/ProofWidgets/Demos/InteractiveSvg.lean`
```lean
def init : UpdateResult State := {
  html := <div>Init!!!</div>,
  state := { state := isvg.init
             time := 0
             selected := none
             mousePos := none
             idToData := isvg.render 0 none none isvg.init |>.idToDataList}
}
```
