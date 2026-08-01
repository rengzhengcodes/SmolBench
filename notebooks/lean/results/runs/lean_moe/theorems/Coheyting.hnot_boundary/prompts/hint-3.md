## Current goal
```
⊢ ￢∂ a = ⊤
```

## Full tactic state
```
α : Type u_1
inst✝ : CoheytingAlgebra α
a✝ b a : α
⊢ ￢∂ a = ⊤
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Coheyting.hnot_boundary` in `Mathlib/Order/Heyting/Boundary.lean`

## Premises used in the next tactic
- `Coheyting.boundary`
- `hnot_inf_distrib`
- `sup_hnot_self`

## Premise signatures
### `Coheyting.boundary` (commanddeclaration)
```lean
def boundary (a : α) : α
```

### `hnot_inf_distrib` (commanddeclaration)
```lean
theorem hnot_inf_distrib (a b : α) : ￢(a ⊓ b) = ￢a ⊔ ￢b
```

### `sup_hnot_self` (commanddeclaration)
```lean
@[simp]
theorem sup_hnot_self (a : α) : a ⊔ ￢a = ⊤
```

## Premise full source (with proof)
### `Coheyting.boundary` (commanddeclaration) at `Mathlib/Order/Heyting/Boundary.lean`
```lean
/-- The boundary of an element of a co-Heyting algebra is the intersection of its Heyting negation
with itself. Note that this is always `⊥` for a boolean algebra. -/
def boundary (a : α) : α :=
  a ⊓ ￢a
```

### `hnot_inf_distrib` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
theorem hnot_inf_distrib (a b : α) : ￢(a ⊓ b) = ￢a ⊔ ￢b := by
  simp_rw [← top_sdiff', sdiff_inf_distrib]
```

### `sup_hnot_self` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
@[simp]
theorem sup_hnot_self (a : α) : a ⊔ ￢a = ⊤ :=
  Codisjoint.eq_top codisjoint_hnot_right
```

## Transitive premise context (1-hop, 6/6 premises, ≈445 tokens)
### `Lean.Xml.Parser.element` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Data/Xml/Parser.lean`
```lean
  /-- https://www.w3.org/TR/xml/#NT-element -/
  partial def element : Parsec Element := do
    let elem ← Parser.elementPrefix
    EmptyElemTag elem <|> STag elem <*> content <* ETag
```

### `Lake.Module.co` (commanddeclaration) at `.lake/packages/lean4/src/lean/lake/Lake/Build/Info.lean`
```lean
@[inherit_doc coFacet] abbrev co (self : Module) :=
  self.facet coFacet
```

### `top_sdiff'` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
@[simp]
theorem top_sdiff' (a : α) : ⊤ \ a = ￢a :=
  CoheytingAlgebra.top_sdiff _
```

### `sdiff_inf_distrib` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
theorem sdiff_inf_distrib (a b c : α) : a \ (b ⊓ c) = a \ b ⊔ a \ c :=
  eq_of_forall_ge_iff fun d => by
    rw [sup_le_iff, sdiff_le_comm, le_inf_iff]
    simp_rw [sdiff_le_comm]
```

### `Codisjoint.eq_top` (commanddeclaration) at `Mathlib/Order/Disjoint.lean`
```lean
theorem Codisjoint.eq_top : Codisjoint a b → a ⊔ b = ⊤ :=
  @Disjoint.eq_bot αᵒᵈ _ _ _ _
```

### `codisjoint_hnot_right` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
theorem codisjoint_hnot_right : Codisjoint a (￢a) :=
  codisjoint_iff_le_sup.2 <| sdiff_le_iff.1 (top_sdiff' _).le
```
