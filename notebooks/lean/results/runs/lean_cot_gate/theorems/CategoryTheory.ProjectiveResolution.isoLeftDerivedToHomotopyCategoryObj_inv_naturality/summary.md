# CategoryTheory.ProjectiveResolution.isoLeftDerivedToHomotopyCategoryObj_inv_naturality   (k=3, 4 tactics total)

file: `Mathlib/CategoryTheory/Abelian/LeftDerived.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✘ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 25.4s, verify 0.3s, in=659, out=1229)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 70.3s, verify 0.3s, in=659, out=3287)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 79.8s, verify 0.3s, in=659, out=3739)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 82.4s, verify 0.3s, in=659, out=3903)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.9s, verify 0.3s, in=659, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.2s, verify 0.4s, in=659, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.6s, verify 0.4s, in=659, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.0s, verify 0.3s, in=659, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 7.7s, verify 0.4s, in=659, out=260)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 8.1s, verify 0.4s, in=659, out=275)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 8.7s, verify 0.1s, in=659, out=293)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [← Functor.mapHomotopyCategory_comp]
```

**lean_error:** tail step 1/1 ('simp only [← Functor.mapHomotopyCategory_comp]'): unknown constant 'CategoryTheory.Functor.mapHomotopyCategory_comp'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 9.8s, verify 0.5s, in=659, out=330)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
aesop_cat
```
