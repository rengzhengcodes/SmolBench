# CategoryTheory.SemiadditiveOfBinaryBiproducts.add_comp   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Preadditive/OfBiproducts.lean`  

**Ground-truth tail (from k):**
```lean
ext <;> simp
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.1s, verify 0.1s, in=346, out=752)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext <;> simp [Category.assoc]
```
