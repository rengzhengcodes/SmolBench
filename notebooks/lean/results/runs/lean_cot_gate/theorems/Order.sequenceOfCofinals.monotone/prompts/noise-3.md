## Current goal
```
⊢ sequenceOfCofinals p 𝒟 n ≤
    match some val✝ with
    | none => sequenceOfCofinals p 𝒟 n
    | some i => Cofinal.above (𝒟 i) (sequenceOfCofinals p 𝒟 n)
```

## Full tactic state
```
case hf.some
P : Type u_1
inst✝¹ : Preorder P
p : P
ι : Type u_2
inst✝ : Encodable ι
𝒟 : ι → Cofinal P
n : ℕ
val✝ : ι
⊢ sequenceOfCofinals p 𝒟 n ≤
    match some val✝ with
    | none => sequenceOfCofinals p 𝒟 n
    | some i => Cofinal.above (𝒟 i) (sequenceOfCofinals p 𝒟 n)
```

## Proof so far (5 tactics)
```lean
apply monotone_nat_of_le_succ
intro n
dsimp only [sequenceOfCofinals, Nat.add]
cases (Encodable.decode n : Option ι)
rfl
```

## Theorem
`Order.sequenceOfCofinals.monotone` in `Mathlib/Order/Ideal.lean`

## Premises used in the next tactic
- `Order.Cofinal.le_above`

## Premise signatures
### `Order.Cofinal.le_above` (commanddeclaration)
```lean
theorem le_above : x ≤ D.above x
```

## Premise full source (with proof)
### `Order.Cofinal.le_above` (commanddeclaration) at `Mathlib/Order/Ideal.lean`
```lean
theorem le_above : x ≤ D.above x :=
  (Classical.choose_spec <| D.mem_gt x).2
```

## Filler (hint:2 → hint:3 token-match, ≈122 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
