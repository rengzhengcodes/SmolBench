## Current goal
```
⊢ offsetOfPos { data := l ++ r } { byteIdx := utf8Len l } = List.length l
```

## Full tactic state
```
l r : List Char
⊢ offsetOfPos { data := l ++ r } { byteIdx := utf8Len l } = List.length l
```
