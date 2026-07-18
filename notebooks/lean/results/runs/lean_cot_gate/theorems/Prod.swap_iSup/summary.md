# Prod.swap_iSup   (k=0, 1 tactics total)

file: `Mathlib/Order/CompleteLattice.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [iSup, swap_sSup, ← range_comp, Function.comp]
```

**True premises at k:** `iSup`, `Prod.swap_sSup`, `Set.range_comp`, `Function.comp`

## Verdict matrix

| rung | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ · · ✘ ✘ ✘ |
| `hint:2` | · ✘ ✘ ✘ | · · · · ✘ ✘ ✘ · |
| `hint:3` | · ✘ ✘ ✘ | ✘ · ✘ ✘ · ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | · ✘ ✘ · ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=292, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.3s, verify 0.1s, in=292, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [swap_def, iSup_prod]
```

**lean_error:** tail step 1/1 ('simp only [swap_def, iSup_prod]'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.4s, verify 0.1s, in=292, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [swap_iSup, iSup_swap]
```

**lean_error:** tail step 1/1 ('simp_rw [swap_iSup, iSup_swap]'): no goals to be solved

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.5s, verify 0.1s, in=292, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Prod.iSup]
```

**lean_error:** tail step 1/1 ('simp [Prod.iSup]'): unknown constant 'Prod.iSup'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 3.7s, verify 0.1s, in=292, out=117)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [swap_iSup]
```

**lean_error:** tail step 1/1 ('rw [swap_iSup]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 4.2s, verify 0.1s, in=292, out=132)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact swap_iSup
```

**lean_error:** tail step 1/1 ('exact swap_iSup'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 5.1s, verify 0.1s, in=292, out=135)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [swap_iSup']
```

**lean_error:** tail step 1/1 ("simp [swap_iSup']"): unknown identifier 'swap_iSup''

### `stepk:1` · qwen3-lean-cot-r128 · rollout 6 → **incomplete**  (gen 9.0s, verify 0.1s, in=292, out=256)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [iSup, swap]
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

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 11.8s, verify 0.1s, in=292, out=339)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [iSup_prod, swap]
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

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 11.9s, verify 0.1s, in=292, out=366)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iSup, swap_iSup]
```

**lean_error:** tail step 1/1 ('rw [iSup, swap_iSup]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 12.9s, verify 0.1s, in=292, out=396)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [iSup_prod_mk, swap_prod_mk]
```

**lean_error:** tail step 1/1 ('simp only [iSup_prod_mk, swap_prod_mk]'): unknown identifier 'iSup_prod_mk'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 15.0s, verify 0.1s, in=292, out=455)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.5s, verify 0.1s, in=1106, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [iSup, Prod.swap_sSup, Set.range_comp]
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

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.6s, verify 0.1s, in=1106, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [iSup, swap_sSup, range_comp]
```

**lean_error:** tail step 1/1 ('simp_rw [iSup, swap_sSup, range_comp]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.9s, verify 0.1s, in=1106, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup, swap_sSup, iSup, range_comp, image_image]
```

**lean_error:** tail step 1/1 ('rw [iSup, swap_sSup, iSup, range_comp, image_image]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 4.1s, verify 0.1s, in=1106, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup, Prod.swap_sSup, Set.range_comp, iSup, Prod.swap]
```

**lean_error:** tail step 1/1 ('rw [iSup, Prod.swap_sSup, Set.range_comp, iSup, Prod.swap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 9.2s, verify 0.1s, in=1106, out=290)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [iSup, Prod.swap_sSup, Set.range_comp, Function.comp]
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

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 9.9s, verify 0.1s, in=1106, out=312)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup, Prod.swap_sSup, ← Set.range_comp, Function.comp]
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

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 11.4s, verify 0.1s, in=1106, out=354)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup, iSup, Prod.swap_sSup, ← Set.range_comp]
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

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **incomplete**  (gen 12.5s, verify 0.1s, in=1106, out=360)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup, Prod.swap_sSup, ← Set.range_comp, Function.comp]
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

### `hint:2` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 13.4s, verify 0.1s, in=1106, out=297)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup, Prod.swap_sSup, ← Function.comp, Set.range_comp]
```

**lean_error:** tail step 1/1 ('rw [iSup, Prod.swap_sSup, ← Function.comp, Set.range_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 14.3s, verify 0.1s, in=1106, out=301)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [iSup, Prod.swap_sSup, Set.range_comp, Function.comp]
```

**lean_error:** tail step 1/1 ('simp_rw [iSup, Prod.swap_sSup, Set.range_comp, Function.comp]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 15.9s, verify 0.1s, in=1106, out=323)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup, Prod.swap_sSup, Set.range_comp, Function.comp]
```

**lean_error:** tail step 1/1 ('rw [iSup, Prod.swap_sSup, Set.range_comp, Function.comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 7 → **incomplete**  (gen 20.7s, verify 0.1s, in=1106, out=280)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [iSup, Prod.swap_sSup, Set.range_comp, Function.comp]
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

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.8s, verify 0.1s, in=2511, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [iSup, swap_sSup, range_comp]
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

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.1s, verify 0.1s, in=2511, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [iSup, swap_sSup, range_comp]
```

**lean_error:** tail step 1/1 ('simp_rw [iSup, swap_sSup, range_comp]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.1s, verify 0.1s, in=2511, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [iSup, iSup, Prod.swap_sSup, Set.range_comp]
```

**lean_error:** tail step 1/1 ('rw [iSup, iSup, Prod.swap_sSup, Set.range_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.4s, verify 0.1s, in=2511, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [iSup, iSup, Prod.swap_sSup, Set.range_comp]
```

**lean_error:** tail step 1/1 ('rw [iSup, iSup, Prod.swap_sSup, Set.range_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 22.5s, verify 0.1s, in=2511, out=213)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
aesop
```

**lean_error:** tail step 1/1 ('aesop'): tactic 'aesop' failed, made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 25.1s, verify 0.1s, in=2511, out=311)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [iSup, Prod.swap_sSup, Set.range_comp, Function.comp]
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

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 27.2s, verify 0.1s, in=2511, out=330)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [iSup, Prod.swap_sSup, ← iSup, Set.range_comp]
```

**lean_error:** tail step 1/1 ('rw [iSup, Prod.swap_sSup, ← iSup, Set.range_comp]'): failed to rewrite using equation theorems for 'iSup'

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 28.5s, verify 0.1s, in=2511, out=282)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [iSup, iSup, Prod.swap_sSup, Set.range_comp]
```

**lean_error:** tail step 1/1 ('rw [iSup, iSup, Prod.swap_sSup, Set.range_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 4 → **incomplete**  (gen 28.9s, verify 0.1s, in=2511, out=238)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [iSup, Prod.swap_sSup, Set.range_comp, Function.comp]
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

### `hint:3` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 29.3s, verify 0.1s, in=2511, out=229)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [iSup, Prod.swap_sSup, ← Function.comp, range_comp]
```

**lean_error:** tail step 1/1 ('rw [iSup, Prod.swap_sSup, ← Function.comp, range_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 30.2s, verify 0.1s, in=2511, out=273)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [iSup, swap_sSup, Set.range_comp, Function.comp]
```

**lean_error:** tail step 1/1 ('simp_rw [iSup, swap_sSup, Set.range_comp, Function.comp]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 30.7s, verify 0.1s, in=2511, out=250)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [iSup, iSup, swap_sSup, Set.range_comp, Function.comp]
```

**lean_error:** tail step 1/1 ('rw [iSup, iSup, swap_sSup, Set.range_comp, Function.comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.6s, verify 0.1s, in=2531, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iSup, iSup, Prod.swap_sSup, Set.range_comp]
```

**lean_error:** tail step 1/1 ('rw [iSup, iSup, Prod.swap_sSup, Set.range_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.8s, verify 0.1s, in=2531, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [iSup, swap_sSup, range_comp, image_image, iSup]
```

**lean_error:** tail step 1/1 ('simp_rw [iSup, swap_sSup, range_comp, image_image, iSup]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.3s, verify 0.1s, in=2531, out=30)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iSup, Prod.swap_sSup, Set.range_comp, image_comp, Prod.swap_comp_swap, iSup]
```

**lean_error:** tail step 1/1 ('rw [iSup, Prod.swap_sSup, Set.range_comp, image_comp, Prod.swap_comp_swap, iSup]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 3.9s, verify 0.1s, in=2531, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [iSup, swap_sSup, range_comp]
```

**lean_error:** tail step 1/1 ('simp_rw [iSup, swap_sSup, range_comp]'): simp made no progress

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 19.0s, verify 0.1s, in=2531, out=229)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iSup, Prod.swap_sSup, ← Set.range_comp, iSup]
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

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 21.1s, verify 0.1s, in=2531, out=268)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa only [iSup, Prod.swap_sSup, Set.range_comp, Function.comp]
```

**lean_error:** tail step 1/1 ('simpa only [iSup, Prod.swap_sSup, Set.range_comp, Function.comp]'): tactic 'assumption' failed

### `noise:3` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 21.6s, verify 0.1s, in=2531, out=249)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [iSup, Prod.swap_sSup, Set.range_comp, Function.comp]
```

**lean_error:** tail step 1/1 ('simp_rw [iSup, Prod.swap_sSup, Set.range_comp, Function.comp]'): simp made no progress

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 22.9s, verify 0.1s, in=2531, out=359)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iSup, Prod.swap_sSup, ← Set.range_comp, Function.comp]
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

### `noise:3` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 23.1s, verify 0.1s, in=2531, out=305)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iSup, Prod.swap_sSup, ← Function.comp, Set.range_comp]
```

**lean_error:** tail step 1/1 ('rw [iSup, Prod.swap_sSup, ← Function.comp, Set.range_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 23.3s, verify 0.1s, in=2531, out=300)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iSup, Prod.swap_sSup, ← Function.comp, Set.range_comp]
```

**lean_error:** tail step 1/1 ('rw [iSup, Prod.swap_sSup, ← Function.comp, Set.range_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 25.2s, verify 0.1s, in=2531, out=241)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iSup, iSup, swap_sSup, Set.range_comp, Function.comp]
```

**lean_error:** tail step 1/1 ('rw [iSup, iSup, swap_sSup, Set.range_comp, Function.comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 26.8s, verify 0.1s, in=2531, out=390)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iSup, Prod.swap_sSup, iSup, Set.range_comp, Function.comp]
```

**lean_error:** tail step 1/1 ('rw [iSup, Prod.swap_sSup, iSup, Set.range_comp, Function.comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
