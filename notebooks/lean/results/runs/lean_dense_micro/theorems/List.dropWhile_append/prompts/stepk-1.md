## Current goal
```
⊢ (if p h = true then dropWhile p (t ++ ys) else h :: (t ++ ys)) =
    if isEmpty (if p h = true then dropWhile p t else h :: t) = true then dropWhile p ys
    else (if p h = true then dropWhile p t else h :: t) ++ ys
```

## Full tactic state
```
case cons
α : Type u_1
p : α → Bool
ys : List α
h : α
t : List α
ih : dropWhile p (t ++ ys) = if isEmpty (dropWhile p t) = true then dropWhile p ys else dropWhile p t ++ ys
⊢ (if p h = true then dropWhile p (t ++ ys) else h :: (t ++ ys)) =
    if isEmpty (if p h = true then dropWhile p t else h :: t) = true then dropWhile p ys
    else (if p h = true then dropWhile p t else h :: t) ++ ys
```
