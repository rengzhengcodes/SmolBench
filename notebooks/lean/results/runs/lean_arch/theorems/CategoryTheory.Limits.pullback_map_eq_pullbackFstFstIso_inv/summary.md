# CategoryTheory.Limits.pullback_map_eq_pullbackFstFstIso_inv   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/Diagonal.lean`  

**Ground-truth tail (from k):**
```lean
simp only [pullbackFstFstIso_inv, lift_snd_assoc, lift_fst]
```

**True premises at k:** `CategoryTheory.Limits.pullbackFstFstIso_inv`, `CategoryTheory.Limits.pullback.lift_snd_assoc`, `CategoryTheory.Limits.pullback.lift_fst`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.3s, in=444, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [map_eq_pullbackFstFstIso_inv_snd_fst]
apply Category.comp_id
done
```

**lean_error:** tail step 1/3 ('rw [map_eq_pullbackFstFstIso_inv_snd_fst]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=418, out=52)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← cancel_mono i₃]
simp only [Category.assoc, Iso.inv_hom_id_assoc, Category.comp_id]
rw [← pullback.condition, map_snd, map_fst, Category.assoc, Category.assoc]
rfl
```

**lean_error:** tail step 1/4 ('rw [← cancel_mono i₃]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 5.9s, verify 0.1s, in=433, out=346)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply pullback_map_eq_pullbackFstFstIso_inv_snd_fst
```

**lean_error:** tail step 1/1 ('apply pullback_map_eq_pullbackFstFstIso_inv_snd_fst'): unknown identifier 'pullback_map_eq_pullbackFstFstIso_inv_snd_fst'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=891, out=40)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [map_eq_lift, lift_snd_assoc, lift_fst]
exact (pullbackFstFstIso _ _ _ _ _ _ _ _ _).inv_hom_id_assoc _ _
```

**lean_error:** tail step 1/2 ('rw [map_eq_lift, lift_snd_assoc, lift_fst]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=877, out=71)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Category.assoc, Iso.inv_hom_id, Category.comp_id, pullback.map_eq_lift]
simp_rw [pullback.lift_fst, pullback.lift_snd, Category.assoc]
simp only [pullbackFstFstIso_inv_fst, pullbackFstFstIso_inv_snd]
```

**lean_error:** tail step 1/3 ('rw [← Category.assoc, Iso.inv_hom_id, Category.comp_id, pullback.map_eq_lift]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.5s, in=880, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply pullback.hom_ext
apply pullback.lift_fst
apply pullback.lift_snd_assoc
```

**lean_error:** tail step 2/3 ('apply pullback.lift_fst'): tactic 'apply' failed, failed to unify

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=1024, out=40)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [map_eq_lift, lift_snd_assoc, lift_fst]
exact (pullbackFstFstIso _ _ _ _ _ _ _ _ _).inv_hom_id_assoc _ _
```

**lean_error:** tail step 1/2 ('rw [map_eq_lift, lift_snd_assoc, lift_fst]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=1012, out=81)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← Category.assoc, Iso.eq_inv_comp]
ext
· simp only [Category.assoc, pullback.lift_fst, pullbackFstFstIso_inv_fst]
  erw [map_fst]
· simp only [pullback.lift_snd, Category.assoc, pullbackFstFstIso_inv_snd]
  erw [map_snd]
```

**lean_error:** tail step 1/6 ('rw [← Category.assoc, Iso.eq_inv_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.2s, in=1013, out=57)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply pullback.lift_fst
apply pullback.lift_snd_assoc
exact e₁
exact e₂
exact (pullbackFstFstIso f g f' g' i₁ i₂ i₃ e₁ e₂).hom_inv_id
```

**lean_error:** tail step 1/5 ('apply pullback.lift_fst'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.2s, in=1048, out=40)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [map_eq_lift, lift_snd_assoc, lift_fst]
exact (pullbackFstFstIso _ _ _ _ _ _ _ _ _).inv_hom_id_assoc _ _
```

**lean_error:** tail step 1/2 ('rw [map_eq_lift, lift_snd_assoc, lift_fst]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=1049, out=108)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Category.assoc, ← Iso.eq_inv_comp]
ext
· simp only [Category.assoc, pullback.lift_fst, Iso.inv_comp_eq, pullback.lift_fst_assoc, pullbackFstFstIso_inv_fst]
  erw [map_fst]
· simp only [Category.assoc, pullback.lift_snd, Iso.inv_comp_eq, pullback.lift_snd_assoc, pullbackFstFstIso_inv_snd]
  erw [map_snd]
```

**lean_error:** tail step 1/6 ('rw [← Category.assoc, ← Iso.eq_inv_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.5s, in=1037, out=41)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply pullback.hom_ext
apply pullbackFstFstIso_inv
exact pullback.lift_fst _ _ _ ≪≫ pullback.lift_snd _ _ _
```

**lean_error:** tail step 2/3 ('apply pullbackFstFstIso_inv'): tactic 'apply' failed, failed to unify
