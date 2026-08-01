## Current goal
```
⊢ find? a l = Option.map (fun x => x.snd) (List.find? (fun x => x.fst == a) (toList l))
```

## Full tactic state
```
α : Type u_1
β : Type u_2
inst✝ : BEq α
a : α
l : AssocList α β
⊢ find? a l = Option.map (fun x => x.snd) (List.find? (fun x => x.fst == a) (toList l))
```
