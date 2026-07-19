# CategoryTheory.GlueData.ι_jointly_surjective   (k=5, 6 tactics total)

file: `Mathlib/CategoryTheory/GlueData.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨i, y, eq⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✓ ✘ ✘ ✓ | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 50.7s, verify 0.2s, in=480, out=2171)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use i, y
exact eq
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 51.1s, verify 0.1s, in=480, out=2191)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
existsi [i, y]
exact eq.symm
```

**lean_error:** tail step 1/2 ('existsi [i, y]'): application type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 58.4s, verify 0.1s, in=480, out=2518)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
existsi [i, y], exact eq
```

**lean_error:** tail step 1/1 ('existsi [i, y], exact eq'): application type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 63.7s, verify 0.2s, in=480, out=2746)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
use i, y
exact eq
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.6s, verify 0.1s, in=480, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨i, y, eq.trans (Category.comp_id _)⟩
```

**lean_error:** tail step 1/1 ('exact ⟨i, y, eq.trans (Category.comp_id _)⟩'): application type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.7s, verify 0.1s, in=480, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨i, y, eq.trans (Category.id_comp _)⟩
```

**lean_error:** tail step 1/1 ('exact ⟨i, y, eq.trans (Category.id_comp _)⟩'): application type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.8s, verify 0.1s, in=480, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨i, y, eq.trans (Category.id_comp x)⟩
```

**lean_error:** tail step 1/1 ('exact ⟨i, y, eq.trans (Category.id_comp x)⟩'): application type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=480, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨i, y, eq.trans (Category.id_comp x).symm⟩
```

**lean_error:** tail step 1/1 ('exact ⟨i, y, eq.trans (Category.id_comp x).symm⟩'): application type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 4.4s, verify 0.1s, in=480, out=160)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨i, y, eq⟩
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 5.8s, verify 0.1s, in=480, out=216)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨i, y, eq⟩
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 6.0s, verify 0.1s, in=480, out=226)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa only [Category.id_comp] using ⟨i, y, eq⟩
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 6.3s, verify 0.4s, in=480, out=238)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨i, y, eq.trans (Category.comp_id _)⟩
```

**lean_error:** tail step 1/1 ('exact ⟨i, y, eq.trans (Category.comp_id _)⟩'): application type mismatch
