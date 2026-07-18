## Current goal
```
⊢ x ∈ RingHom.range (algebraMap (↥S) B) ↔ x ∈ S
```

## Full tactic state
```
A : Type u_1
B✝ : Type u_2
B' : Type u_3
inst✝⁶ : CommRing A
inst✝⁵ : Ring B✝
inst✝⁴ : Algebra A B✝
x✝ : B✝
inst✝³ : Nontrivial B✝
B : Type u_4
inst✝² : CommRing B
inst✝¹ : Algebra A B
inst✝ : Nontrivial B
S : Subalgebra A B
x : B
int : IsIntegral (↥S) x
⊢ x ∈ RingHom.range (algebraMap (↥S) B) ↔ x ∈ S
```

## Proof so far (1 tactic)
```lean
rw [two_le_natDegree_iff int, Iff.not]
```

## Theorem
`minpoly.two_le_natDegree_subalgebra` in `Mathlib/FieldTheory/Minpoly/Basic.lean`

## Premises used in the next tactic
- `Subtype.range_val_subtype`

## Premise signatures
### `Subtype.range_val_subtype` (commanddeclaration)
```lean
theorem range_val_subtype {p : α → Prop} : range (Subtype.val : Subtype p → α) = { x | p x }
```

## Premise full source (with proof)
### `Subtype.range_val_subtype` (commanddeclaration) at `Mathlib/Data/Set/Image.lean`
```lean
theorem range_val_subtype {p : α → Prop} : range (Subtype.val : Subtype p → α) = { x | p x } :=
  range_coe
```
