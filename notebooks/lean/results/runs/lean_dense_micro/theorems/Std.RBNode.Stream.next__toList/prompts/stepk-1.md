## Current goal
```
⊢ Option.map
      (fun x =>
        match x with
        | (a, b) => (a, toList b))
      (next? s) =
    List.next? (toList s)
```

## Full tactic state
```
α : Type u_1
s : RBNode.Stream α
⊢ Option.map
      (fun x =>
        match x with
        | (a, b) => (a, toList b))
      (next? s) =
    List.next? (toList s)
```
