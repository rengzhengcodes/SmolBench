# Prod.swap_iInf   (k=0, 1 tactics total)

file: `Mathlib/Order/CompleteLattice.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [iInf, swap_sInf, ← range_comp, Function.comp]
```

**True premises at k:** `iInf`, `Prod.swap_sInf`, `Set.range_comp`, `Function.comp`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-goedel | qwen3-lean-leannav | qwen3-lean-real |
| --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | · | ✘ | · |
| `hint:2` | ✘ | ✘ | · | · |
| `hint:3` | ✘ | ✘ | · | · |
| `noise:3` | ✘ | · | · | · |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 110.2s, verify 0.1s, in=292, out=6229)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iInf_prod, swap, iInf_prod]; congr; apply iInf_congr; intro i; rfl
```

**lean_error:** tail step 1/1 ('rw [iInf_prod, swap, iInf_prod]; congr; apply iInf_congr; intro i; rfl'): <stdin>:1:31: expected end of input

### `stepk:1` · qwen3-lean-goedel · rollout 0 → **incomplete**  (gen 1.4s, verify 0.1s, in=292, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [iInf]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
β₂ : Type u_3
γ : Type u_4
ι : Sort u_5
ι' : Sort u_6
...
```

### `stepk:1` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 3.7s, verify 0.1s, in=292, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 0.9s, verify 0.1s, in=292, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [iInf]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
β₂ : Type u_3
γ : Type u_4
ι : Sort u_5
ι' : Sort u_6
...
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 39.6s, verify 0.1s, in=1106, out=2076)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iInf, Prod.swap_sInf, Set.range_comp]
```

**lean_error:** tail step 1/1 ('rw [iInf, Prod.swap_sInf, Set.range_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=1106, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [iInf, Prod.swap_sInf, Set.range_comp, Function.comp, Prod.swap_fst, Prod.swap_snd]
```

**lean_error:** tail step 1/1 ('simp only [iInf, Prod.swap_sInf, Set.range_comp, Function.comp, Prod.swap_fst, Prod.swap_snd]'): unknown constant 'Prod.swap_fst'

### `hint:2` · qwen3-lean-leannav · rollout 0 → **incomplete**  (gen 3.9s, verify 0.1s, in=1106, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [iInf, Prod.swap_sInf, Set.range_comp, ← image_comp]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
β₂ : Type u_3
γ : Type u_4
ι : Sort u_5
ι' : Sort u_6
...
```

### `hint:2` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 1.0s, verify 0.1s, in=1106, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [iInf, Prod.swap_sInf, Set.range_comp]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
β₂ : Type u_3
γ : Type u_4
ι : Sort u_5
ι' : Sort u_6
...
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 9.0s, verify 0.3s, in=2511, out=436)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold iInf
rw [Prod.swap_sInf]
rw [Set.range_comp]
rfl
```

**lean_error:** tail step 3/4 ('rw [Set.range_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=2511, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Prod.swap_sInf, range_comp, Function.comp]
```

**lean_error:** tail step 1/1 ('simp only [Prod.swap_sInf, range_comp, Function.comp]'): simp made no progress

### `hint:3` · qwen3-lean-leannav · rollout 0 → **incomplete**  (gen 3.7s, verify 0.1s, in=2511, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [iInf, Prod.swap_sInf, Set.range_comp, Function.comp]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
β₂ : Type u_3
γ : Type u_4
ι : Sort u_5
ι' : Sort u_6
...
```

### `hint:3` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 1.1s, verify 0.1s, in=2511, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [iInf, Prod.swap_sInf, Set.range_comp, Set.image_image]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
β₂ : Type u_3
γ : Type u_4
ι : Sort u_5
ι' : Sort u_6
...
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 69.9s, verify 0.1s, in=2531, out=3681)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iInf, Prod.swap_sInf, Set.range_comp]
```

**lean_error:** tail step 1/1 ('rw [iInf, Prod.swap_sInf, Set.range_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-goedel · rollout 0 → **incomplete**  (gen 0.9s, verify 0.1s, in=2531, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [iInf, swap_sInf, range_comp]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
β₂ : Type u_3
γ : Type u_4
ι : Sort u_5
ι' : Sort u_6
...
```

### `noise:3` · qwen3-lean-leannav · rollout 0 → **incomplete**  (gen 3.8s, verify 0.1s, in=2531, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [iInf, swap_sInf, range_comp]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
β₂ : Type u_3
γ : Type u_4
ι : Sort u_5
ι' : Sort u_6
...
```

### `noise:3` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 1.9s, verify 0.1s, in=2531, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [iInf, swap_sInf, range_comp]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
β₂ : Type u_3
γ : Type u_4
ι : Sort u_5
ι' : Sort u_6
...
```
