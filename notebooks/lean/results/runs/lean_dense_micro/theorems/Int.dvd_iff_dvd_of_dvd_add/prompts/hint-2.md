## Current goal
```
⊢ a ∣ b ↔ a ∣ c
```

## Full tactic state
```
a b c : Int
H : a ∣ b - -c
⊢ a ∣ b ↔ a ∣ c
```

## Proof so far (1 tactic)
```lean
rw [← Int.sub_neg] at H
```

## Theorem
`Int.dvd_iff_dvd_of_dvd_add` in `.lake/packages/std/Std/Data/Int/DivMod.lean`

## Premises used in the next tactic
- `Int.dvd_iff_dvd_of_dvd_sub`
- `Int.dvd_neg`

## Premise signatures
### `Int.dvd_iff_dvd_of_dvd_sub` (commanddeclaration)
```lean
protected theorem dvd_iff_dvd_of_dvd_sub {a b c : Int} (H : a ∣ b - c) : a ∣ b ↔ a ∣ c
```

### `Int.dvd_neg` (commanddeclaration)
```lean
protected theorem dvd_neg {a b : Int} : a ∣ -b ↔ a ∣ b
```

## Premise full source (with proof)
### `Int.dvd_iff_dvd_of_dvd_sub` (commanddeclaration) at `.lake/packages/std/Std/Data/Int/DivMod.lean`
```lean
protected theorem dvd_iff_dvd_of_dvd_sub {a b c : Int} (H : a ∣ b - c) : a ∣ b ↔ a ∣ c :=
  ⟨fun h => Int.sub_sub_self b c ▸ Int.dvd_sub h H,
   fun h => Int.sub_add_cancel b c ▸ Int.dvd_add H h⟩
```

### `Int.dvd_neg` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/DivModLemmas.lean`
```lean
protected theorem dvd_neg {a b : Int} : a ∣ -b ↔ a ∣ b := by
  constructor <;> exact fun ⟨k, e⟩ =>
    ⟨-k, by simp [← e, Int.neg_mul, Int.mul_neg, Int.neg_neg]⟩
```
