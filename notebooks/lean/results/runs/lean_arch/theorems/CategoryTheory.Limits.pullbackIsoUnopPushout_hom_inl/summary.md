# CategoryTheory.Limits.pullbackIsoUnopPushout_hom_inl   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Limits/Opposites.lean`  

**Ground-truth tail (from k):**
```lean
rw [← pullbackIsoUnopPushout_inv_fst, Iso.hom_inv_id_assoc]
```

**True premises at k:** `CategoryTheory.Limits.pullbackIsoUnopPushout_inv_fst`, `CategoryTheory.Iso.hom_inv_id_assoc`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✘ | ✓ | ✘ |
| `noise:3` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.8s, verify 0.1s, in=340, out=47)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
erw [pullbackIsoUnopPushout_hom_comp_pullback_inl]
rw [pullback_inl_unop]
rw [unop_comp]
rw [pushout.inl_unop_comp_pullback_inl]
```

**lean_error:** tail step 1/4 ('erw [pullbackIsoUnopPushout_hom_comp_pullback_inl]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=314, out=31)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← unop_comp, pushoutIsoUnopPushout_hom_inl]
simp [pullback.snd_fst_id_assoc]
```

**lean_error:** tail step 1/2 ('rw [← unop_comp, pushoutIsoUnopPushout_hom_inl]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=329, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply pullback.unop_pushout_inl
```

**lean_error:** tail step 1/1 ('apply pullback.unop_pushout_inl'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.2s, in=792, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]
```

**lean_error:** tail step 1/1 ('rw [Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=766, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← CategoryTheory.Limits.pullbackIsoUnopPushout_inv_fst f g, CategoryTheory.Iso.hom_inv_id_assoc]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.3s, in=781, out=45)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← cancel_epi (pullbackIsoUnopPushout f g).inv]
rw [Iso.hom_inv_id]
rw [pullbackIsoUnopPushout_inv_fst]
```

**lean_error:** tail step 2/3 ('rw [Iso.hom_inv_id]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.2s, in=1412, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]
```

**lean_error:** tail step 1/1 ('rw [Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=1387, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← CategoryTheory.Limits.pullbackIsoUnopPushout_inv_fst f g, CategoryTheory.Iso.hom_inv_id_assoc]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.6s, in=1401, out=47)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← cancel_epi (pullbackIsoUnopPushout f g).inv]
rw [← pullbackIsoUnopPushout_inv_fst]
dsimp
rw [Iso.inv_hom_id]
```

**lean_error:** tail step 4/4 ('rw [Iso.inv_hom_id]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.2s, in=1435, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]
```

**lean_error:** tail step 1/1 ('rw [Iso.hom_inv_id_assoc, pullbackIsoUnopPushout_inv_fst]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=1480, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← CategoryTheory.Limits.pullbackIsoUnopPushout_inv_fst f g, CategoryTheory.Iso.hom_inv_id_assoc]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.3s, in=1424, out=47)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← cancel_epi (pullbackIsoUnopPushout f g).inv]
rw [pullbackIsoUnopPushout_inv_fst]
dsimp
rw [Iso.hom_inv_id_assoc]
```

**lean_error:** tail step 3/4 ('dsimp'): dsimp made no progress
