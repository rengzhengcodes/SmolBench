# Filter.mul_eq_one_iff   (k=9, 10 tactics total)

file: `Mathlib/Order/Filter/Pointwise.lean`  

**Ground-truth tail (from k):**
```lean
rw [pure_mul_pure, h, pure_one]
```

**True premises at k:** `Filter.pure_mul_pure`, `Filter.pure_one`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✘ | ✘ ✓ ✘ ✓ |
| `hint:2` | ✓ ✓ ✓ ✘ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ ✓ | ✓ · ✓ ✓ | ✓ ✘ ✘ ✘ |
| `noise:3` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✘ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 60.2s, verify 0.1s, in=259, out=2257)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [map_mul pure a b, h, map_one pure]
```

**lean_error:** tail step 1/1 ('rw [map_mul pure a b, h, map_one pure]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 74.2s, verify 0.1s, in=259, out=2808)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [pure_mul, h, pure_one]
```

**lean_error:** tail step 1/1 ('rw [pure_mul, h, pure_one]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 80.2s, verify 0.1s, in=259, out=3049)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← pure_mul a b]
rw [h]
rw [pure_one]
```

**lean_error:** tail step 1/3 ('rw [← pure_mul a b]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 148.5s, verify 0.1s, in=259, out=5583)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [←map_mul pure a b]
rw [h]
rw [map_one pure]
```

**lean_error:** tail step 1/3 ('rw [←map_mul pure a b]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.9s, verify 0.1s, in=259, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=259, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.3s, verify 0.1s, in=259, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.7s, verify 0.1s, in=259, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← pure_one, ← pure_mul, h]
```

**lean_error:** tail step 1/1 ('rw [← pure_one, ← pure_mul, h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 5.9s, verify 0.1s, in=259, out=165)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [pure_mul, h, pure_one]
```

**lean_error:** tail step 1/1 ('rw [pure_mul, h, pure_one]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 6.1s, verify 0.1s, in=259, out=175)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pure_mul_pure, h, pure_one]
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 7.3s, verify 0.1s, in=259, out=210)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← pure_mul, h, pure_one]
```

**lean_error:** tail step 1/1 ('rw [← pure_mul, h, pure_one]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 7.4s, verify 0.1s, in=259, out=212)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 20.3s, verify 0.1s, in=756, out=766)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Filter.pure_mul_pure, h, Filter.pure_one]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 22.8s, verify 0.1s, in=756, out=863)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 45.6s, verify 0.1s, in=756, out=1717)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
erw [pure_mul_pure, h, pure_one]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 105.0s, verify 0.2s, in=756, out=3988)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [pure_mul_pure]
rw [h]
refl
```

**lean_error:** tail step 3/3 ('refl'): <stdin>:1:1: unknown tactic

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.0s, verify 0.1s, in=756, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [h]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.1s, verify 0.1s, in=756, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [h]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.2s, verify 0.1s, in=756, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [h]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.6s, verify 0.1s, in=756, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [pure_mul_pure, h]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 4.7s, verify 0.1s, in=756, out=131)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 4.9s, verify 0.1s, in=756, out=140)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 6.0s, verify 0.1s, in=756, out=161)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 6.3s, verify 0.1s, in=756, out=178)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 19.2s, verify 0.1s, in=2577, out=398)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.pure_mul_pure, h, Filter.pure_one]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 22.7s, verify 0.1s, in=2577, out=434)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 51.8s, verify 0.1s, in=2577, out=1172)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 66.9s, verify 0.1s, in=2577, out=1759)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.1s, verify 0.1s, in=2577, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [h]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 2.1s, verify 0.1s, in=2577, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← h]
```

**final state (truncated):**
```
case refine'_2.intro.intro.intro.intro
F : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
δ : Type u_5
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.2s, verify 0.1s, in=2577, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [h]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.3s, verify 0.1s, in=2577, out=9)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [h]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 11.1s, verify 0.1s, in=2577, out=178)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 11.4s, verify 0.1s, in=2577, out=193)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rwa [← Filter.pure_mul_pure, h, Filter.pure_one]
```

**lean_error:** tail step 1/1 ('rwa [← Filter.pure_mul_pure, h, Filter.pure_one]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 11.8s, verify 0.1s, in=2577, out=204)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rwa [pure_mul_pure, h, pure_one]
```

**lean_error:** tail step 1/1 ('rwa [pure_mul_pure, h, pure_one]'): no goals to be solved

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 12.6s, verify 0.1s, in=2577, out=205)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rwa [pure_mul_pure, h, pure_one]
```

**lean_error:** tail step 1/1 ('rwa [pure_mul_pure, h, pure_one]'): no goals to be solved

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 8.2s, verify 0.1s, in=2592, out=316)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 11.0s, verify 0.1s, in=2592, out=416)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 21.9s, verify 0.1s, in=2592, out=824)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 58.6s, verify 0.1s, in=2592, out=2190)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
rfl
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.3s, verify 0.1s, in=2592, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [h]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.4s, verify 0.1s, in=2592, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [h]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.5s, verify 0.1s, in=2592, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [h]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.8s, verify 0.1s, in=2592, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [pure_mul_pure, h]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 4.8s, verify 0.1s, in=2592, out=139)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 7.1s, verify 0.1s, in=2592, out=206)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [pure_mul_pure, pure_one, h]
```

**lean_error:** tail step 1/1 ('rw [pure_mul_pure, pure_one, h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 7.2s, verify 0.1s, in=2592, out=208)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.pure_mul_pure, h, Filter.pure_one]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 7.6s, verify 0.1s, in=2592, out=220)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [pure_mul_pure, h, pure_one]
```
