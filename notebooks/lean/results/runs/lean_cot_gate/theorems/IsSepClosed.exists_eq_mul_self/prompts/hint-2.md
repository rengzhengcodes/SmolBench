## Current goal
```
⊢ ∃ z_1, z ^ 2 = z_1 * z_1
```

## Full tactic state
```
case intro
k : Type u
inst✝² : Field k
K : Type v
inst✝¹ : Field K
inst✝ : IsSepClosed k
h2 : NeZero 2
z : k
⊢ ∃ z_1, z ^ 2 = z_1 * z_1
```

## Proof so far (1 tactic)
```lean
rcases exists_pow_nat_eq x 2 with ⟨z, rfl⟩
```

## Theorem
`IsSepClosed.exists_eq_mul_self` in `Mathlib/FieldTheory/IsSepClosed.lean`

## Premises used in the next tactic
- `sq`

## Premise signatures
### `sq` (stdtacticaliasalias)
```lean
@[to_additive existing two_nsmul] alias sq
```

## Premise full source (with proof)
### `sq` (stdtacticaliasalias) at `Mathlib/Algebra/GroupPower/Basic.lean`
```lean
@[to_additive existing two_nsmul] alias sq := pow_two
```
