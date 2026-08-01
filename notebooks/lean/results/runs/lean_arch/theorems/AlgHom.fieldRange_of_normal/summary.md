# AlgHom.fieldRange_of_normal   (k=2, 3 tactics total)

file: `Mathlib/FieldTheory/Normal.lean`  

**Ground-truth tail (from k):**
```lean
rw [← show E.val.comp ↑g = f from DFunLike.ext_iff.mpr (f.restrictNormal_commutes E),
  ← AlgHom.map_fieldRange, AlgEquiv.fieldRange_eq_top g, ← AlgHom.fieldRange_eq_map,
  IntermediateField.fieldRange_val]
```

**True premises at k:** `AlgHom.map_fieldRange`, `AlgEquiv.fieldRange_eq_top`, `AlgHom.fieldRange_eq_map`, `IntermediateField.fieldRange_val`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.1s, in=594, out=46)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x,
split,
{ rintro ⟨y, rfl⟩,
  exact y.2 },
{ intro hx,
  have hy := g hx,
  exact ⟨⟨hy, hx⟩, by simp⟩ }
```

**lean_error:** tail step 1/7 ('ext x,'): <stdin>:1:5: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.4s, in=560, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← AlgEquiv.toAlgHom_range g]
exact Subtype.range_val f
```

**lean_error:** tail step 1/2 ('rw [← AlgEquiv.toAlgHom_range g]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 8.4s, verify 0.1s, in=583, out=506)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply fieldRange_eq_of_inverse
exact g
```

**lean_error:** tail step 1/2 ('apply fieldRange_eq_of_inverse'): unknown identifier 'fieldRange_eq_of_inverse'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.5s, in=1269, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [AlgHom.fieldRange_eq_map f]
rw [AlgEquiv.fieldRange_eq_top g]
rw [IntermediateField.fieldRange_val]
```

**lean_error:** tail step 2/3 ('rw [AlgEquiv.fieldRange_eq_top g]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.2s, in=1226, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← AlgHom.fieldRange_eq_map, AlgEquiv.fieldRange_eq_top g, IntermediateField.map_top, Subalgebra.toIntermediateField_top]
```

**lean_error:** tail step 1/1 ('rw [← AlgHom.fieldRange_eq_map, AlgEquiv.fieldRange_eq_top g, IntermediateField.map_top, Subalgebra.toIntermediateField_top]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=1258, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [fieldRange_eq_map, map_top_eq, fieldRange_val]
exact congr_arg coe (g.fieldRange_eq_top)
```

**lean_error:** tail step 1/2 ('rw [fieldRange_eq_map, map_top_eq, fieldRange_val]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.5s, in=2086, out=28)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [AlgHom.fieldRange_eq_map]
rw [IntermediateField.fieldRange_val]
rw [AlgEquiv.fieldRange_eq_top]
```

**lean_error:** tail step 2/3 ('rw [IntermediateField.fieldRange_val]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.3s, in=2035, out=28)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← IntermediateField.fieldRange_val E, ← AlgHom.fieldRange_eq_map, AlgEquiv.fieldRange_eq_top g]
```

**lean_error:** tail step 1/1 ('rw [← IntermediateField.fieldRange_val E, ← AlgHom.fieldRange_eq_map, AlgEquiv.fieldRange_eq_top g]'): tactic 'rewrite' failed, motive is not type correct

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=2075, out=40)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [fieldRange_eq_map, map_top_eq, IntermediateField.coe_top, AlgHom.fieldRange_val]
exact congr_arg coe (g.fieldRange_eq_top)
```

**lean_error:** tail step 1/2 ('rw [fieldRange_eq_map, map_top_eq, IntermediateField.coe_top, AlgHom.fieldRange_val]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.3s, in=2111, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [AlgHom.fieldRange_eq_map, AlgEquiv.fieldRange_eq_top g]
exact IntermediateField.map_id E
```

**lean_error:** tail step 1/2 ('rw [AlgHom.fieldRange_eq_map, AlgEquiv.fieldRange_eq_top g]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.6s, in=2162, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← IntermediateField.fieldRange_val]
rw [AlgHom.fieldRange_eq_map, ← AlgEquiv.fieldRange_eq_top g]
rfl
```

**lean_error:** tail step 1/3 ('rw [← IntermediateField.fieldRange_val]'): tactic 'rewrite' failed, pattern is a metavariable

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=2100, out=40)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [fieldRange_eq_map, map_top, AlgEquiv.fieldRange_eq_top, fieldRange_val]
exact congr_arg Subtype.val (g.fieldRange_eq_top)
```

**lean_error:** tail step 1/2 ('rw [fieldRange_eq_map, map_top, AlgEquiv.fieldRange_eq_top, fieldRange_val]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
