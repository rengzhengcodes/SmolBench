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

| rung | qwen3-235b-a22b-base | qwen3-lean-goedel | qwen3-lean-leannav | qwen3-lean-real |
| --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 141.0s, verify 0.1s, in=547, out=7653)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [fieldRange_eq_map];
apply g.surjective.range_eq
```

**lean_error:** tail step 1/2 ('rw [fieldRange_eq_map];'): <stdin>:1:22: expected end of input

### `stepk:1` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=547, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [g.toAlgHom, ← AlgEquiv.coe_algHom]
```

**lean_error:** tail step 1/1 ('simp [g.toAlgHom, ← AlgEquiv.coe_algHom]'): invalid 'simp', proposition expected

### `stepk:1` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=547, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=547, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 139.3s, verify 0.2s, in=1222, out=7565)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [AlgHom.fieldRange_eq_map, ← IntermediateField.map_comp, AlgEquiv.fieldRange_eq_top, IntermediateField.map_top]
```

**lean_error:** tail step 1/1 ('rw [AlgHom.fieldRange_eq_map, ← IntermediateField.map_comp, AlgEquiv.fieldRange_eq_top, IntermediateField.map_top]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=1222, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1222, out=37)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [AlgEquiv.fieldRange_eq_top, AlgHom.fieldRange_eq_map, AlgEquiv.coe_toAlgHom,
  AlgHom.map_top]
```

**lean_error:** tail step 1/2 ('simp [AlgEquiv.fieldRange_eq_top, AlgHom.fieldRange_eq_map, AlgEquiv.coe_toAlgHom,'): <stdin>:1:82: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 1.0s, verify 0.3s, in=1222, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [AlgHom.fieldRange_eq_map, AlgHom.map_top]
```

**lean_error:** tail step 1/1 ('rw [AlgHom.fieldRange_eq_map, AlgHom.map_top]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 149.2s, verify 0.2s, in=2042, out=8075)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [AlgHom.fieldRange_eq_map, AlgHom.map_fieldRange, AlgEquiv.fieldRange_eq_top, IntermediateField.fieldRange_val]
```

**lean_error:** tail step 1/1 ('rw [AlgHom.fieldRange_eq_map, AlgHom.map_fieldRange, AlgEquiv.fieldRange_eq_top, IntermediateField.fieldRange_val]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=2042, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:3` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 1.3s, verify 0.3s, in=2042, out=37)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [AlgEquiv.fieldRange_eq_top, AlgHom.fieldRange_eq_map, AlgEquiv.coe_toAlgHom,
  AlgHom.map_top]
```

**lean_error:** tail step 1/2 ('simp [AlgEquiv.fieldRange_eq_top, AlgHom.fieldRange_eq_map, AlgEquiv.coe_toAlgHom,'): <stdin>:1:82: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 2.6s, verify 1.0s, in=2042, out=41)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [AlgHom.fieldRange_eq_map, AlgHom.fieldRange_eq_map, map_top, AlgEquiv.fieldRange_eq_top,
  IntermediateField.map_top, map_top]
```

**lean_error:** tail step 1/2 ('rw [AlgHom.fieldRange_eq_map, AlgHom.fieldRange_eq_map, map_top, AlgEquiv.fieldRange_eq_top,'): <stdin>:1:92: unexpected end of input; expected ']'

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 153.1s, verify 0.2s, in=2067, out=8278)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [AlgHom.fieldRange_eq_map, AlgHom.map_fieldRange, AlgEquiv.fieldRange_eq_top, fieldRange_val]
```

**lean_error:** tail step 1/1 ('rw [AlgHom.fieldRange_eq_map, AlgHom.map_fieldRange, AlgEquiv.fieldRange_eq_top, fieldRange_val]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=2067, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `noise:3` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=2067, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `noise:3` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=2067, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress
