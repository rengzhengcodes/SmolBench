# CategoryTheory.SemiadditiveOfBinaryBiproducts.add_comp   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Preadditive/OfBiproducts.lean`  

**Ground-truth tail (from k):**
```lean
ext <;> simp
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 | llama-lean-fenced-micro-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=307, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [biprod.desc_comp],
  refl,
```

**lean_error:** tail step 1/2 ('rw [biprod.desc_comp],'): <stdin>:1:21: expected end of input

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.6s, verify 0.1s, in=307, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [biprod.desc_comp]
congr
rfl 
rfl
```

**lean_error:** tail step 1/4 ('rw [biprod.desc_comp]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 0.9s, verify 0.2s, in=307, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
· simp only [biprod.inl_desc, assoc]
· simp only [biprod.inr_desc, assoc]
```

**lean_error:** tail step 2/3 ('· simp only [biprod.inl_desc, assoc]'): unknown identifier 'assoc'

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.1s, verify 0.2s, in=307, out=31)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
· simp only [category.assoc, biprod.inl_desc]
· simp only [category.assoc, biprod.inr_desc]
```

**lean_error:** tail step 2/3 ('· simp only [category.assoc, biprod.inl_desc]'): unknown identifier 'category.assoc'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 0.3s, verify 0.1s, in=307, out=2)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 0.4s, verify 0.1s, in=307, out=2)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 0.5s, verify 0.1s, in=307, out=2)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 0.5s, verify 0.1s, in=307, out=2)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · llama-lean-fenced-micro-r128 · rollout 2 → **lean_error**  (gen 12.0s, verify 0.1s, in=307, out=136)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · llama-lean-fenced-micro-r128 · rollout 1 → **lean_error**  (gen 16.0s, verify 0.1s, in=307, out=228)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · llama-lean-fenced-micro-r128 · rollout 3 → **lean_error**  (gen 17.5s, verify 0.1s, in=307, out=261)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [← cancel_epi (biprod.inl X X), ← cancel_epi (biprod.inr X X), Category.assoc,
  biprod.inl_desc_assoc, biprod.inr_desc_assoc, comp_zero, zero_comp, biprod.inl_desc,
  biprod.inr_desc]
```

**lean_error:** tail step 1/3 ('simp only [← cancel_epi (biprod.inl X X), ← cancel_epi (biprod.inr X X), Category.assoc,'): <stdin>:1:88: unexpected end of input; expected ']'

### `stepk:1` · llama-lean-fenced-micro-r128 · rollout 0 → **lean_error**  (gen 18.2s, verify 0.1s, in=307, out=280)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress
