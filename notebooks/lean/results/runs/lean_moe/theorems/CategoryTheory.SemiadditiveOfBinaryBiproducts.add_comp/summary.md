# CategoryTheory.SemiadditiveOfBinaryBiproducts.add_comp   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Preadditive/OfBiproducts.lean`  

**Ground-truth tail (from k):**
```lean
ext <;> simp
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.1s, verify 0.1s, in=346, out=752)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext <;> simp [Category.assoc]
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 122.1s, verify 0.1s, in=292, out=16502)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Function.comp_def]
apply biprod.ext
· simp [assoc, biprod.inl_desc]
· simp [assoc, biprod.inr_desc]
```

**lean_error:** tail step 1/4 ('simp [Function.comp_def]'): simp made no progress

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.0s, verify 0.1s, in=292, out=562)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply biprod.desc_ext
constructor
· simp [biprod.desc_fst, Category.assoc]
· simp [biprod.desc_snd, Category.assoc]
```

**lean_error:** tail step 1/4 ('apply biprod.desc_ext'): invalid field notation, type is not of the form (C ...) where C is a constant
