# CategoryTheory.SemiadditiveOfBinaryBiproducts.add_comp   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Preadditive/OfBiproducts.lean`  

**Ground-truth tail (from k):**
```lean
ext <;> simp
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.3s, verify 0.1s, in=280, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.3s, verify 0.1s, in=280, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.4s, verify 0.1s, in=280, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [biprod.desc_comp]
```

**lean_error:** tail step 1/1 ('simp [biprod.desc_comp]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.5s, verify 0.1s, in=280, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [biprod.desc_eq_zero_iff]
```

**lean_error:** tail step 1/1 ('simp [biprod.desc_eq_zero_iff]'): invalid field notation, type is not of the form (C ...) where C is a constant
