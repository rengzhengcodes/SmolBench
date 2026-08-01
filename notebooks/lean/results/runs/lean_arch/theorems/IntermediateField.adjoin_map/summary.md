# IntermediateField.adjoin_map   (k=3, 4 tactics total)

file: `Mathlib/FieldTheory/Adjoin.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **success**  (gen 0.3s, verify 0.4s, in=390, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.2s, in=355, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
simp only [coe_toAlgHom]
rw [Set.image_image]
```

**lean_error:** tail step 2/3 ('simp only [coe_toAlgHom]'): unknown identifier 'coe_toAlgHom'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.3s, verify 0.1s, in=379, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```
