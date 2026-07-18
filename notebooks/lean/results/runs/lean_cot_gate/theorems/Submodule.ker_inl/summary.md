# Submodule.ker_inl   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/Prod.lean`  

**Ground-truth tail (from k):**
```lean
rw [ker, ← prod_bot, prod_comap_inl]
```

**True premises at k:** `LinearMap.ker`, `Submodule.prod_bot`, `Submodule.prod_comap_inl`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ |

## Per-cell detail

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
