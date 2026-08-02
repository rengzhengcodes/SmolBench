## Current goal
```
⊢ (a.data ++ b.data)[i] = b.data[i - size a]
```

## Full tactic state
```
i : Nat
a b : ByteArray
hle : size a ≤ i
h : i < size (a ++ b)
h' : optParam (i - size a < size b) ⋯
⊢ (a.data ++ b.data)[i] = b.data[i - size a]
```
