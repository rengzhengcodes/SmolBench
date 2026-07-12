# LinearMap.ker_prodMap   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Prod.lean`  

**Ground-truth tail (from k):**
```lean
rw [← prodMap_comap_prod, Submodule.prod_bot]
```

**True premises at k:** `LinearMap.prodMap_comap_prod`, `Submodule.prod_bot`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-goedel | qwen3-lean-leannav | qwen3-lean-real |
| --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | · | · | · |
| `hint:2` | ✓ | · | ✘ | · |
| `hint:3` | ✘ | · | ✘ | · |
| `noise:3` | ✘ | · | · | · |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 79.9s, verify 0.3s, in=498, out=4363)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext ⟨x, y⟩
split
· intro h
  simp at h
  exact ⟨h.1, h.2⟩
· intro h
  simp
  exact ⟨h.1, h.2⟩
```

**lean_error:** tail step 2/8 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-lean-goedel · rollout 0 → **incomplete**  (gen 0.9s, verify 0.2s, in=498, out=6)

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

### `stepk:1` · qwen3-lean-leannav · rollout 0 → **incomplete**  (gen 0.8s, verify 0.2s, in=498, out=6)

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

### `stepk:1` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 1.0s, verify 0.2s, in=498, out=6)

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

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 73.0s, verify 0.2s, in=940, out=3904)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Submodule.prod_bot]
rw [prodMap_comap_prod]
```

### `hint:2` · qwen3-lean-goedel · rollout 0 → **incomplete**  (gen 7.6s, verify 0.2s, in=940, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

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

### `hint:2` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=940, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Submodule.prod_bot, LinearMap.prodMap_comap_prod]
```

**lean_error:** tail step 1/1 ('simp only [Submodule.prod_bot, LinearMap.prodMap_comap_prod]'): simp made no progress

### `hint:2` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 0.8s, verify 0.2s, in=940, out=6)

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

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 85.5s, verify 0.2s, in=1471, out=4685)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [←prod_bot, prodMap_comap_prod]
```

**lean_error:** tail step 1/1 ('rw [←prod_bot, prodMap_comap_prod]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-goedel · rollout 0 → **incomplete**  (gen 1.1s, verify 0.2s, in=1471, out=6)

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

### `hint:3` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1471, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('simp only [prodMap_comap_prod, prod_bot]'): unknown identifier 'prod_bot'

### `hint:3` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 0.7s, verify 0.2s, in=1471, out=6)

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

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 37.7s, verify 0.2s, in=1498, out=2017)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-goedel · rollout 0 → **incomplete**  (gen 1.2s, verify 0.2s, in=1498, out=15)

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

### `noise:3` · qwen3-lean-leannav · rollout 0 → **incomplete**  (gen 1.1s, verify 0.2s, in=1498, out=15)

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

### `noise:3` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 1.7s, verify 0.2s, in=1498, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

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
