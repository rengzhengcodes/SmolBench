## Current goal
```
⊢ Array.extract a.data start (start + (stop - start)) = Array.extract a.data start stop
```

## Full tactic state
```
a : ByteArray
start stop : Nat
h : stop ≤ start
⊢ Array.extract a.data start (start + (stop - start)) = Array.extract a.data start stop
```
