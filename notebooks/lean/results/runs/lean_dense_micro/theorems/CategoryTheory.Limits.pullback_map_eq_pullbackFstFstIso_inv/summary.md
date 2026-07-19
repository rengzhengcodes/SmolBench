# CategoryTheory.Limits.pullback_map_eq_pullbackFstFstIso_inv   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/Diagonal.lean`  

**Ground-truth tail (from k):**
```lean
simp only [pullbackFstFstIso_inv, lift_snd_assoc, lift_fst]
```

**True premises at k:** `CategoryTheory.Limits.pullbackFstFstIso_inv`, `CategoryTheory.Limits.pullback.lift_snd_assoc`, `CategoryTheory.Limits.pullback.lift_fst`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✓ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.9s, verify 0.2s, in=444, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [map_eq_pullbackFstFstIso_inv_snd_fst]
simp
```

**lean_error:** tail step 1/2 ('rw [map_eq_pullbackFstFstIso_inv_snd_fst]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=444, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [map_eq_pullbackFstFstIso_inv_snd_fst]
apply Category.comp_id
done
```

**lean_error:** tail step 1/3 ('rw [map_eq_pullbackFstFstIso_inv_snd_fst]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.3s, verify 0.2s, in=444, out=30)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [map_eq_pullbackFstFstIso_inv_snd_fst]
rw [Iso.inv_hom_id]
rw [Category.comp_id]
```

**lean_error:** tail step 1/3 ('rw [map_eq_pullbackFstFstIso_inv_snd_fst]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.8s, verify 0.2s, in=444, out=49)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [map_eq_pullbackFstFstIso_inv_snd_fst]
rw [Iso.inv_hom_id]
rw [Category.assoc]
rw [Iso.inv_hom_id]
rw [Category.id_comp]
rw [Category.id_comp]
```

**lean_error:** tail step 1/6 ('rw [map_eq_pullbackFstFstIso_inv_snd_fst]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=444, out=2)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 0.7s, verify 0.1s, in=444, out=4)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
aesop_cat
```

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **success**  (gen 1.1s, verify 0.1s, in=444, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [map, pullbackFstFstIso]
```

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **success**  (gen 1.2s, verify 0.1s, in=444, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [map, pullbackFstFstIso]
```

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=891, out=41)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [map_eq_lift, lift_snd_assoc, lift_fst]
exact (pullbackFstFstIso _ _ _ _ _ _ _ _ _).inv_naturality_assoc _ _
```

**lean_error:** tail step 1/2 ('rw [map_eq_lift, lift_snd_assoc, lift_fst]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.6s, verify 0.2s, in=891, out=43)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [map_eq_lift, lift_fst_assoc, lift_snd_assoc, Iso.inv_hom_id_assoc]
rw [Iso.inv_hom_id, lift_fst]
rw [lift_snd]
simp only [assoc]
```

**lean_error:** tail step 1/4 ('rw [map_eq_lift, lift_fst_assoc, lift_snd_assoc, Iso.inv_hom_id_assoc]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 2.2s, verify 0.1s, in=891, out=71)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
dsimp [map],
rw [pullback.lift_fst],
simp_rw [Category.assoc],
rw [pullback.lift_snd_assoc],
rw [(pullbackFstFstIso _ _ _ _ _ _ _ _ _).inv_hom_id_assoc],
simp_rw [Category.assoc],
rw [pullbackFstFstIso_inv]
```

**lean_error:** tail step 1/7 ('dsimp [map],'): <stdin>:1:11: expected end of input

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 2.5s, verify 0.1s, in=891, out=87)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [map_eq_pullback_lift, pullback.lift_fst_assoc, pullback.lift_snd_assoc],
  exact (pullbackFstFstIso f g f' g' i₁ i₂ i₃ e₁ e₂).inv ≫ snd ≫ fst,
  apply_instance,
  assumption,
  assumption,
  assumption,
  assumption,
  assumption,
  assumption,
  assumption,
  assumption,
  assumption
```

**lean_error:** tail step 1/12 ('rw [map_eq_pullback_lift, pullback.lift_fst_assoc, pullback.lift_snd_assoc],'): <stdin>:1:75: expected end of input

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **success**  (gen 1.0s, verify 0.1s, in=891, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [pullbackFstFstIso]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=891, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [pullbackFstFstIso, map]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 1.5s, verify 0.1s, in=891, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [pullbackFstFstIso, map, pullback.lift_snd_assoc, pullback.lift_fst]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=891, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [map_eq_lift, pullback.lift_snd_assoc, pullback.lift_fst,
  pullbackFstFstIso_inv, assoc]
```

**lean_error:** tail step 1/2 ('simp_rw [map_eq_lift, pullback.lift_snd_assoc, pullback.lift_fst,'): <stdin>:1:65: unexpected end of input; expected ']'
