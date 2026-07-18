# CategoryTheory.SemiadditiveOfBinaryBiproducts.add_comp   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Preadditive/OfBiproducts.lean`  

**Ground-truth tail (from k):**
```lean
ext <;> simp
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 112.7s, verify 0.1s, in=280, out=5218)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply biprod.hom_ext; simp [assoc, biprod.inl_comp_desc, biprod.inr_comp_desc]
```

**lean_error:** tail step 1/1 ('apply biprod.hom_ext; simp [assoc, biprod.inl_comp_desc, biprod.inr_comp_desc]'): <stdin>:1:20: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 143.2s, verify 0.1s, in=280, out=6639)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply biprod.hom_ext; simp
```

**lean_error:** tail step 1/1 ('apply biprod.hom_ext; simp'): <stdin>:1:20: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 158.6s, verify 0.1s, in=280, out=7395)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply biprod.desc_unique
· simp
· simp
```

**lean_error:** tail step 1/3 ('apply biprod.desc_unique'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 207.8s, verify 0.1s, in=280, out=9831)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply biprod.hom_ext;
  simp [biprod.ι_desc, comp_assoc]
```

**lean_error:** tail step 1/2 ('apply biprod.hom_ext;'): <stdin>:1:20: expected end of input

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
