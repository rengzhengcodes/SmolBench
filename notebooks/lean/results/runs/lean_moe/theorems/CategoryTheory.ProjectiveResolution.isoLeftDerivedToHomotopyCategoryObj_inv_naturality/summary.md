# CategoryTheory.ProjectiveResolution.isoLeftDerivedToHomotopyCategoryObj_inv_naturality   (k=3, 4 tactics total)

file: `Mathlib/CategoryTheory/Abelian/LeftDerived.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.4s, verify 0.5s, in=736, out=799)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Category.assoc]
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 28.7s, verify 0.1s, in=701, out=3831)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [show (Functor.mapHomotopyCategory F (ComplexShape.down ℕ)).map ((HomotopyCategory.quotient C (ComplexShape.down ℕ)).map φ) = (HomotopyCategory.quotient C (ComplexShape.down ℕ) ⋙ Functor.mapHomotopyCategory F (ComplexShape.down ℕ)).map φ by
  rw [Functor.comp_map]]
<;> rfl
```

**lean_error:** tail step 1/3 ('rw [show (Functor.mapHomotopyCategory F (ComplexShape.down ℕ)).map ((HomotopyCategory.quotient C (ComplexShape.down ℕ)).map φ) = (HomotopyCategory.quotient C (ComplexShape.down ℕ) ⋙ Functor.mapHomotopyCategory F (ComplexShape.down ℕ)).map φ by'): <stdin>:1:243: unexpected end of inpu

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.5s, verify 0.5s, in=674, out=583)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Functor.comp_map]
```
