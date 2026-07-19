# LinearMap.ker_prodMap   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Prod.lean`  

**Ground-truth tail (from k):**
```lean
rw [← prodMap_comap_prod, Submodule.prod_bot]
```

**True premises at k:** `LinearMap.prodMap_comap_prod`, `Submodule.prod_bot`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✓ ✘ ✘ ✘ | ✘ ✘ ✘ · |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 2 → **success**  (gen 0.9s, verify 0.3s, in=532, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
simp [Submodule.mem_comap, Submodule.mem_bot, Submodule.mem_prod]
```

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 2.3s, verify 0.6s, in=532, out=85)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
constructor
rintro ⟨x, hx⟩
rw [Submodule.mem_bot] at hx
exact ⟨⟨x.1, by simp [hx]⟩, ⟨x.2, by simp [hx]⟩⟩
rintro ⟨⟨x, hx⟩, ⟨y, hy⟩⟩
exact ⟨⟨x, y⟩, by simp [hx, hy]⟩
```

**lean_error:** tail step 3/7 ('rintro ⟨x, hx⟩'): tactic 'cases' failed, nested error:

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 3.6s, verify 0.6s, in=532, out=139)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
constructor
· rintro ⟨x, y⟩ hx
  rw [Submodule.mem_bot] at hx
  rw [Submodule.mem_bot, Prod.mk_eq_zero] at hx
  constructor
  · apply mem_comap
    rw [Submodule.mem_bot]
    exact hx.1
  · apply mem_comap
    rw [Submodule.mem_bot]
    exact hx.2
· rintro ⟨⟨x, hx⟩, ⟨y, hy⟩⟩
  apply mem_comap
  rw [Submodule.mem_bot]
  rw [Prod.mk_eq_zero]
  constructor
  · exact hx
  · exact hy
```

**lean_error:** tail step 3/19 ('· rintro ⟨x, y⟩ hx'): tactic 'cases' failed, nested error:

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.1s, verify 0.8s, in=532, out=140)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
simp only [Submodule.mem_comap, Submodule.mem_bot, LinearMap.prodMap_apply, Prod.mk.inj_iff]
constructor
· rintro ⟨x, y⟩ hx
  constructor
  · apply Submodule.mem_comap.mp
    rw [Submodule.mem_bot]
    exact hx.1
  · apply Submodule.mem_comap.mp
    rw [Submodule.mem_bot]
    exact hx.2
· rintro ⟨⟨x, hx⟩, ⟨y, hy⟩⟩
  apply Submodule.mem_comap.mpr
  rw [Submodule.mem_bot]
  constructor
  · exact hx
  · exact hy
```

**lean_error:** tail step 4/17 ('· rintro ⟨x, y⟩ hx'): tactic 'cases' failed, nested error:

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=532, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Submodule.prod, comap_prodMap]
```

**lean_error:** tail step 1/1 ('simp [Submodule.prod, comap_prodMap]'): unknown identifier 'comap_prodMap'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.2s, verify 0.1s, in=532, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [Submodule.comap_bot, ker_prodMap]
```

**lean_error:** tail step 1/1 ('simp_rw [Submodule.comap_bot, ker_prodMap]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=532, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [comap_bot, ker_prodMap]
```

**lean_error:** tail step 1/1 ('simp_rw [comap_bot, ker_prodMap]'): unknown identifier 'comap_bot'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **incomplete**  (gen 1.8s, verify 0.2s, in=532, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Submodule.prod, Submodule.comap, prodMap]
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

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=972, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [←prodMap_comap_prod f g ⊥ ⊥],
simp [prod_bot]
```

**lean_error:** tail step 1/2 ('rw [←prodMap_comap_prod f g ⊥ ⊥],'): <stdin>:1:32: expected end of input

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.2s, verify 0.1s, in=972, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.prodMap_comap_prod f g],
simp only [Submodule.prod_bot]
```

**lean_error:** tail step 1/2 ('rw [LinearMap.prodMap_comap_prod f g],'): <stdin>:1:37: expected end of input

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=972, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥]
rw [Submodule.prod_bot]
```

**lean_error:** tail step 1/2 ('rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=972, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥],
simp only [Submodule.prod_bot]
```

**lean_error:** tail step 1/2 ('rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥],'): <stdin>:1:41: expected end of input

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.1s, verify 0.2s, in=972, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← prod_bot, prodMap_comap_prod]
```

**lean_error:** tail step 1/1 ('rw [← prod_bot, prodMap_comap_prod]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.3s, verify 0.2s, in=972, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← prod_bot, prodMap_comap_prod]
```

**lean_error:** tail step 1/1 ('rw [← prod_bot, prodMap_comap_prod]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.6s, verify 0.2s, in=972, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [← prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 2.1s, verify 0.2s, in=972, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← comap_bot, LinearMap.prodMap_comap_prod, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('rw [← comap_bot, LinearMap.prodMap_comap_prod, Submodule.prod_bot]'): tactic 'rewrite' failed, equality or iff proof expected
