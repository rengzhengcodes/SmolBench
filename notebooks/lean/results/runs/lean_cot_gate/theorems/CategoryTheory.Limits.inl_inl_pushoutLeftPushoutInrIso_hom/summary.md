# CategoryTheory.Limits.inl_inl_pushoutLeftPushoutInrIso_hom   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`  

**Ground-truth tail (from k):**
```lean
rw [← Category.assoc, ← Iso.eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]
```

**True premises at k:** `CategoryTheory.Category.assoc`, `CategoryTheory.Iso.eq_comp_inv`, `CategoryTheory.Limits.inl_pushoutLeftPushoutInrIso_inv`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 135.7s, verify 0.1s, in=335, out=5436)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw pushout_inl_comp_pushout_left_pushout_inr_iso_hom
```

**lean_error:** tail step 1/1 ('rw pushout_inl_comp_pushout_left_pushout_inr_iso_hom'): <stdin>:1:3: expected '['

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 235.3s, verify 0.2s, in=335, out=9463)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [pushout_left_pushout_inr_hom_inl, category.id_comp]
```

**lean_error:** tail step 1/1 ('rw [pushout_left_pushout_inr_hom_inl, category.id_comp]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 236.5s, verify 0.1s, in=335, out=9536)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [←assoc, pushoutLeftPushoutInrIso_hom_comp_inl]
```

**lean_error:** tail step 1/1 ('simp [←assoc, pushoutLeftPushoutInrIso_hom_comp_inl]'): unknown identifier 'assoc'

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 247.3s, verify 0.2s, in=335, out=10081)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
erw [←category.assoc, iso.hom_inv_id, category.id_comp]
```

**lean_error:** tail step 1/1 ('erw [←category.assoc, iso.hom_inv_id, category.id_comp]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=335, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.2s, verify 0.1s, in=335, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.6s, verify 0.1s, in=335, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pushoutLeftPushoutInrIso_hom_inl_inl]
```

**lean_error:** tail step 1/1 ('simp [pushoutLeftPushoutInrIso_hom_inl_inl]'): unknown identifier 'pushoutLeftPushoutInrIso_hom_inl_inl'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.7s, verify 0.1s, in=335, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pushoutLeftPushoutInrIso_hom_inl_inl]
```

**lean_error:** tail step 1/1 ('simp [pushoutLeftPushoutInrIso_hom_inl_inl]'): unknown identifier 'pushoutLeftPushoutInrIso_hom_inl_inl'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 10.1s, verify 0.1s, in=335, out=276)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 12.3s, verify 0.1s, in=335, out=334)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pushoutLeftPushoutInrIso_hom]
```

**lean_error:** tail step 1/1 ('simp [pushoutLeftPushoutInrIso_hom]'): unknown identifier 'pushoutLeftPushoutInrIso_hom'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 14.4s, verify 0.2s, in=335, out=393)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [pushoutLeftPushoutInrIso_hom_comp_inl, pushout.inl_comp_inl]
```

**lean_error:** tail step 1/1 ('rw [pushoutLeftPushoutInrIso_hom_comp_inl, pushout.inl_comp_inl]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 17.9s, verify 0.1s, in=335, out=503)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pushoutLeftPushoutInrIso_hom]
```

**lean_error:** tail step 1/1 ('simp [pushoutLeftPushoutInrIso_hom]'): unknown identifier 'pushoutLeftPushoutInrIso_hom'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 81.3s, verify 0.1s, in=883, out=3381)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply (eq_comp_inv (pushoutLeftPushoutInrIso f g g')).mpr
exact inl_pushoutLeftPushoutInrIso_inv
```

**lean_error:** tail step 1/2 ("apply (eq_comp_inv (pushoutLeftPushoutInrIso f g g')).mpr"): unknown identifier 'eq_comp_inv'

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 157.5s, verify 0.1s, in=883, out=6249)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iso.eq_comp_inv.mp (inl_pushoutLeftPushoutInrIso_inv.symm)
```

**lean_error:** tail step 1/1 ('exact iso.eq_comp_inv.mp (inl_pushoutLeftPushoutInrIso_inv.symm)'): unknown identifier 'iso.eq_comp_inv.mp'

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 169.9s, verify 0.2s, in=883, out=6703)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [←inl_pushoutLeftPushoutInrIso_inv f g g', Category.assoc, iso.inv_hom_id, Category.id_comp]
```

**lean_error:** tail step 1/1 ("rw [←inl_pushoutLeftPushoutInrIso_inv f g g', Category.assoc, iso.inv_hom_id, Category.id_comp]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 184.8s, verify 0.1s, in=883, out=7305)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw ← inl_pushoutLeftPushoutInrIso_inv f g g'
rw iso.inv_comp_hom
rw Category.comp_id
```

**lean_error:** tail step 1/3 ("rw ← inl_pushoutLeftPushoutInrIso_inv f g g'"): <stdin>:1:3: expected '['

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=883, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.8s, verify 0.5s, in=883, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [← Category.assoc, ← inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/1 ('simp [← Category.assoc, ← inl_pushoutLeftPushoutInrIso_inv]'): tactic 'simp' failed, nested error:

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.3s, verify 0.5s, in=883, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [← Category.assoc, ← inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/1 ('simp [← Category.assoc, ← inl_pushoutLeftPushoutInrIso_inv]'): tactic 'simp' failed, nested error:

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.1s, verify 0.1s, in=883, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Category.assoc, Iso.comp_inv_eq, inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/1 ('simp only [Category.assoc, Iso.comp_inv_eq, inl_pushoutLeftPushoutInrIso_inv]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 15.2s, verify 0.1s, in=883, out=416)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Category.assoc, Iso.eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/1 ('simp only [Category.assoc, Iso.eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 18.1s, verify 0.1s, in=883, out=511)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [eq_comp_inv (pushoutLeftPushoutInrIso f g g'), inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/1 ("simp [eq_comp_inv (pushoutLeftPushoutInrIso f g g'), inl_pushoutLeftPushoutInrIso_inv]"): unknown identifier 'eq_comp_inv'

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 27.1s, verify 0.1s, in=883, out=781)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [← Iso.eq_comp_inv (pushoutLeftPushoutInrIso f g g'),
  CategoryTheory.Category.assoc, Iso.hom_inv_id, inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/2 ("simp only [← Iso.eq_comp_inv (pushoutLeftPushoutInrIso f g g'),"): <stdin>:1:63: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 30.7s, verify 0.2s, in=883, out=906)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Category.assoc, ← eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/1 ('rw [← Category.assoc, ← eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 187.5s, verify 0.2s, in=1920, out=4025)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← inl_pushoutLeftPushoutInrIso_inv f g g', Category.assoc, iso.inv_hom_id, comp_id]
```

**lean_error:** tail step 1/1 ("rw [← inl_pushoutLeftPushoutInrIso_inv f g g', Category.assoc, iso.inv_hom_id, comp_id]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 223.3s, verify 0.1s, in=1920, out=4816)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Iso.eq_comp_inv.2,
exact inl_pushoutLeftPushoutInrIso_inv f g g'
```

**lean_error:** tail step 1/2 ('apply Iso.eq_comp_inv.2,'): <stdin>:1:23: expected end of input

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 281.4s, verify 0.2s, in=1920, out=6282)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← inl_pushoutLeftPushoutInrIso_inv f g g']
rw [← Category.assoc]
simp
```

**lean_error:** tail step 1/3 ("rw [← inl_pushoutLeftPushoutInrIso_inv f g g']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 334.9s, verify 0.2s, in=1920, out=8691)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Category.assoc, ← inl_pushoutLeftPushoutInrIso_inv f g g', Iso.hom_inv_id_assoc, Category.comp_id]
```

**lean_error:** tail step 1/1 ("rw [Category.assoc, ← inl_pushoutLeftPushoutInrIso_inv f g g', Iso.hom_inv_id_assoc, Category.comp_id]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1920, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.8s, verify 0.3s, in=1920, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← Category.assoc]
```

**lean_error:** tail step 1/1 ('simp [← Category.assoc]'): tactic 'simp' failed, nested error:

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 3.2s, verify 0.5s, in=1920, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← Category.assoc, ← inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/1 ('simp [← Category.assoc, ← inl_pushoutLeftPushoutInrIso_inv]'): tactic 'simp' failed, nested error:

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.7s, verify 0.1s, in=1920, out=30)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Category.assoc, ← Iso.eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/1 ('simp only [Category.assoc, ← Iso.eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 25.2s, verify 0.2s, in=1920, out=442)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Category.assoc, ← eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/1 ('rw [Category.assoc, ← eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 26.5s, verify 0.2s, in=1920, out=330)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Iso.eq_comp_inv
```

**lean_error:** tail step 1/1 ('apply Iso.eq_comp_inv'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 27.0s, verify 0.1s, in=1920, out=437)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Category.assoc, Iso.eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/1 ('simp only [Category.assoc, Iso.eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 30.4s, verify 0.2s, in=1920, out=490)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← CategoryTheory.Category.assoc, Iso.eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/1 ('rw [← CategoryTheory.Category.assoc, Iso.eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 101.2s, verify 0.2s, in=1946, out=4146)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Iso.eq_comp_inv
rw inl_pushoutLeftPushoutInrIso_inv
rfl
```

**lean_error:** tail step 1/3 ('apply Iso.eq_comp_inv'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 133.0s, verify 0.1s, in=1946, out=5350)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Iso.eq_comp_inv.mp
symmetry
apply inl_pushoutLeftPushoutInrIso_inv
```

**lean_error:** tail step 1/3 ('apply Iso.eq_comp_inv.mp'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 170.7s, verify 0.2s, in=1946, out=6730)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← inl_pushoutLeftPushoutInrIso_inv f g g', Category.assoc, iso.inv_comp_hom, Category.comp_id]
```

**lean_error:** tail step 1/1 ("rw [← inl_pushoutLeftPushoutInrIso_inv f g g', Category.assoc, iso.inv_comp_hom, Category.comp_id]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 182.9s, verify 0.2s, in=1946, out=7230)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← inl_pushoutLeftPushoutInrIso_inv f g g']
simp
```

**lean_error:** tail step 1/2 ("rw [← inl_pushoutLeftPushoutInrIso_inv f g g']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.9s, verify 0.1s, in=1946, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1946, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=1946, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Category.assoc]
```

**lean_error:** tail step 1/1 ('simp [Category.assoc]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.7s, verify 0.1s, in=1946, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [← Category.assoc, eq_comp_inv, ← pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/1 ('simp [← Category.assoc, eq_comp_inv, ← pushoutLeftPushoutInrIso_inv]'): unknown identifier 'eq_comp_inv'

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 17.6s, verify 0.2s, in=1946, out=496)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Category.assoc, Iso.eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/1 ('rw [← Category.assoc, Iso.eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 22.0s, verify 0.1s, in=1946, out=628)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [CategoryTheory.Category.assoc, CategoryTheory.Iso.eq_comp_inv,
  CategoryTheory.Limits.inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/2 ('simp only [CategoryTheory.Category.assoc, CategoryTheory.Iso.eq_comp_inv,'): <stdin>:1:73: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 26.7s, verify 0.2s, in=1946, out=764)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Category.assoc, Iso.eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/1 ('rw [Category.assoc, Iso.eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 27.4s, verify 0.1s, in=1946, out=791)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Category.assoc, Iso.eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]
```

**lean_error:** tail step 1/1 ('simp only [Category.assoc, Iso.eq_comp_inv, inl_pushoutLeftPushoutInrIso_inv]'): simp made no progress
