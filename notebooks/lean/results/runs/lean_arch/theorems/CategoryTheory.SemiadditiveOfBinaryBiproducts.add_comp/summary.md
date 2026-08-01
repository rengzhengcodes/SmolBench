# CategoryTheory.SemiadditiveOfBinaryBiproducts.add_comp   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Preadditive/OfBiproducts.lean`  

**Ground-truth tail (from k):**
```lean
ext <;> simp
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=307, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [biprod.desc_comp_left, biprod.desc_comp_right] 
apply biprod.hom_ext 
simp 
simp
```

**lean_error:** tail step 1/4 ('rw [biprod.desc_comp_left, biprod.desc_comp_right]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.3s, in=280, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext1
  simp
ext1
  simp
```

**lean_error:** tail step 3/4 ('ext1'): no applicable extensionality theorem found for

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=296, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply biprod.hom_ext
simp [biprod.desc_comp]
```

**lean_error:** tail step 1/2 ('apply biprod.hom_ext'): tactic 'apply' failed, failed to unify
