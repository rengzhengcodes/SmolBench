# CategoryTheory.Limits.Concrete.widePushout_exists_rep'   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/ConcreteCategory.lean`  

**Ground-truth tail (from k):**
```lean
use i, y
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.0s, verify 0.1s, in=406, out=485)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨i, y, rfl⟩
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 24.8s, verify 0.1s, in=356, out=3977)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨i, y, rfl⟩
```

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 2.7s, verify 0.1s, in=350, out=294)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use i, y
rfl
```
