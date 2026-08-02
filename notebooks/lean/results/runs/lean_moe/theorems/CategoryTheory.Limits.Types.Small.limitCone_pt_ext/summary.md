# CategoryTheory.Limits.Types.Small.limitCone_pt_ext   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Types.lean`  

**Ground-truth tail (from k):**
```lean
aesop
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.7s, verify 0.1s, in=323, out=629)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (equivShrink (↑(Functor.sections F))).symm.injective w
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 72.7s, verify 0.2s, in=275, out=9428)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply (equivShrink (Functor.sections F)).symm.injective
exact w
```

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.6s, verify 0.2s, in=273, out=596)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply (equivShrink ↑(Functor.sections F)).symm.injective
exact w
```
