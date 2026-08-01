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
