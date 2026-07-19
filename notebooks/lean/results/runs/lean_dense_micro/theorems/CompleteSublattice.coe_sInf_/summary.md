# CompleteSublattice.coe_sInf'   (k=0, 1 tactics total)

file: `Mathlib/Order/CompleteSublattice.lean`  

**Ground-truth tail (from k):**
```lean
rw [coe_sInf, ← Set.image, sInf_image]
```

**True premises at k:** `CompleteSublattice.coe_sInf`, `Set.image`, `sInf_image`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✘ | ✘ ✓ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.3s, verify 0.1s, in=283, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sInf, coeInf]
congr
ext
simp
```

**lean_error:** tail step 1/4 ('rw [sInf, coeInf]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.6s, verify 0.1s, in=283, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sInf_eq_iInf]
congr
ext1
rw [CompleteLatticeHom.map_iInf]
```

**lean_error:** tail step 1/4 ('rw [sInf_eq_iInf]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=283, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sInf_eq_iInf]
rw [iInf_subtype]
congr 
rw [Subtype.coe_iInf]
```

**lean_error:** tail step 1/4 ('rw [sInf_eq_iInf]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 2.5s, verify 0.1s, in=283, out=32)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sInf_eq_iInf]
rw [iInf_subtype]
congr
ext N
rw [CompleteLatticeHom.coe_iInf]
```

**lean_error:** tail step 1/5 ('rw [sInf_eq_iInf]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **incomplete**  (gen 0.9s, verify 0.2s, in=283, out=2)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
inst✝¹ : CompleteLattice α
inst✝ : CompleteLattice β
f : CompleteLatticeHom α β
L : CompleteSublattice α
...
```

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.3s, verify 0.1s, in=283, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [CompleteLatticeHom.sInf_eq, sInf_image]
```

**lean_error:** tail step 1/1 ('simp [CompleteLatticeHom.sInf_eq, sInf_image]'): unknown constant 'CompleteLatticeHom.sInf_eq'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.1s, in=283, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [← sInf_image, ← f.coe_sInf]
```

**lean_error:** tail step 1/1 ('simp [← sInf_image, ← f.coe_sInf]'): invalid field 'coe_sInf', the environment does not contain 'CompleteLatticeHom.coe_sInf'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.5s, verify 0.1s, in=283, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [← f.coe_sInf, ← f.coe_Inf]
```

**lean_error:** tail step 1/1 ('simp [← f.coe_sInf, ← f.coe_Inf]'): invalid field 'coe_sInf', the environment does not contain 'CompleteLatticeHom.coe_sInf'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.4s, verify 0.2s, in=775, out=36)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf, ←sInf_image]
congr 1
ext1
simp only [Set.mem_image, CompleteLatticeHom.coe_coe]
```

### `hint:2` · llama-31-405b-base · rollout 2 → **success**  (gen 1.7s, verify 0.2s, in=775, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf, ←sInf_image]
rfl
```

### `hint:2` · llama-31-405b-base · rollout 3 → **success**  (gen 1.9s, verify 0.3s, in=775, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CompleteSublattice.coe_sInf]
rw [←sInf_image]
rw [Set.image]
```

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 2.2s, verify 0.1s, in=775, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image]
congr
ext x
rw [Set.mem_image, Set.mem_setOf]
```

**lean_error:** tail step 1/4 ('rw [coe_sInf, sInf_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=775, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **success**  (gen 1.5s, verify 0.1s, in=775, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf, ← sInf_image, Set.image]
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.6s, verify 0.1s, in=775, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf, sInf_image, preimage_set_of_eq]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, sInf_image, preimage_set_of_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=775, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coe_sInf, ← sInf_image, image_eq_preimage]
```

**lean_error:** tail step 1/1 ('rw [coe_sInf, ← sInf_image, image_eq_preimage]'): tactic 'rewrite' failed, equality or iff proof expected
