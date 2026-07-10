# Prod.swap_iInf   (k=0, 1 tactics total)

file: `Mathlib/Order/CompleteLattice.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [iInf, swap_sInf, ← range_comp, Function.comp]
```

**True premises at k:** `iInf`, `Prod.swap_sInf`, `Set.range_comp`, `Function.comp`

## Verdict matrix

| rung | llama-31-405b-base | llama-31-405b-lean-lora | nemotron-ultra-253b-base | nemotron-ultra-253b-lean-lora | qwen3-235b-a22b-base | qwen3-235b-a22b-lean-lora |
| --- | --- | --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ | ✘ | ✘ | · |
| `hint:3` | ✘ | ✘ | ✘ | ✘ | · | · |
| `noise:3` | ✘ | ✘ | ✘ | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.3s, in=315, out=37)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iInf, swap]
ext
simp [iInf, swap, infᵢ]
congr
funext
rw [swap]
rfl
rfl
```

**lean_error:** tail step 3/8 ('simp [iInf, swap, infᵢ]'): unknown identifier 'infᵢ'

### `stepk:1` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=315, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [swap, iInf_prod, iInf_comm]
```

**lean_error:** tail step 1/1 ('simp_rw [swap, iInf_prod, iInf_comm]'): simp made no progress

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=304, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iInf, swap_prod, infᵢ_prod]
congr
ext i
simp [swap]
```

**lean_error:** tail step 1/4 ('rw [iInf, swap_prod, infᵢ_prod]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=295, out=63)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iInf, swap_prod, infi_inf_eq]
simp [swap_prod]
```

**lean_error:** tail step 1/2 ('rw [iInf, swap_prod, infi_inf_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 160.7s, verify 0.2s, in=292, out=9593)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
simp only [Prod.snd_iInf]
simp only [Prod.fst_iInf]
```

**lean_error:** tail step 2/3 ('simp only [Prod.snd_iInf]'): simp made no progress

### `stepk:1` · qwen3-235b-a22b-lean-lora · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=292, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=1125, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iInf, swap_sInf]
rw [Set.range_comp Prod.swap]
rw [Function.comp]
```

**lean_error:** tail step 2/3 ('rw [Set.range_comp Prod.swap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=1125, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iInf, iInf, swap_sInf, Set.range_comp]
```

**lean_error:** tail step 1/1 ('rw [iInf, iInf, swap_sInf, Set.range_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 21.3s, verify 0.1s, in=1114, out=1626)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold iInf,
rw swap_sInf,
rw ← range_comp,
```

**lean_error:** tail step 1/3 ('unfold iInf,'): <stdin>:1:11: expected end of input

### `hint:2` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1105, out=43)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iInf, swap_sInf, Set.range_comp, Function.comp]
simp [Set.image_univ]
exact congr_arg sInf (Set.ext_iff.mpr (by aesop))
```

**lean_error:** tail step 1/3 ('rw [iInf, swap_sInf, Set.range_comp, Function.comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 65.2s, verify 0.3s, in=1106, out=3639)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold iInf
rw [swap_sInf]
rw [Set.range_comp Prod.swap f]
rfl
```

**lean_error:** tail step 3/4 ('rw [Set.range_comp Prod.swap f]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 1.2s, verify 0.1s, in=1106, out=24)

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

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.2s, in=2519, out=26)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [iInf, swap_sInf]
rw [Set.range_comp Function.swap]
rw [Set.image_comp Function.swap]
```

**lean_error:** tail step 2/3 ('rw [Set.range_comp Function.swap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=2519, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [iInf, swap_sInf, range_comp]
```

**lean_error:** tail step 1/1 ('rw [iInf, swap_sInf, range_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=2508, out=43)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
done
```

**lean_error:** tail step 1/1 ('done'): internal exception #7

### `hint:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 2.1s, verify 0.1s, in=2499, out=72)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [iInf, swap_sInf, range_comp, Function.comp]
exact congr_arg sInf (by rw [image_comp, image_comp])
```

**lean_error:** tail step 1/2 ('rw [iInf, swap_sInf, range_comp, Function.comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 66.5s, verify 0.1s, in=2511, out=3721)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [iInf, swap_sInf, ← Set.range_comp]
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

### `hint:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 1.0s, verify 0.1s, in=2511, out=23)

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

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=2547, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iInf, swap_sInf]
rw [Set.range_comp Prod.swap]
rw [iInf]
```

**lean_error:** tail step 2/3 ('rw [Set.range_comp Prod.swap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=2547, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iInf, swap_sInf, range_comp]
```

**lean_error:** tail step 1/1 ('rw [iInf, swap_sInf, range_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.3s, in=2536, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iInf, swap_sInf]
congr
exact Set.range_comp swap f
```

**lean_error:** tail step 3/3 ('exact Set.range_comp swap f'): type mismatch

### `noise:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=2527, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iInf, swap_sInf, range_comp, Function.comp, Prod.swap_image', Set.image_image]
```

**lean_error:** tail step 1/1 ("rw [iInf, swap_sInf, range_comp, Function.comp, Prod.swap_image', Set.image_image]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 61.5s, verify 0.3s, in=2531, out=3399)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iInf]
rw [Prod.swap_sInf]
rw [Set.range_comp]
rfl
```

**lean_error:** tail step 3/4 ('rw [Set.range_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 1.1s, verify 0.1s, in=2531, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

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
