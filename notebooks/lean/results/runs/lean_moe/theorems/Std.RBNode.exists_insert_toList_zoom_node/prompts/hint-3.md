## Current goal
```
⊢ toList t = Path.listL p ++ toList l ++ v' :: (toList r ++ Path.listR p) ∧
    toList (insert cmp t v) = Path.listL p ++ toList l ++ v :: (toList r ++ Path.listR p)
```

## Full tactic state
```
α : Type u_1
c : RBColor
n : Nat
cmp : α → α → Ordering
c' : RBColor
l : RBNode α
v' : α
r : RBNode α
p : Path α
v : α
t : RBNode α
ht : Balanced t c n
e : zoom (cmp v) t = (node c' l v' r, p)
⊢ toList t = Path.listL p ++ toList l ++ v' :: (toList r ++ Path.listR p) ∧
    toList (insert cmp t v) = Path.listL p ++ toList l ++ v :: (toList r ++ Path.listR p)
```

## Proof so far (1 tactic)
```lean
refine ⟨p.listL ++ l.toList, r.toList ++ p.listR, ?_⟩
```

## Theorem
`Std.RBNode.exists_insert_toList_zoom_node` in `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`

## Premises used in the next tactic
- `Std.RBNode.zoom_toList`
- `Std.RBNode.insert_toList_zoom_node`

## Premise signatures
### `Std.RBNode.zoom_toList` (commanddeclaration)
```lean
theorem _root_.Std.RBNode.zoom_toList {t : RBNode α} (eq : t.zoom cut = (t', p')) :
    p'.withList t'.toList = t.toList
```

### `Std.RBNode.insert_toList_zoom_node` (commanddeclaration)
```lean
theorem insert_toList_zoom_node {t : RBNode α} (ht : Balanced t c n)
    (e : zoom (cmp v) t = (node c' l v' r, p)) :
    (t.insert cmp v).toList = p.withList (node c l v r).toList
```

## Premise full source (with proof)
### `Std.RBNode.zoom_toList` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`
```lean
theorem _root_.Std.RBNode.zoom_toList {t : RBNode α} (eq : t.zoom cut = (t', p')) :
    p'.withList t'.toList = t.toList := by rw [← fill_toList, ← zoom_fill eq]; rfl
```

### `Std.RBNode.insert_toList_zoom_node` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`
```lean
theorem insert_toList_zoom_node {t : RBNode α} (ht : Balanced t c n)
    (e : zoom (cmp v) t = (node c' l v' r, p)) :
    (t.insert cmp v).toList = p.withList (node c l v r).toList := insert_toList_zoom ht e
```

## Transitive premise context (1-hop, 5/5 premises, ≈477 tokens)
### `Std.RBNode.Path.fill_toList` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`
```lean
@[simp] theorem fill_toList {p : Path α} : (p.fill t).toList = p.withList t.toList := by
  induction p generalizing t <;> simp [*]
```

### `Std.RBNode.Path.zoom_fill` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Alter.lean`
```lean
theorem zoom_fill (H : zoom cut t path = (t', path')) : path.fill t = path'.fill t' :=
  (H ▸ zoom_fill' cut t path).symm
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

### `Std.RBNode.insert_toList_zoom` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`
```lean
theorem insert_toList_zoom {t : RBNode α} (ht : Balanced t c n)
    (e : zoom (cmp v) t = (t', p)) :
    (t.insert cmp v).toList = p.withList (t'.setRoot v).toList := by
  rw [← setBlack_toList, ← Path.zoom_insert ht e, setBlack_toList, Path.insert_toList]
```
