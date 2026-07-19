## Current goal
```
⊢ ⨆ f, map f K ≤ ⨆ f, map f K'
```

## Full tactic state
```
F : Type u_1
K✝ : Type u_2
L : Type u_3
inst✝⁵ : Field F
inst✝⁴ : Field K✝
inst✝³ : Field L
inst✝² : Algebra F K✝
inst✝¹ : Algebra F L
K K' : IntermediateField F L
inst✝ : Normal F L
h : K ≤ K'
⊢ ⨆ f, map f K ≤ ⨆ f, map f K'
```

## Proof so far (1 tactic)
```lean
rw [normalClosure_def', normalClosure_def']
```

## Theorem
`IntermediateField.normalClosure_mono` in `Mathlib/FieldTheory/NormalClosure.lean`

## Premises used in the next tactic
- `iSup_mono`
- `IntermediateField.map_mono`

## Premise signatures
### `iSup_mono` (commanddeclaration)
```lean
@[gcongr]
theorem iSup_mono (h : ∀ i, f i ≤ g i) : iSup f ≤ iSup g
```

### `IntermediateField.map_mono` (commanddeclaration)
```lean
theorem map_mono (f : L →ₐ[K] L') {S T : IntermediateField K L} (h : S ≤ T) :
    S.map f ≤ T.map f
```

## Premise full source (with proof)
### `iSup_mono` (commanddeclaration) at `Mathlib/Order/CompleteLattice.lean`
```lean
@[gcongr]
theorem iSup_mono (h : ∀ i, f i ≤ g i) : iSup f ≤ iSup g :=
  iSup_le fun i => le_iSup_of_le i <| h i
```

### `IntermediateField.map_mono` (commanddeclaration) at `Mathlib/FieldTheory/IntermediateField.lean`
```lean
theorem map_mono (f : L →ₐ[K] L') {S T : IntermediateField K L} (h : S ≤ T) :
    S.map f ≤ T.map f :=
  SetLike.coe_mono (Set.image_subset f h)
```
