# LinearMap.ker_prodMap   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Prod.lean`  

**Ground-truth tail (from k):**
```lean
rw [← prodMap_comap_prod, Submodule.prod_bot]
```

**True premises at k:** `LinearMap.prodMap_comap_prod`, `Submodule.prod_bot`

## Verdict matrix

| rung | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- |
| `stepk:1` | · · ✘ ✘ | ✘ · · · ✘ · · ✘ |
| `hint:2` | ✘ · ✘ ✘ | ✘ ✘ ✘ ✘ ✘ ✘ ✘ · |
| `hint:3` | · · ✘ ✘ | · ✘ ✘ ✘ ✓ ✘ ✘ X |
| `noise:3` | · ✘ · · | · ✘ ✘ ✘ ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.6s, verify 0.2s, in=498, out=6)

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

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 1.7s, verify 0.2s, in=498, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Submodule.eq_bot_iff]
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

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.9s, verify 0.1s, in=498, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Submodule.comap_eq_bot_iff]
```

**lean_error:** tail step 1/1 ('simp [Submodule.comap_eq_bot_iff]'): unknown constant 'Submodule.comap_eq_bot_iff'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.8s, verify 0.1s, in=498, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Submodule.comap_eq_bot_iff]
```

**lean_error:** tail step 1/1 ('simp [Submodule.comap_eq_bot_iff]'): unknown constant 'Submodule.comap_eq_bot_iff'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 4.4s, verify 0.1s, in=498, out=137)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [comap_prodMap]
```

**lean_error:** tail step 1/1 ('simp [comap_prodMap]'): unknown identifier 'comap_prodMap'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 5 → **incomplete**  (gen 5.1s, verify 0.2s, in=498, out=163)

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

### `stepk:1` · qwen3-lean-cot-r128 · rollout 4 → **incomplete**  (gen 5.3s, verify 0.2s, in=498, out=168)

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

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 6.4s, verify 0.2s, in=498, out=176)

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

### `stepk:1` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 7.0s, verify 0.2s, in=498, out=220)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [prodMap, Submodule.comap_prod_prod]
```

**lean_error:** tail step 1/1 ('rw [prodMap, Submodule.comap_prod_prod]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 8.3s, verify 0.2s, in=498, out=259)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ext_iff]
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

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 9.1s, verify 0.2s, in=498, out=281)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [prodMap, LinearMap.coe_mk]
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

### `stepk:1` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 9.7s, verify 0.1s, in=498, out=273)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Submodule.comap_prodMap]
```

**lean_error:** tail step 1/1 ('simp [Submodule.comap_prodMap]'): unknown constant 'Submodule.comap_prodMap'

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.9s, verify 0.2s, in=940, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 2.3s, verify 0.2s, in=940, out=15)

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

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.5s, verify 0.1s, in=940, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('simp [prodMap_comap_prod, prod_bot]'): unknown identifier 'prod_bot'

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.6s, verify 0.2s, in=940, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 6.2s, verify 0.2s, in=940, out=202)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [prodMap_comap_prod, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod, Submodule.prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 11.1s, verify 0.1s, in=940, out=184)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply LinearMap.ker_prodMap
```

**lean_error:** tail step 1/1 ('apply LinearMap.ker_prodMap'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 14.0s, verify 0.1s, in=940, out=421)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact prodMap_comap_prod _ _ ⊥ ⊥
```

**lean_error:** tail step 1/1 ('exact prodMap_comap_prod _ _ ⊥ ⊥'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 14.1s, verify 0.1s, in=940, out=306)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [LinearMap.prodMap_comap_prod, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('simp only [LinearMap.prodMap_comap_prod, Submodule.prod_bot]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 14.2s, verify 0.1s, in=940, out=248)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('simp [prodMap_comap_prod, prod_bot]'): unknown identifier 'prod_bot'

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 14.2s, verify 0.2s, in=940, out=388)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 16.2s, verify 0.2s, in=940, out=472)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← prod_bot, prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [← prod_bot, prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-cot-r128 · rollout 5 → **incomplete**  (gen 24.2s, verify 0.2s, in=940, out=597)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [prodMap_comap_prod]
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

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 2.8s, verify 0.2s, in=1471, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

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

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 3.0s, verify 0.2s, in=1471, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [prodMap_comap_prod]
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

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 3.2s, verify 0.2s, in=1471, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.4s, verify 0.2s, in=1471, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 25.4s, verify 0.2s, in=1471, out=345)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [prodMap_comap_prod]
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

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 26.5s, verify 0.2s, in=1471, out=207)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 30.8s, verify 0.2s, in=1471, out=543)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.prodMap_comap_prod f g ⊥ ⊥, Submodule.prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 31.8s, verify 0.1s, in=1471, out=353)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [prodMap_comap_prod _ _ ⊥ ⊥, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('simp only [prodMap_comap_prod _ _ ⊥ ⊥, Submodule.prod_bot]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 5 → **success**  (gen 33.4s, verify 0.1s, in=1471, out=412)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← Submodule.prod_bot, prodMap_comap_prod]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 35.4s, verify 0.1s, in=1471, out=493)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa only [prod_bot] using prodMap_comap_prod f g ⊥ ⊥
```

**lean_error:** tail step 1/1 ('simpa only [prod_bot] using prodMap_comap_prod f g ⊥ ⊥'): unknown identifier 'prod_bot'

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 94.1s, verify 0.1s, in=1471, out=322)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('simp only [prodMap_comap_prod, prod_bot]'): unknown identifier 'prod_bot'

### `hint:3` · qwen3-lean-cot-r128 · rollout 4 → **exception**  (gen 97.6s, verify 0.0s, in=0, out=0)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** RuntimeError: Inference endpoint unreachable after 10 consecutive connection failures (instance i-077d8082814a9172d is running). If the instance is running, your public IP probably changed and the security group is blocking you: re-run provision_spot_instance() to re-authorize your current IP.

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.1s, verify 0.2s, in=1498, out=15)

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

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.3s, verify 0.2s, in=1498, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 1.5s, verify 0.2s, in=1498, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [prodMap_comap_prod]
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

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 2.1s, verify 0.2s, in=1498, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [prodMap_comap_prod]
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

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 15.5s, verify 0.2s, in=1498, out=276)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [prodMap_comap_prod]
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

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 17.2s, verify 0.2s, in=1498, out=319)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [prodMap_comap_prod f g ⊥ ⊥, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod f g ⊥ ⊥, prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 18.0s, verify 0.1s, in=1498, out=302)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('simp only [prodMap_comap_prod, prod_bot]'): unknown identifier 'prod_bot'

### `noise:3` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 18.6s, verify 0.2s, in=1498, out=225)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← prodMap_comap_prod f g ⊥ ⊥, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [← prodMap_comap_prod f g ⊥ ⊥, prod_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 21.3s, verify 0.2s, in=1498, out=384)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [← prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 22.5s, verify 0.2s, in=1498, out=397)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [prodMap_comap_prod f g ⊥ ⊥]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod f g ⊥ ⊥]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 27.9s, verify 0.2s, in=1498, out=433)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← prod_bot, prodMap_comap_prod]
```

**lean_error:** tail step 1/1 ('rw [← prod_bot, prodMap_comap_prod]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 28.2s, verify 0.2s, in=1498, out=448)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [prodMap_comap_prod, prod_bot]
```

**lean_error:** tail step 1/1 ('rw [prodMap_comap_prod, prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
