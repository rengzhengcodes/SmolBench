# LinearMap.ker_prodMap   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Prod.lean`  

**Ground-truth tail (from k):**
```lean
rw [← prodMap_comap_prod, Submodule.prod_bot]
```

**True premises at k:** `LinearMap.prodMap_comap_prod`, `Submodule.prod_bot`

## Verdict matrix

| rung | llama-31-405b-base | llama-31-405b-lean-lora | nemotron-ultra-253b-base | nemotron-ultra-253b-lean-lora | qwen3-235b-a22b-base | qwen3-235b-a22b-lean-lora |
| --- | --- | --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | · | ✘ | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | ✘ | ✘ | ✓ | · |
| `hint:3` | ✘ | ✘ | ✘ | ✘ | ✓ | · |
| `noise:3` | ✘ | ✘ | ✘ | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=532, out=84)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext ⟨x, y⟩,
  constructor,
  rintro ⟨h : f x + g y = 0⟩,
  rw [add_eq_zero_iff] at h,
  obtain ⟨hx, hy⟩ := h,
  exact ⟨hx, hy⟩,
  rintro ⟨hf : f x = 0, hg : g y = 0⟩,
  exact add_eq_zero hf hg
```

**lean_error:** tail step 1/8 ('ext ⟨x, y⟩,'): <stdin>:1:10: expected end of input

### `stepk:1` · llama-31-405b-lean-lora · rollout 0 → **incomplete**  (gen 0.9s, verify 0.4s, in=532, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Submodule.comap_bot, ker_prodMap]
```

**final state (truncated):**
```
R : Type u
K : Type u'
M : Type v
V : Type v'
M₂ : Type w
V₂ : Type w'
...
```

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 2.8s, verify 0.1s, in=521, out=189)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply submodule.ext
intro x
constructor
intro h
simp only [submodule.comap_pure_le, submodule.prod_le_prod, submodule.le_def] at h
split
{ intro a
  have := h (a, 0)
  simp only [prod_map_apply, submodule.comap_pure_le, submodule.le_def] at this
  exact this.1 }
{ intro b
  have := h (0, b)
  simp only [prod_map_apply, submodule.comap_pure_le, submodule.le_def] at this
  exact this.2 }
intro h
simp only [submodule.comap_pure_le, submodule.prod_le_prod, submodule.le_def] at h
intro p
simp only [prod_map_apply, submodule.comap_pure_le, submodule.le_def]
exact ⟨h.1 p.1, h.2 p.2⟩
```

**lean_error:** tail step 1/19 ('apply submodule.ext'): unknown identifier 'submodule.ext'

### `stepk:1` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 3.7s, verify 0.2s, in=512, out=151)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Submodule.comap_prodMap, Submodule.comap_bot, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('rw [Submodule.comap_prodMap, Submodule.comap_bot, Submodule.prod_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 129.7s, verify 0.5s, in=498, out=8726)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Submodule.ext
rintro ⟨x, y⟩
simp only [Submodule.mem_comap, LinearMap.map_pair, Prod.mk_eq_zero_iff, Submodule.mem_prod, mem_bot]
```

**lean_error:** tail step 3/3 ('simp only [Submodule.mem_comap, LinearMap.map_pair, Prod.mk_eq_zero_iff, Submodule.mem_prod, mem_bot]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 1.0s, verify 0.2s, in=498, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
R : Type u
K : Type u'
M : Type v
V : Type v'
M₂ : Type w
V₂ : Type w'
...
```

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=972, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥]
rw [Submodule.prod_bot]
```

**lean_error:** tail step 1/2 ('rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.7s, verify 0.2s, in=972, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← comap_bot, prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [← comap_bot, prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=961, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=952, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 101.7s, verify 0.1s, in=940, out=6895)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Submodule.prod_bot, prodMap_comap_prod f g ⊥ ⊥]
```

### `hint:2` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 0.9s, verify 0.2s, in=940, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
R : Type u
K : Type u'
M : Type v
V : Type v'
M₂ : Type w
V₂ : Type w'
...
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=1501, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥]
rw [Submodule.prod_bot]
```

**lean_error:** tail step 1/2 ('rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=1501, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← comap_bot, prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [← comap_bot, prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.2s, in=1490, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 2.8s, verify 0.2s, in=1481, out=104)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 36.5s, verify 0.1s, in=1471, out=2328)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← Submodule.prod_bot, LinearMap.prodMap_comap_prod]
```

### `hint:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 0.7s, verify 0.2s, in=1471, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
R : Type u
K : Type u'
M : Type v
V : Type v'
M₂ : Type w
V₂ : Type w'
...
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=1527, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥]
rw [Submodule.prod_bot]
```

**lean_error:** tail step 1/2 ('rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=1527, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← comap_bot, prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [← comap_bot, prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1516, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact rfl
```

**lean_error:** tail step 1/1 ('exact rfl'): type mismatch

### `noise:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=1507, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 63.9s, verify 0.1s, in=1498, out=3973)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Submodule.prod_bot], apply LinearMap.prodMap_comap_prod
```

**lean_error:** tail step 1/1 ('rw [Submodule.prod_bot], apply LinearMap.prodMap_comap_prod'): <stdin>:1:23: expected end of input

### `noise:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 1.2s, verify 0.4s, in=1498, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [LinearMap.prodMap_comap_prod]
```

**final state (truncated):**
```
R : Type u
K : Type u'
M : Type v
V : Type v'
M₂ : Type w
V₂ : Type w'
...
```
