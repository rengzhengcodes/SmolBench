# CategoryTheory.Limits.biproduct.lift_desc   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Preadditive/Biproducts.lean`  

**Ground-truth tail (from k):**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, biproduct.ι_π_assoc, comp_dite,
  dite_comp]
```

**True premises at k:** `CategoryTheory.Limits.biproduct.lift_eq`, `CategoryTheory.Limits.biproduct.desc_eq`, `CategoryTheory.Preadditive.comp_sum`, `CategoryTheory.Preadditive.sum_comp`, `CategoryTheory.Limits.biproduct.ι_π_assoc`, `CategoryTheory.comp_dite`, `CategoryTheory.dite_comp`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | · · · ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | · · · ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | · · · ✘ | ✘ · ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 176.8s, verify 0.1s, in=295, out=6930)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have key := preadditive.biproduct.ι_π_eq_self f
rw [← category.id_comp (desc h), key]
rw [category.assoc, finset.sum_comp, finset.comp_sum]
apply finset.sum_congr rfl
  intros j -
  rw [biproduct.fac, biproduct.fac']
```

**lean_error:** tail step 1/6 ('have key := preadditive.biproduct.ι_π_eq_self f'): internal exception #7

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 202.2s, verify 0.1s, in=295, out=8044)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
preadditive.lift_desc g h
```

**lean_error:** tail step 1/1 ('preadditive.lift_desc g h'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 249.6s, verify 0.1s, in=295, out=10216)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact biproduct.lift_desc g h
```

**lean_error:** tail step 1/1 ('exact biproduct.lift_desc g h'): function expected at

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 294.3s, verify 0.1s, in=295, out=12279)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [lift_eq_sum_ι_comp, desc_eq_sum_comp_π]
rw [Preadditive.comp_sum, Preadditive.sum_comp]
apply Finset.sum_congr rfl
intros j k
rw [assoc, biproduct.π_ι, if_pos, comp_id, if_false, comp_zero]
split_ifs with h
subst h
refl
rw zero_comp
```

**lean_error:** tail step 1/9 ('rw [lift_eq_sum_ι_comp, desc_eq_sum_comp_π]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.1s, verify 0.1s, in=295, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [lift_ι, π_desc]
```

**lean_error:** tail step 1/1 ('simp [lift_ι, π_desc]'): unknown identifier 'lift_ι'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=295, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [lift_ι, π_desc]
```

**lean_error:** tail step 1/1 ('simp [lift_ι, π_desc]'): unknown identifier 'lift_ι'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=295, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [← cancel_epi biprod.ι, ← assoc]
```

**lean_error:** tail step 1/1 ('simp [← cancel_epi biprod.ι, ← assoc]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.3s, verify 0.1s, in=295, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Preadditive.sum_comp, Preadditive.comp_sum]
```

**lean_error:** tail step 1/1 ('simp [Preadditive.sum_comp, Preadditive.comp_sum]'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 5.5s, verify 0.1s, in=295, out=153)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [sum_comp_desc]
```

**lean_error:** tail step 1/1 ('simp only [sum_comp_desc]'): unknown identifier 'sum_comp_desc'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 13.6s, verify 0.1s, in=295, out=357)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [biprod.lift_desc, biprod_fan.mk_π_lift, biprod_cofan.ι_desc]
```

**lean_error:** tail step 1/1 ('simp [biprod.lift_desc, biprod_fan.mk_π_lift, biprod_cofan.ι_desc]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 64.3s, verify 0.1s, in=295, out=2082)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [← assoc, Preadditive.desc_comp, Preadditive.comp_lift]
```

**lean_error:** tail step 1/1 ('simp only [← assoc, Preadditive.desc_comp, Preadditive.comp_lift]'): unknown identifier 'assoc'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 898.6s, verify 0.1s, in=295, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← lift_ι, ← π_desc, ← Finset.sum_ite_eq, ← Finset.sum_ite_eq, ← Finset.sum_ite_eq,
  Finset.sum_mul_boole, Finset.sum_mul_boole, Finset.sum_mul_boole, lift_eq, desc_eq,
  Finset.sum_comp, Finset.comp_sum, ← Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp, Finset.sum_comp,
  Fin
```

**lean_error:** tail step 1/1246 ('rw [← lift_ι, ← π_desc, ← Finset.sum_ite_eq, ← Finset.sum_ite_eq, ← Finset.sum_ite_eq,'): <stdin>:1:86: unexpected end of input; expected ']'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 138.2s, verify 0.3s, in=1782, out=5451)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq]
rw [CategoryTheory.Preadditive.comp_sum, CategoryTheory.Preadditive.sum_comp]
simp only [biproduct.ι_π, comp_dite, Finset.sum_dite_eq, Category.assoc, if_true]
```

**lean_error:** tail step 2/3 ('rw [CategoryTheory.Preadditive.comp_sum, CategoryTheory.Preadditive.sum_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 160.2s, verify 0.4s, in=1782, out=6261)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [lift_eq, desc_eq]
rw [sum_comp]
rw [comp_sum]
simp only [biproduct.ι_π, comp_dite, dite_comp, Category.assoc, comp_zero, id_comp, zero_comp]
rw [Finset.sum_dite_eq']
simp only [Finset.mem_univ, if_true, Finset.sum_singleton]
```

**lean_error:** tail step 3/6 ('rw [comp_sum]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 169.2s, verify 0.3s, in=1782, out=6627)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq]
rw [sum_comp, comp_sum]
simp only [Category.assoc]
rw [biproduct.ι_π]
simp [Finset.sum_dite_eq, if_true, comp_id, comp_zero]
```

**lean_error:** tail step 2/5 ('rw [sum_comp, comp_sum]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 283.7s, verify 0.3s, in=1782, out=11719)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq]
rw [sum_comp, comp_sum]
simp only [biproduct.ι_comp_π, comp_dite, dite_comp, Category.assoc, Finset.sum_dite_eq', Finset.mem_univ, if_true]
```

**lean_error:** tail step 2/3 ('rw [sum_comp, comp_sum]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 2.2s, verify 0.2s, in=1782, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp]
```

**final state (truncated):**
```
C : Type u
inst✝³ : Category.{v, u} C
inst✝² : Preadditive C
J : Type
inst✝¹ : Fintype J
f : J → C
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 2.4s, verify 0.2s, in=1782, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp]
```

**final state (truncated):**
```
C : Type u
inst✝³ : Category.{v, u} C
inst✝² : Preadditive C
J : Type
inst✝¹ : Fintype J
f : J → C
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 2.9s, verify 0.2s, in=1782, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp]
```

**final state (truncated):**
```
C : Type u
inst✝³ : Category.{v, u} C
inst✝² : Preadditive C
J : Type
inst✝¹ : Fintype J
f : J → C
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 3.4s, verify 0.1s, in=1782, out=49)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, Finset.sum_product, Finset.sum_comm,
  Category.assoc, biproduct.ι_π_assoc]
```

**lean_error:** tail step 1/2 ('simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, Finset.sum_product, Finset.sum_comm,'): <stdin>:1:100: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 14.7s, verify 0.1s, in=1782, out=406)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
aesop_cat [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp,
  biproduct.ι_π_assoc, comp_dite, dite_comp]
```

**lean_error:** tail step 1/2 ('aesop_cat [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp,'): <stdin>:1:10: expected end of input

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 15.1s, verify 0.1s, in=1782, out=423)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, Category.assoc, comp_sum, sum_comp, comp_dite,
  dite_comp, Finset.sum_dite_eq']
```

**lean_error:** tail step 1/2 ('simp [biproduct.lift_eq, biproduct.desc_eq, Category.assoc, comp_sum, sum_comp, comp_dite,'): <stdin>:1:90: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 15.7s, verify 0.1s, in=1782, out=422)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, biproduct.ι_π_assoc,
  comp_dite, dite_comp]
```

**lean_error:** tail step 1/2 ('simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, biproduct.ι_π_assoc,'): <stdin>:1:84: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 17.3s, verify 0.1s, in=1782, out=464)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [lift_eq, desc_eq, comp_sum, sum_comp, Category.assoc, dite_comp,
  biproduct.ι_π_assoc, comp_dite, Finset.sum_dite_eq', Finset.mem_univ, eqToHom_refl,
  Category.comp_id, if_true]
```

**lean_error:** tail step 1/3 ('simp only [lift_eq, desc_eq, comp_sum, sum_comp, Category.assoc, dite_comp,'): <stdin>:1:75: unexpected end of input; expected ']'

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 250.3s, verify 0.3s, in=2524, out=4121)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq]
rw [sum_comp, comp_sum]
congr
ext
rw [biproduct.ι_π, comp_dite, dite_comp]
simp only [Category.id_comp, Category.comp_id, comp_zero, zero_comp]
rw [Finset.sum_dite_eq']
simp [if_true]
```

**lean_error:** tail step 2/8 ('rw [sum_comp, comp_sum]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 260.3s, verify 0.3s, in=2524, out=7149)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq]
simp only [sum_comp, comp_sum]
simp only [biproduct.ι_π, comp_dite]
simp only [Finset.sum_dite_eq']
simp only [if_true, Category.comp_id, comp_zero, zero_comp]
```

**lean_error:** tail step 3/5 ('simp only [biproduct.ι_π, comp_dite]'): simp made no progress

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 270.1s, verify 0.4s, in=2524, out=5677)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq]
rw [sum_comp]
rw [comp_sum]
simp only [biproduct.ι_π, comp_dite, comp_zero, Finset.sum_dite_eq, Category.id_comp]
```

**lean_error:** tail step 3/4 ('rw [comp_sum]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 301.6s, verify 0.3s, in=2524, out=6712)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq]
rw [sum_comp, comp_sum]
simp only [biproduct.ι_π, comp_dite, dite_comp, Finset.sum_dite_eq, Finset.mem_univ, if_true, Category.comp_id, Category.id_comp]
```

**lean_error:** tail step 2/3 ('rw [sum_comp, comp_sum]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 3.5s, verify 0.2s, in=2524, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp]
```

**final state (truncated):**
```
C : Type u
inst✝³ : Category.{v, u} C
inst✝² : Preadditive C
J : Type
inst✝¹ : Fintype J
f : J → C
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 3.9s, verify 0.2s, in=2524, out=34)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, biproduct.ι_π_assoc]
```

**final state (truncated):**
```
C : Type u
inst✝³ : Category.{v, u} C
inst✝² : Preadditive C
J : Type
inst✝¹ : Fintype J
f : J → C
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 4.1s, verify 0.2s, in=2524, out=34)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, biproduct.ι_π_assoc]
```

**final state (truncated):**
```
C : Type u
inst✝³ : Category.{v, u} C
inst✝² : Preadditive C
J : Type
inst✝¹ : Fintype J
f : J → C
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 4.4s, verify 0.1s, in=2524, out=51)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, biproduct.ι_π_assoc,
  Finset.sum_dite_eq', Finset.mem_univ, if_true]
```

**lean_error:** tail step 1/2 ('simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, biproduct.ι_π_assoc,'): <stdin>:1:84: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 23.9s, verify 0.1s, in=2524, out=534)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, biproduct.ι_π_assoc,
  comp_dite, Category.assoc, comp_zero, Finset.sum_dite_eq', Finset.mem_univ, eqToHom_refl,
  Category.comp_id, if_true]
```

**lean_error:** tail step 1/3 ('simp only [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, biproduct.ι_π_assoc,'): <stdin>:1:89: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 28.7s, verify 0.1s, in=2524, out=485)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
aesop_cat [simp] (rule_sets [CategoryTheory, Finset, Decidable, Prop, CategoryTheory.Preadditive])
```

**lean_error:** tail step 1/1 ('aesop_cat [simp] (rule_sets [CategoryTheory, Finset, Decidable, Prop, CategoryTheory.Preadditive])'): <stdin>:1:10: expected end of input

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 30.3s, verify 0.1s, in=2524, out=517)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [biproduct.lift_eq, biproduct.desc_eq, comp_sum, biproduct.ι_π_assoc, dite_comp,
  sum_comp, comp_dite, Finset.sum_dite_eq', Finset.mem_univ, eqToHom_refl, Category.assoc,
  comp_zero, Category.comp_id, if_true]
```

**lean_error:** tail step 1/3 ('simp only [biproduct.lift_eq, biproduct.desc_eq, comp_sum, biproduct.ι_π_assoc, dite_comp,'): <stdin>:1:90: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 32.5s, verify 0.1s, in=2524, out=560)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [biproduct.lift_eq, biproduct.desc_eq, comp_sum, biproduct.ι_π_assoc, comp_dite,
  Finset.sum_dite_eq', Finset.mem_univ, eqToHom_refl, Category.assoc, comp_zero, dite_comp,
  Category.comp_id, if_true, sum_comp]
```

**lean_error:** tail step 1/3 ('simp only [biproduct.lift_eq, biproduct.desc_eq, comp_sum, biproduct.ι_π_assoc, comp_dite,'): <stdin>:1:90: unexpected end of input; expected ']'

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 87.4s, verify 0.3s, in=2547, out=3547)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq]
rw [sum_comp, comp_sum]
simp [biproduct.ι_π, comp_dite, Finset.sum_dite_eq']
```

**lean_error:** tail step 2/3 ('rw [sum_comp, comp_sum]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 150.9s, verify 0.3s, in=2547, out=5917)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq]
rw [sum_comp, comp_sum]
simp only [biproduct.ι_π, Category.assoc, comp_dite, dite_comp]
rw [Finset.sum_dite_eq']
simp only [Finset.mem_univ, if_true, Category.id_comp, Category.comp_id]
```

**lean_error:** tail step 2/5 ('rw [sum_comp, comp_sum]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 156.7s, verify 0.3s, in=2547, out=6126)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq]
rw [sum_comp, comp_sum]
simp only [Category.assoc, biproduct.ι_π, comp_dite, dite_comp, if_true, Finset.sum_dite_eq']
```

**lean_error:** tail step 2/3 ('rw [sum_comp, comp_sum]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 184.2s, verify 0.2s, in=2547, out=7213)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [biproduct.lift_eq, biproduct.desc_eq]
simp [sum_comp, comp_sum, biproduct.ι_π, comp_dite, dite_comp, comp_id, zero_comp]
rw [Finset.sum_dite_eq']
simp [if_true]
```

**lean_error:** tail step 2/4 ('simp [sum_comp, comp_sum, biproduct.ι_π, comp_dite, dite_comp, comp_id, zero_comp]'): unknown identifier 'comp_id'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 2.6s, verify 0.2s, in=2547, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp]
```

**final state (truncated):**
```
C : Type u
inst✝³ : Category.{v, u} C
inst✝² : Preadditive C
J : Type
inst✝¹ : Fintype J
f : J → C
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 2.7s, verify 0.2s, in=2547, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp]
```

**final state (truncated):**
```
C : Type u
inst✝³ : Category.{v, u} C
inst✝² : Preadditive C
J : Type
inst✝¹ : Fintype J
f : J → C
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 3.1s, verify 0.2s, in=2547, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, sum_comp, comp_sum, ← Finset.sum_product]
```

**final state (truncated):**
```
C : Type u
inst✝³ : Category.{v, u} C
inst✝² : Preadditive C
J : Type
inst✝¹ : Fintype J
f : J → C
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 3.2s, verify 0.1s, in=2547, out=35)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, Finset.sum_product, Finset.sum_mul]
```

**lean_error:** tail step 1/1 ('simp [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, Finset.sum_product, Finset.sum_mul]'): unknown constant 'Finset.sum_mul'

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 15.3s, verify 0.1s, in=2547, out=406)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, biproduct.ι_π,
  Category.assoc, comp_dite, Finset.sum_dite_eq', Finset.mem_univ, dite_comp]
```

**lean_error:** tail step 1/2 ('simp only [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, biproduct.ι_π,'): <stdin>:1:83: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 15.4s, verify 0.1s, in=2547, out=409)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [lift_eq, desc_eq, sum_comp, comp_sum, ι_π, comp_dite, dite_comp]
```

**final state (truncated):**
```
C : Type u
inst✝³ : Category.{v, u} C
inst✝² : Preadditive C
J : Type
inst✝¹ : Fintype J
f : J → C
...
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 20.3s, verify 0.1s, in=2547, out=553)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [lift_eq, desc_eq, sum_comp, comp_sum, ι_π_assoc, comp_dite, dite_comp,
  Finset.sum_dite_eq', Finset.mem_univ, eqToHom_refl, Category.assoc, comp_zero, if_true]
```

**lean_error:** tail step 1/2 ('simp only [lift_eq, desc_eq, sum_comp, comp_sum, ι_π_assoc, comp_dite, dite_comp,'): <stdin>:1:81: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 22.6s, verify 0.1s, in=2547, out=623)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, biproduct.ι_π_assoc,
  Category.assoc, comp_dite, dite_comp, Finset.sum_dite_eq', Finset.mem_univ, eqToHom_refl,
  Category.comp_id, if_true]
```

**lean_error:** tail step 1/3 ('simp only [biproduct.lift_eq, biproduct.desc_eq, comp_sum, sum_comp, biproduct.ι_π_assoc,'): <stdin>:1:89: unexpected end of input; expected ']'
