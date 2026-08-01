# CompleteSublattice.coe_sInf'   (k=0, 1 tactics total)

file: `Mathlib/Order/CompleteSublattice.lean`  

**Ground-truth tail (from k):**
```lean
rw [coe_sInf, ← Set.image, sInf_image]
```

**True premises at k:** `CompleteSublattice.coe_sInf`, `Set.image`, `sInf_image`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=283, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sInf_eq_iInf]
simp only [Subtype.coe_iInf]
```

**lean_error:** tail step 1/2 ('rw [sInf_eq_iInf]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=254, out=32)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← f.map_sInf, Subtype.coe_sInf, sInf_image]
simp only [Subtype.coe_mk, iInf_apply]
```

**lean_error:** tail step 1/2 ('rw [← f.map_sInf, Subtype.coe_sInf, sInf_image]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=272, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sInf_def, coe_infᵢ']
```

**lean_error:** tail step 1/1 ("rw [sInf_def, coe_infᵢ']"): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.3s, verify 0.2s, in=775, out=36)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf, ←sInf_image]
congr 1
ext1
simp only [Set.mem_image, CompleteLatticeHom.coe_coe]
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=742, out=39)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CompleteSublattice.coe_sInf]
simp_rw [←Subtype.val_eq_coe, Subtype.val_eq_coe, ←Set.image_eq_image, sInf_image]
```

**lean_error:** tail step 2/2 ('simp_rw [←Subtype.val_eq_coe, Subtype.val_eq_coe, ←Set.image_eq_image, sInf_image]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=764, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image, Set.image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image, Set.image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.8s, verify 0.2s, in=872, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [coe_sInf, ← sInf_image]
congr 
ext
simp
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=839, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [CompleteSublattice.coe_sInf]
simp_rw [←Subtype.coe_image]
rw [sInf_image]
```

**lean_error:** tail step 2/3 ('simp_rw [←Subtype.coe_image]'): simp made no progress

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=861, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image, Set.image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image, Set.image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.0s, verify 0.2s, in=896, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [coe_sInf, ←sInf_image]
congr 
ext
simp
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.2s, in=874, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [CompleteSublattice.coe_sInf]
simp_rw [←Subtype.coe_image]
rw [sInf_image]
```

**lean_error:** tail step 2/3 ('simp_rw [←Subtype.coe_image]'): simp made no progress

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=885, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image, Set.image]
exact (Set.image_eq_range _ _).symm
```

**lean_error:** tail step 1/2 ('rw [coe_sInf, sInf_image, Set.image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
