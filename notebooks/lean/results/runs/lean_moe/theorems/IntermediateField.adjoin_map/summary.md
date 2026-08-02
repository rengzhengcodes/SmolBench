# IntermediateField.adjoin_map   (k=3, 4 tactics total)

file: `Mathlib/FieldTheory/Adjoin.lean`  

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

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.4s, verify 0.1s, in=434, out=599)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 93.5s, verify 0.1s, in=394, out=11478)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : ⇑↑f = ⇑f := by
  calc
    ⇑↑f = ⇑(↑f) := rfl
    _ = ↑f := by
      ext x
      <;> rfl
    _ = ⇑f := by
      ext x
      <;> rfl
rw [show Subfield.closure (Set.range ⇑(algebraMap F E') ∪ ⇑↑f '' S) = Subfield.closure (Set.range ⇑(algebraMap F E') ∪ ⇑f '' S) by rw [h]]
<;> rfl
```

**lean_error:** tail step 1/11 ('have h : ⇑↑f = ⇑f := by'): <stdin>:1:23: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.4s, verify 0.1s, in=379, out=564)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```
