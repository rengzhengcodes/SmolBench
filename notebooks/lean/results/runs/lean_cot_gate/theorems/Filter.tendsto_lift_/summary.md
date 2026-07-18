# Filter.tendsto_lift'   (k=0, 1 tactics total)

file: `Mathlib/Order/Filter/Lift.lean`  

**Ground-truth tail (from k):**
```lean
simp only [Filter.lift', tendsto_lift, tendsto_principal, comp]
```

**True premises at k:** `Filter.lift'`, `Filter.tendsto_lift`, `Filter.tendsto_principal`, `Function.comp`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ |
| `hint:3` | · ✓ ✓ ✓ |
| `noise:3` | ✓ ✓ ✓ · |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=296, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [tendsto_lift'_gen]
```

**lean_error:** tail step 1/1 ("simp [tendsto_lift'_gen]"): unknown identifier 'tendsto_lift'_gen'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.3s, verify 1.4s, in=296, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [tendsto_def, mem_lift'_sets]
```

**lean_error:** tail step 1/1 ("simp [tendsto_def, mem_lift'_sets]"): unknown identifier 'mem_lift'_sets'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.7s, verify 0.1s, in=296, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [tendsto_def, mem_lift'_sets, eventually_map]
```

**lean_error:** tail step 1/1 ("simp only [tendsto_def, mem_lift'_sets, eventually_map]"): unknown identifier 'mem_lift'_sets'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 3.7s, verify 0.1s, in=296, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Filter.lift'_tendsto_iff, tendsto_iff_eventually]
```

**lean_error:** tail step 1/1 ("simp only [Filter.lift'_tendsto_iff, tendsto_iff_eventually]"): unknown constant 'Filter.lift'_tendsto_iff'

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.1s, verify 0.1s, in=1211, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Filter.lift', tendsto_lift, tendsto_principal]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.7s, verify 0.7s, in=1211, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Filter.lift', tendsto_lift, tendsto_principal]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 3.8s, verify 0.1s, in=1211, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Filter.lift', tendsto_lift, Function.comp_apply, tendsto_principal]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 3.9s, verify 0.1s, in=1211, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Filter.lift', tendsto_lift, tendsto_principal, Function.comp_apply]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 3.9s, verify 0.1s, in=3868, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Filter.lift', tendsto_lift, tendsto_principal]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
f f₁ f₂ : Filter α
h h₁ h₂ : Set α → Set β
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 4.1s, verify 0.1s, in=3868, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Filter.lift', tendsto_lift, Function.comp_apply, tendsto_principal]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 4.2s, verify 0.1s, in=3868, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Filter.lift', tendsto_lift, tendsto_principal]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 4.4s, verify 0.1s, in=3868, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Filter.lift', tendsto_lift, tendsto_principal]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 3.4s, verify 0.1s, in=3895, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Filter.lift', tendsto_lift, tendsto_principal]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 3.5s, verify 0.1s, in=3895, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Filter.lift', tendsto_lift, tendsto_principal]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 3.6s, verify 0.1s, in=3895, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Filter.lift', tendsto_lift, Function.comp_apply, tendsto_principal]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 4.0s, verify 0.1s, in=3895, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Filter.lift', tendsto_lift, tendsto_principal]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
f f₁ f₂ : Filter α
h h₁ h₂ : Set α → Set β
...
```
