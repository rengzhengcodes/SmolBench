# LinearMap.ker_prodMap   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Prod.lean`  

**Ground-truth tail (from k):**
```lean
rw [← prodMap_comap_prod, Submodule.prod_bot]
```

**True premises at k:** `LinearMap.prodMap_comap_prod`, `Submodule.prod_bot`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✘ | ✓ | ✘ |
| `noise:3` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=532, out=31)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext ⟨m, n⟩,
simp only [Submodule.mem_bot, Submodule.mem_comap, Submodule.mem_prod],
exact iff.rfl
```

**lean_error:** tail step 1/3 ('ext ⟨m, n⟩,'): <stdin>:1:10: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.5s, in=492, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
  simp [prodMap, eq_comm]
  simp [prodMap, eq_comm]
```

**lean_error:** tail step 3/3 ('simp [prodMap, eq_comm]'): simp made no progress

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.8s, in=521, out=87)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Submodule.ext
intro x
constructor
· rintro ⟨h₁, h₂⟩
  rw [Submodule.mem_comap] at h₁ h₂
  exact ⟨h₁, h₂⟩
· rintro ⟨h₁, h₂⟩
  rw [Submodule.mem_comap] at h₁ h₂
  exact ⟨h₁, h₂⟩
```

**lean_error:** tail step 4/9 ('· rintro ⟨h₁, h₂⟩'): tactic 'cases' failed, nested error:

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=972, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥]
rw [Submodule.prod_bot]
```

**lean_error:** tail step 1/2 ('rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 3.4s, verify 0.4s, in=915, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← prodMap_comap_prod, Submodule.prod_bot]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.2s, in=961, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.5s, in=1501, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥]
rw [Submodule.prod_bot]
```

**lean_error:** tail step 1/2 ('rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 3.2s, verify 0.1s, in=1443, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← prodMap_comap_prod, Submodule.prod_bot]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=1490, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=1527, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥]
rw [Submodule.prod_bot]
```

**lean_error:** tail step 1/2 ('rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 3.3s, verify 0.1s, in=1532, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← prodMap_comap_prod, Submodule.prod_bot]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1516, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact rfl
```

**lean_error:** tail step 1/1 ('exact rfl'): type mismatch
