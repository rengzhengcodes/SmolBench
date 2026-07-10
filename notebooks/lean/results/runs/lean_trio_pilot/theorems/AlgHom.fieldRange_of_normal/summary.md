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

| rung | llama-31-405b-base | llama-31-405b-lean-lora | nemotron-ultra-253b-base | nemotron-ultra-253b-lean-lora | qwen3-235b-a22b-base | qwen3-235b-a22b-lean-lora |
| --- | --- | --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ | ✘ | ✘ | · |
| `hint:3` | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=594, out=46)

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

### `stepk:1` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.3s, verify 0.3s, in=594, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa only [fieldRange_eq_map] using g.symm.range
```

**lean_error:** tail step 1/1 ('simpa only [fieldRange_eq_map] using g.symm.range'): invalid field 'range', the environment does not contain 'AlgEquiv.range'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 5.6s, verify 0.1s, in=583, out=410)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply fieldRange_eq_of_inverse 
exact g
```

**lean_error:** tail step 1/2 ('apply fieldRange_eq_of_inverse'): unknown identifier 'fieldRange_eq_of_inverse'

### `stepk:1` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=574, out=49)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Set.range_iff
```

**lean_error:** tail step 1/1 ('exact Set.range_iff'): unknown constant 'Set.range_iff'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 127.0s, verify 0.1s, in=547, out=6835)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact inst✝.fieldRange f
```

**lean_error:** tail step 1/1 ('exact inst✝.fieldRange f'): <stdin>:1:10: expected end of input

### `stepk:1` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=547, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.5s, in=1269, out=41)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [AlgHom.fieldRange_eq_map f]
rw [← AlgHom.map_fieldRange f g]
rw [AlgEquiv.fieldRange_eq_top g]
rw [IntermediateField.fieldRange_val]
```

**lean_error:** tail step 2/4 ('rw [← AlgHom.map_fieldRange f g]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.9s, verify 0.2s, in=1269, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← g.fieldRange_eq_map, AlgEquiv.fieldRange_eq_top, IntermediateField.fieldRange_val]
```

**lean_error:** tail step 1/1 ('rw [← g.fieldRange_eq_map, AlgEquiv.fieldRange_eq_top, IntermediateField.fieldRange_val]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=1258, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [fieldRange_val, AlgEquiv.fieldRange_eq_top]
```

**lean_error:** tail step 1/1 ('rw [fieldRange_val, AlgEquiv.fieldRange_eq_top]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=1249, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [fieldRange_eq_map, map_top_eq, fieldRange_val]
exact congr_arg coe (g.fieldRange_eq_top)
```

**lean_error:** tail step 1/2 ('rw [fieldRange_eq_map, map_top_eq, fieldRange_val]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 160.8s, verify 0.1s, in=1222, out=8106)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw ←AlgHom.map_fieldRange g E.val
rw AlgEquiv.fieldRange_eq_top
rw IntermediateField.fieldRange_val
```

**lean_error:** tail step 1/3 ('rw ←AlgHom.map_fieldRange g E.val'): <stdin>:1:3: expected '['

### `hint:2` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 1.0s, verify 0.5s, in=1222, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [AlgEquiv.fieldRange_eq_top, AlgHom.fieldRange_eq_map, IntermediateField.fieldRange_val]
```

**final state (truncated):**
```
F : Type u_1
K : Type u_2
inst✝¹⁹ : Field F
inst✝¹⁸ : Field K
inst✝¹⁷ : Algebra F K
K₁ : Type u_3
...
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.6s, in=2086, out=54)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [AlgHom.fieldRange_eq_map]
rw [IntermediateField.map_id]
rw [g.fieldRange_eq_top]
rw [IntermediateField.top_toSubalgebra]
rw [IntermediateField.toSubalgebra_eq_iff]
rw [IntermediateField.fieldRange_val]
```

**lean_error:** tail step 2/6 ('rw [IntermediateField.map_id]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 2.1s, verify 0.2s, in=2086, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [fieldRange_eq_map, map_eq_top_iff, Set.range_iff_surjective.mpr g.surjective]
```

**lean_error:** tail step 1/1 ('rw [fieldRange_eq_map, map_eq_top_iff, Set.range_iff_surjective.mpr g.surjective]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=2075, out=71)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [fieldRange_val, ←fieldRange_eq_map, map_fieldRange, AlgEquiv.fieldRange_eq_top, map_top, AlgHom.fieldRange_eq_map, map_top]
rw [←fieldRange_eq_map, map_fieldRange, AlgEquiv.fieldRange_eq_top, map_top]
rw [fieldRange_val]
```

**lean_error:** tail step 1/3 ('rw [fieldRange_val, ←fieldRange_eq_map, map_fieldRange, AlgEquiv.fieldRange_eq_top, map_top, AlgHom.fieldRange_eq_map, map_top]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=2066, out=34)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [fieldRange_eq_map, map_top, ← fieldRange_val]
exact congr_arg _ (AlgEquiv.fieldRange_eq_top g)
```

**lean_error:** tail step 1/2 ('rw [fieldRange_eq_map, map_top, ← fieldRange_val]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 155.7s, verify 0.3s, in=2042, out=8320)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [AlgHom.fieldRange_eq_map, IntermediateField.map_map, g.map_top, IntermediateField.fieldRange_val]
```

**lean_error:** tail step 1/1 ('rw [AlgHom.fieldRange_eq_map, IntermediateField.map_map, g.map_top, IntermediateField.fieldRange_val]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=2042, out=46)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [AlgHom.fieldRange_eq_map, AlgHom.map_fieldRange, ← AlgHom.fieldRange_eq_map, AlgEquiv.fieldRange_eq_top,
  IntermediateField.map_top, fieldRange_val]
```

**lean_error:** tail step 1/2 ('rw [AlgHom.fieldRange_eq_map, AlgHom.map_fieldRange, ← AlgHom.fieldRange_eq_map, AlgEquiv.fieldRange_eq_top,'): <stdin>:1:108: unexpected end of input; expected ']'

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.3s, in=2111, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [AlgHom.fieldRange_eq_map, AlgEquiv.fieldRange_eq_top g]
exact IntermediateField.map_id E
```

**lean_error:** tail step 1/2 ('rw [AlgHom.fieldRange_eq_map, AlgEquiv.fieldRange_eq_top g]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.6s, verify 0.2s, in=2111, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using (g : E →ₐ[F] E).fieldRange_eq_map
```

**lean_error:** tail step 1/1 ('simpa using (g : E →ₐ[F] E).fieldRange_eq_map'): type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=2100, out=36)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [fieldRange_eq_map, map_top_eq, fieldRange_val]
exact congr_arg (fun x => x) (g.fieldRange_eq_top)
```

**lean_error:** tail step 1/2 ('rw [fieldRange_eq_map, map_top_eq, fieldRange_val]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.6s, verify 0.2s, in=2091, out=32)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [fieldRange_val, ←fieldRange_eq_map, map_fieldRange, fieldRange_eq_top, map_top, fieldRange_val]
```

**lean_error:** tail step 1/1 ('rw [fieldRange_val, ←fieldRange_eq_map, map_fieldRange, fieldRange_eq_top, map_top, fieldRange_val]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 135.0s, verify 0.1s, in=2067, out=7315)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw AlgHom.map_fieldRange
rw AlgEquiv.fieldRange_eq_top
rw IntermediateField.fieldRange_val
```

**lean_error:** tail step 1/3 ('rw AlgHom.map_fieldRange'): <stdin>:1:3: expected '['

### `noise:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=2067, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [AlgHom.fieldRange_eq_map, AlgHom.map_top]
```

**lean_error:** tail step 1/1 ('rw [AlgHom.fieldRange_eq_map, AlgHom.map_top]'): tactic 'rewrite' failed, equality or iff proof expected
