## Current goal
```
⊢ revFind s p =
    Option.map (fun x => { byteIdx := utf8Len x }) (List.tail? (List.dropWhile (fun x => !p x) (List.reverse s.data)))
```

## Full tactic state
```
p : Char → Bool
s : String
⊢ revFind s p =
    Option.map (fun x => { byteIdx := utf8Len x }) (List.tail? (List.dropWhile (fun x => !p x) (List.reverse s.data)))
```
