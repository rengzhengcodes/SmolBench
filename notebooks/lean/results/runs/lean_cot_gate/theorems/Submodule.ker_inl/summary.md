# Submodule.ker_inl   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/Prod.lean`  

**Ground-truth tail (from k):**
```lean
rw [ker, ← prod_bot, prod_comap_inl]
```

**True premises at k:** `LinearMap.ker`, `Submodule.prod_bot`, `Submodule.prod_comap_inl`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✘ | ✘ ✘ ✘ ✘ | ✓ ✘ ✓ · |
| `hint:3` | ✘ ✓ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✓ ✓ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ · · |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 82.9s, verify 0.1s, in=331, out=3407)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply ker_eq_bot
intros m h
rw [linear_map.inl_apply] at h
rw [prod.mk_eq_zero] at h
exact h.1
```

**lean_error:** tail step 1/5 ('apply ker_eq_bot'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 97.3s, verify 0.1s, in=331, out=4021)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply ker_eq_bot_iff.mpr
intros x h
have ⟨hx, _⟩ := Prod.eq_zero_iff.1 h
exact hx
```

**lean_error:** tail step 1/4 ('apply ker_eq_bot_iff.mpr'): unknown identifier 'ker_eq_bot_iff.mpr'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 119.5s, verify 0.1s, in=331, out=4974)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply submodule.ext
intro x
split
· intro hx
  rw inl_apply at hx
  rw Prod.eq_iff_fst_eq_snd_eq at hx
  exact hx.1
· intro hx
  rw hx
  simp [inl_apply]
```

**lean_error:** tail step 1/10 ('apply submodule.ext'): unknown identifier 'submodule.ext'

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 124.9s, verify 0.2s, in=331, out=5227)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
simp only [Submodule.mem_ker, LinearMap.inl_apply, Prod.mk_eq_zero, Submodule.mem_bot]
split
rintro ⟨rfl, _⟩
intro h
simp [h]
```

**lean_error:** tail step 2/6 ('simp only [Submodule.mem_ker, LinearMap.inl_apply, Prod.mk_eq_zero, Submodule.mem_bot]'): unknown constant 'Submodule.mem_ker'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=331, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=331, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Submodule.ext_iff]
```

**lean_error:** tail step 1/1 ('simp [Submodule.ext_iff]'): unknown constant 'Submodule.ext_iff'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.6s, verify 0.1s, in=331, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [ker_eq_bot_iff_injective]
```

**lean_error:** tail step 1/1 ('simp [ker_eq_bot_iff_injective]'): unknown identifier 'ker_eq_bot_iff_injective'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=331, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Submodule.ext_iff, inl]
```

**lean_error:** tail step 1/1 ('simp [Submodule.ext_iff, inl]'): unknown constant 'Submodule.ext_iff'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 5.5s, verify 0.1s, in=331, out=175)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 5.9s, verify 0.1s, in=331, out=183)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 8.2s, verify 0.1s, in=331, out=245)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [LinearMap.ker_eq_bot, LinearMap.inl_injective]
```

**lean_error:** tail step 1/1 ('simp only [LinearMap.ker_eq_bot, LinearMap.inl_injective]'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 8.4s, verify 0.1s, in=331, out=256)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [ker_eq_bot_iff_injective, inl_injective]
```

**lean_error:** tail step 1/1 ('rw [ker_eq_bot_iff_injective, inl_injective]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 28.2s, verify 0.1s, in=786, out=1124)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.ker, ← Submodule.prod_bot, Submodule.prod_comap_inl]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 52.4s, verify 0.1s, in=786, out=2160)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [ker, ←prod_bot, prod_comap_inl]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 69.2s, verify 0.3s, in=786, out=2869)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.ker]
rw [← Submodule.prod_bot]
rw [Submodule.prod_comap_inl]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 97.7s, verify 0.1s, in=786, out=4037)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.1s, verify 0.4s, in=786, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [ker, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('simp [ker, Submodule.prod_bot]'): tactic 'simp' failed, nested error:

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.7s, verify 0.1s, in=786, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Submodule.ker, prod_comap_inl]
```

**lean_error:** tail step 1/1 ('simp [Submodule.ker, prod_comap_inl]'): unknown constant 'Submodule.ker'

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.9s, verify 0.4s, in=786, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]'): tactic 'simp' failed, nested error:

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.2s, verify 0.3s, in=786, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]'): tactic 'simp' failed, nested error:

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 8.8s, verify 0.1s, in=786, out=266)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.ker, ← prod_bot, prod_comap_inl]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 9.8s, verify 0.4s, in=786, out=297)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [ker, prod_comap_inl, prod_bot]
```

**lean_error:** tail step 1/1 ('simp [ker, prod_comap_inl, prod_bot]'): tactic 'simp' failed, nested error:

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 11.1s, verify 0.1s, in=786, out=332)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [ker, ← prod_bot, prod_comap_inl]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 11.3s, verify 0.1s, in=786, out=335)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [LinearMap.ker, prod_bot, prod_comap_inl]
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

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 65.5s, verify 0.1s, in=1744, out=1587)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 69.2s, verify 0.1s, in=1744, out=2162)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [ker, ←prod_bot, prod_comap_inl]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 126.1s, verify 0.4s, in=1744, out=3125)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]'): tactic 'simp' failed, nested error:

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 127.2s, verify 0.1s, in=1744, out=2623)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [ker, Submodule.prod_bot, Submodule.prod_comap_inl]
```

**lean_error:** tail step 1/1 ('rw [ker, Submodule.prod_bot, Submodule.prod_comap_inl]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 3.9s, verify 0.4s, in=1744, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]'): tactic 'simp' failed, nested error:

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 4.2s, verify 0.1s, in=1744, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Submodule.ker, prod_comap_inl, prod_bot]
```

**lean_error:** tail step 1/1 ('simp [Submodule.ker, prod_comap_inl, prod_bot]'): unknown constant 'Submodule.ker'

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 4.3s, verify 0.3s, in=1744, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]'): tactic 'simp' failed, nested error:

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 4.7s, verify 0.3s, in=1744, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]'): tactic 'simp' failed, nested error:

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 15.2s, verify 0.4s, in=1744, out=295)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]'): tactic 'simp' failed, nested error:

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 15.6s, verify 0.4s, in=1744, out=299)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]'): tactic 'simp' failed, nested error:

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 16.4s, verify 0.5s, in=1744, out=279)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]'): tactic 'simp' failed, nested error:

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 17.5s, verify 0.4s, in=1744, out=323)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [ker, prod_comap_inl, prod_bot]
```

**lean_error:** tail step 1/1 ('simp [ker, prod_comap_inl, prod_bot]'): tactic 'simp' failed, nested error:

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 17.5s, verify 0.1s, in=1768, out=701)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.ker, ←Submodule.prod_bot, Submodule.prod_comap_inl]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 68.6s, verify 0.1s, in=1768, out=2844)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.ker, ←Submodule.prod_bot, Submodule.prod_comap_inl]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 77.9s, verify 0.1s, in=1768, out=3214)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 90.0s, verify 0.1s, in=1768, out=3686)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Submodule.ker, ←Submodule.prod_bot]
exact Submodule.prod_comap_inl ⊥ ⊥
```

**lean_error:** tail step 1/2 ('rw [Submodule.ker, ←Submodule.prod_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.7s, verify 0.4s, in=1768, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [LinearMap.ker, prod_comap_inl]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.ker, prod_comap_inl]'): tactic 'simp' failed, nested error:

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.2s, verify 0.3s, in=1768, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]'): tactic 'simp' failed, nested error:

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.5s, verify 0.3s, in=1768, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]'): tactic 'simp' failed, nested error:

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 3.5s, verify 0.3s, in=1768, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.ker, Submodule.prod_comap_inl, Submodule.prod_bot]'): tactic 'simp' failed, nested error:

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 7.8s, verify 0.3s, in=1768, out=238)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]'): tactic 'simp' failed, nested error:

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 8.5s, verify 0.4s, in=1768, out=259)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [ker, prod_comap_inl, prod_bot]
```

**lean_error:** tail step 1/1 ('simp [ker, prod_comap_inl, prod_bot]'): tactic 'simp' failed, nested error:

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 10.1s, verify 0.1s, in=1768, out=298)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [ker, prod_comap_inl, prod_bot]
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

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 11.1s, verify 0.1s, in=1768, out=309)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]
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
