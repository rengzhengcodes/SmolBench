# Submodule.ker_inl   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/Prod.lean`  

**Ground-truth tail (from k):**
```lean
rw [ker, ← prod_bot, prod_comap_inl]
```

**True premises at k:** `LinearMap.ker`, `Submodule.prod_bot`, `Submodule.prod_comap_inl`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.1s, in=358, out=53)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x,
rw [mem_ker, inl_apply],
simp only [mem_bot, eq_self_iff_true, zero_add, map_zero],
split,
exact λ h, h.1,
exact λ h, ⟨h, zero_mem q⟩,
```

**lean_error:** tail step 1/6 ('ext x,'): <stdin>:1:5: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.4s, in=328, out=71)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
intro x
simp only [inl_apply, mem_ker, LinearMap.coe_mk, AddHom.coe_mk]
rw [← add_zero (x : M), LinearMap.map_add, LinearMap.map_zero, add_eq_zero_iff_eq_neg, neg_zero, eq_self_iff_true, Submodule.mem_bot]
rfl
```

**lean_error:** tail step 2/5 ('intro x'): tactic 'introN' failed, insufficient number of binders

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=347, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ker_inl]
rfl
```

**lean_error:** tail step 1/2 ('rw [ker_inl]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 1.0s, in=813, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.ker, Submodule.comap_bot],
exact Submodule.prod_bot,
```

**lean_error:** tail step 1/2 ('rw [LinearMap.ker, Submodule.comap_bot],'): <stdin>:1:39: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=769, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.ker, Submodule.comap_inl_prod, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.ker, Submodule.comap_inl_prod, Submodule.prod_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 23.1s, verify 0.1s, in=802, out=1418)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [ker, prod_bot, prod_comap_inl]
```

**lean_error:** tail step 1/1 ('rw [ker, prod_bot, prod_comap_inl]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.2s, in=1768, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [LinearMap.ker, Submodule.comap_bot, Submodule.prod_comap_inl]
exact Submodule.prod_bot
```

**lean_error:** tail step 1/2 ('rw [LinearMap.ker, Submodule.comap_bot, Submodule.prod_comap_inl]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=1735, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [LinearMap.ker, Submodule.comap_inl_prod, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.ker, Submodule.comap_inl_prod, Submodule.prod_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1757, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [ker, comap_inl, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [ker, comap_inl, prod_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=1792, out=45)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
change ker (inl R M M₂) = comap (inl R M M₂) ⊥,
rw [comap_bot, comap_comap, prod_comap_inl],
exact prod_bot
```

**lean_error:** tail step 1/3 ('change ker (inl R M M₂) = comap (inl R M M₂) ⊥,'): <stdin>:1:46: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.2s, in=1858, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.ker, Submodule.comap_inl_prod, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.ker, Submodule.comap_inl_prod, Submodule.prod_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1781, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [ker, comap_inl, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [ker, comap_inl, prod_bot]'): tactic 'rewrite' failed, equality or iff proof expected
