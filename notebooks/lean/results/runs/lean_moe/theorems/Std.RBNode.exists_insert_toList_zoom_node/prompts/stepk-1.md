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
