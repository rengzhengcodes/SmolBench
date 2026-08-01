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
