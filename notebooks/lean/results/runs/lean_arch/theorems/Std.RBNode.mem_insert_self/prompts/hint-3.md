## Current goal
```
⊢ ∃ s t_1, toList (insert cmp t v) = s ++ v :: t_1
```

## Full tactic state
```
α : Type u_1
c : RBColor
n : Nat
v : α
cmp : α → α → Ordering
t : RBNode α
ht : Balanced t c n
⊢ ∃ s t_1, toList (insert cmp t v) = s ++ v :: t_1
```

## Proof so far (1 tactic)
```lean
rw [← mem_toList, List.mem_iff_append]
```

## Theorem
`Std.RBNode.mem_insert_self` in `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`

## Premises used in the next tactic
- `Std.RBNode.zoom`
- `Std.RBNode.nil`
- `Std.RBNode.exists_insert_toList_zoom_nil`
- `Std.RBNode.node`
- `Std.RBNode.exists_insert_toList_zoom_node`

## Premise signatures
### `Std.RBNode.zoom` (commanddeclaration)
```lean
@[specialize] def zoom (cut : α → Ordering) : RBNode α → (e : Path α := .root) → RBNode α × Path α
  | nil, path => (nil, path)
  | n@(node c a y b), path =>
    match cut y with
    | .lt => zoom cut a (.left c path y b)
    | .gt => zoom cut b (.right c a y path)
    | .eq => (n, path)
```

### `Std.RBNode.nil`
_(not found in premise corpus)_

### `Std.RBNode.exists_insert_toList_zoom_nil` (commanddeclaration)
```lean
theorem exists_insert_toList_zoom_nil {t : RBNode α} (ht : Balanced t c n)
    (e : zoom (cmp v) t = (nil, p)) :
    ∃ L R, t.toList = L ++ R ∧ (t.insert cmp v).toList = L ++ v :: R
```

### `Std.RBNode.node`
_(not found in premise corpus)_

### `Std.RBNode.exists_insert_toList_zoom_node` (commanddeclaration)
```lean
theorem exists_insert_toList_zoom_node {t : RBNode α} (ht : Balanced t c n)
    (e : zoom (cmp v) t = (node c' l v' r, p)) :
    ∃ L R, t.toList = L ++ v' :: R ∧ (t.insert cmp v).toList = L ++ v :: R
```

## Premise full source (with proof)
### `Std.RBNode.zoom` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Basic.lean`
```lean
/--
Like `find?`, but instead of just returning the element, it returns the entire subtree
at the element and a path back to the root for reconstructing the tree.
-/
@[specialize] def zoom (cut : α → Ordering) : RBNode α → (e : Path α := .root) → RBNode α × Path α
  | nil, path => (nil, path)
  | n@(node c a y b), path =>
    match cut y with
    | .lt => zoom cut a (.left c path y b)
    | .gt => zoom cut b (.right c a y path)
    | .eq => (n, path)

/--
This function does the second part of `RBNode.ins`,
which unwinds the stack and rebuilds the tree.
-/
```

### `Std.RBNode.nil`
_(not found in premise corpus)_

### `Std.RBNode.exists_insert_toList_zoom_nil` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`
```lean
theorem exists_insert_toList_zoom_nil {t : RBNode α} (ht : Balanced t c n)
    (e : zoom (cmp v) t = (nil, p)) :
    ∃ L R, t.toList = L ++ R ∧ (t.insert cmp v).toList = L ++ v :: R :=
  ⟨p.listL, p.listR, by simp [← zoom_toList e, insert_toList_zoom_nil ht e]⟩
```

### `Std.RBNode.node`
_(not found in premise corpus)_

### `Std.RBNode.exists_insert_toList_zoom_node` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`
```lean
theorem exists_insert_toList_zoom_node {t : RBNode α} (ht : Balanced t c n)
    (e : zoom (cmp v) t = (node c' l v' r, p)) :
    ∃ L R, t.toList = L ++ v' :: R ∧ (t.insert cmp v).toList = L ++ v :: R := by
  refine ⟨p.listL ++ l.toList, r.toList ++ p.listR, ?_⟩
  simp [← zoom_toList e, insert_toList_zoom_node ht e]
```

## Transitive premise context (1-hop, 9/9 premises, ≈842 tokens)
### `Lean.Xml.Parser.element` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Data/Xml/Parser.lean`
```lean
  /-- https://www.w3.org/TR/xml/#NT-element -/
  partial def element : Parsec Element := do
    let elem ← Parser.elementPrefix
    EmptyElemTag elem <|> STag elem <*> content <* ETag
```

### `Ordering` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Ord.lean`
```lean
inductive Ordering where
  | lt | eq | gt
deriving Inhabited, BEq
```

### `Path` (commanddeclaration) at `Mathlib/Topology/Connected/PathConnected.lean`
```lean
/-- Continuous path connecting two points `x` and `y` in a topological space -/
-- porting note (#10927): removed @[nolint has_nonempty_instance]
structure Path (x y : X) extends C(I, X) where
  /-- The start point of a `Path`. -/
  source' : toFun 0 = x
  /-- The end point of a `Path`. -/
  target' : toFun 1 = y
```

### `Module.Free.function` (commanddeclaration) at `Mathlib/LinearAlgebra/FreeModule/Basic.lean`
```lean
/-- The product of finitely many free modules is free (non-dependent version to help with typeclass
search). -/
instance function [Finite ι] : Module.Free R (ι → M) :=
  Free.pi _ _
```

### `Balanced` (commanddeclaration) at `Mathlib/Analysis/LocallyConvex/Basic.lean`
```lean
/-- A set `A` is balanced if `a • A` is contained in `A` whenever `a` has norm at most `1`. -/
def Balanced (A : Set E) :=
  ∀ a : 𝕜, ‖a‖ ≤ 1 → a • A ⊆ A
```

### `cmp` (commanddeclaration) at `Mathlib/Init/Data/Ordering/Basic.lean`
```lean
/--
Construct an `Ordering` from a type with a decidable `LT` instance,
assuming that incomparable terms are `Ordering.eq`.
-/
def cmp {α : Type u} [LT α] [DecidableRel ((· < ·) : α → α → Prop)] (a b : α) : Ordering :=
  cmpUsing (· < ·) a b
```

### `Std.RBNode.zoom_toList` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`
```lean
theorem _root_.Std.RBNode.zoom_toList {t : RBNode α} (eq : t.zoom cut = (t', p')) :
    p'.withList t'.toList = t.toList := by rw [← fill_toList, ← zoom_fill eq]; rfl
```

### `Std.RBNode.insert_toList_zoom_nil` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`
```lean
theorem insert_toList_zoom_nil {t : RBNode α} (ht : Balanced t c n)
    (e : zoom (cmp v) t = (nil, p)) :
    (t.insert cmp v).toList = p.withList [v] := insert_toList_zoom ht e
```

### `Std.RBNode.insert_toList_zoom_node` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`
```lean
theorem insert_toList_zoom_node {t : RBNode α} (ht : Balanced t c n)
    (e : zoom (cmp v) t = (node c' l v' r, p)) :
    (t.insert cmp v).toList = p.withList (node c l v r).toList := insert_toList_zoom ht e
```
