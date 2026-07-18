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

## Transitive premise context (1-hop, 1/1 premises, ≈297 tokens)
### `Subtype` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`Subtype p`, usually written as `{x : α // p x}`, is a type which
represents all the elements `x : α` for which `p x` is true. It is structurally
a pair-like type, so if you have `x : α` and `h : p x` then
`⟨x, h⟩ : {x // p x}`. An element `s : {x // p x}` will coerce to `α` but
you can also make it explicit using `s.1` or `s.val`.
-/
structure Subtype {α : Sort u} (p : α → Prop) where
  /-- If `s : {x // p x}` then `s.val : α` is the underlying element in the base
  type. You can also write this as `s.1`, or simply as `s` when the type is
  known from context. -/
  val : α
  /-- If `s : {x // p x}` then `s.2` or `s.property` is the assertion that
  `p s.1`, that is, that `s` is in fact an element for which `p` holds. -/
  property : p val
```
