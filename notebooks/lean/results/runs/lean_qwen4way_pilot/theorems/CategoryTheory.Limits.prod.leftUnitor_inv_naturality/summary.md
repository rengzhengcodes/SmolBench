# CategoryTheory.Limits.prod.leftUnitor_inv_naturality   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/BinaryProducts.lean`  

**Ground-truth tail (from k):**
```lean
rw [Iso.inv_comp_eq, ← Category.assoc, Iso.eq_comp_inv, prod.leftUnitor_hom_naturality]
```

**True premises at k:** `CategoryTheory.Iso.inv_comp_eq`, `CategoryTheory.Category.assoc`, `CategoryTheory.Iso.eq_comp_inv`, `CategoryTheory.Limits.prod.leftUnitor_hom_naturality`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-goedel | qwen3-lean-leannav | qwen3-lean-real |
| --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✓ | ✓ | ✓ |
| `hint:2` | ✘ | ✘ | ✓ | ✓ |
| `hint:3` | ✘ | ✘ | ✓ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 207.3s, verify 0.1s, in=279, out=11372)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
  terminal.from_unique
  simp [leftUnitor_inv_comp_prod_right, category.id_comp]
  simp [leftUnitor_inv_comp_prod_right, category.id_comp]
```

**lean_error:** tail step 1/4 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-lean-goedel · rollout 0 → **success**  (gen 70.3s, verify 0.1s, in=279, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-leannav · rollout 0 → **success**  (gen 8.2s, verify 0.1s, in=279, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-real · rollout 0 → **success**  (gen 9.2s, verify 0.1s, in=279, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 80.6s, verify 0.1s, in=937, out=4016)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply inv_comp_eq
rw [prod.leftUnitor_hom_naturality]
rw [Category.assoc]
rw [Iso.hom_inv_id]
rw [Category.id_comp]
```

**lean_error:** tail step 1/5 ('apply inv_comp_eq'): unknown identifier 'inv_comp_eq'

### `hint:2` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 16.6s, verify 0.1s, in=937, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [inv_comp_eq, leftUnitor_hom_naturality, Category.id_comp]
```

**lean_error:** tail step 1/1 ('simp only [inv_comp_eq, leftUnitor_hom_naturality, Category.id_comp]'): unknown identifier 'inv_comp_eq'

### `hint:2` · qwen3-lean-leannav · rollout 0 → **success**  (gen 8.7s, verify 0.1s, in=937, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [← Iso.inv_comp_eq, ← Iso.eq_comp_inv, prod.leftUnitor_hom_naturality]
```

### `hint:2` · qwen3-lean-real · rollout 0 → **success**  (gen 9.5s, verify 0.1s, in=937, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [← Iso.inv_comp_eq, ← Iso.eq_comp_inv, prod.leftUnitor_hom_naturality]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 108.6s, verify 0.1s, in=1112, out=5630)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply (inv_comp_eq (leftUnitor X)).mpr
apply (eq_comp_inv (leftUnitor Y)).mp
exact leftUnitor_hom_naturality f
```

**lean_error:** tail step 1/3 ('apply (inv_comp_eq (leftUnitor X)).mpr'): unknown identifier 'inv_comp_eq'

### `hint:3` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 17.3s, verify 0.7s, in=1112, out=35)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Category.assoc, Iso.inv_hom_id, comp_id, ← inv_comp_eq,
  prod.leftUnitor_hom_naturality]
```

**lean_error:** tail step 1/2 ('simp only [Category.assoc, Iso.inv_hom_id, comp_id, ← inv_comp_eq,'): <stdin>:1:66: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-leannav · rollout 0 → **success**  (gen 70.8s, verify 0.1s, in=1112, out=28)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← Iso.inv_comp_eq, ← Iso.eq_comp_inv, prod.leftUnitor_hom_naturality]
```

### `hint:3` · qwen3-lean-real · rollout 0 → **success**  (gen 9.7s, verify 0.1s, in=1112, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← Iso.inv_comp_eq, ← Category.assoc, ← Iso.eq_comp_inv, prod.leftUnitor_hom_naturality]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 91.4s, verify 0.1s, in=1134, out=4610)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [inv_comp_eq, eq_comp_inv]
exact leftUnitor_hom_naturality f
```

**lean_error:** tail step 1/2 ('rw [inv_comp_eq, eq_comp_inv]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 16.8s, verify 0.5s, in=1134, out=34)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [← iso.inv_comp_eq, iso.eq_comp_inv, prod.leftUnitor_hom_naturality, Iso.hom_inv_id_assoc]
```

**lean_error:** tail step 1/1 ('simp only [← iso.inv_comp_eq, iso.eq_comp_inv, prod.leftUnitor_hom_naturality, Iso.hom_inv_id_assoc]'): unknown identifier 'iso.inv_comp_eq'

### `noise:3` · qwen3-lean-leannav · rollout 0 → **success**  (gen 8.6s, verify 0.1s, in=1134, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [← Iso.inv_comp_eq, ← Iso.eq_comp_inv, prod.leftUnitor_hom_naturality]
```

### `noise:3` · qwen3-lean-real · rollout 0 → **success**  (gen 9.8s, verify 0.1s, in=1134, out=33)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [← Iso.inv_comp_eq, ← Category.assoc, ← Iso.eq_comp_inv, prod.leftUnitor_hom_naturality]
```
