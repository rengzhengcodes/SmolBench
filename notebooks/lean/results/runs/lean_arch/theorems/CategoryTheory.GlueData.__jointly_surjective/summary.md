# CategoryTheory.GlueData.ι_jointly_surjective   (k=5, 6 tactics total)

file: `Mathlib/CategoryTheory/GlueData.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨i, y, eq⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=511, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use i,
use y,
exact eq,
```

**lean_error:** tail step 1/3 ('use i,'): <stdin>:1:6: unexpected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **success**  (gen 0.3s, verify 0.1s, in=480, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨i, y, eq⟩
```

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=500, out=32)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use e,
refine' ⟨i, y, _⟩,
rw [← nat_iso.hom_inv_id, ← eq],
simp
```

**lean_error:** tail step 1/4 ('use e,'): <stdin>:1:6: unexpected end of input
