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

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Std.AssocList.find?_eq` in `.lake/packages/std/Std/Data/AssocList.lean`

## Premises used in the next tactic
- `Std.AssocList.find?_eq_findEntry?`

## Premise signatures
### `Std.AssocList.find?_eq_findEntry?` (commanddeclaration)
```lean
theorem find?_eq_findEntry? [BEq α] (a : α) (l : AssocList α β) :
    find? a l = (l.findEntry? a).map (·.2)
```

## Premise full source (with proof)
### `Std.AssocList.find?_eq_findEntry?` (commanddeclaration) at `.lake/packages/std/Std/Data/AssocList.lean`
```lean
theorem find?_eq_findEntry? [BEq α] (a : α) (l : AssocList α β) :
    find? a l = (l.findEntry? a).map (·.2) := by
  induction l <;> simp [find?, List.find?_cons]; split <;> simp [*]
```
