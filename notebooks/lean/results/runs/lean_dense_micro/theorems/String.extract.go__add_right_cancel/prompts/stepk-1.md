## Current goal
```
⊢ go₁ cs { byteIdx := i + csize c + n } { byteIdx := b + n } { byteIdx := e + n } =
    go₁ cs { byteIdx := i + csize c } { byteIdx := b } { byteIdx := e }
```

## Full tactic state
```
case ind
s : List Char
i✝ b e n : Nat
c : Char
cs : List Char
i : Nat
ih :
  go₁ cs { byteIdx := i + csize c + n } { byteIdx := b + n } { byteIdx := e + n } =
    go₁ cs { byteIdx := i + csize c } { byteIdx := b } { byteIdx := e }
h : ¬i = b
⊢ go₁ cs { byteIdx := i + csize c + n } { byteIdx := b + n } { byteIdx := e + n } =
    go₁ cs { byteIdx := i + csize c } { byteIdx := b } { byteIdx := e }
```
