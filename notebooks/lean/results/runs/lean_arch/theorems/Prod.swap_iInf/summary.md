# Prod.swap_iInf   (k=0, 1 tactics total)

file: `Mathlib/Order/CompleteLattice.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [iInf, swap_sInf, ← range_comp, Function.comp]
```

**True premises at k:** `iInf`, `Prod.swap_sInf`, `Set.range_comp`, `Function.comp`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | · | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **incomplete**  (gen 1.4s, verify 0.4s, in=315, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iInf, swap]
ext
simp [iInf, swap, Function.swap]
```

**final state (truncated):**
```
case a
α : Type u_1
β : Type u_2
β₂ : Type u_3
γ : Type u_4
ι : Sort u_5
...
```

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.2s, in=289, out=33)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
· simp only [iInf_fst, iInf_snd]
· simp only [iInf_fst, iInf_snd, swap]
```

**lean_error:** tail step 2/3 ('· simp only [iInf_fst, iInf_snd]'): unknown identifier 'iInf_fst'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=304, out=85)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply le_antisymm
· refine' iInf_le_of_le _ _
  intro i
  apply swap_le_swap_iff.mpr
  exact iInf_le f i
· refine' iInf_le_of_le _ _
  intro i
  apply swap_le_swap_iff.mp
  exact le_iInf (λ j, swap_le_swap_iff.mpr (le_iInf f j))
```

**lean_error:** tail step 1/9 ('apply le_antisymm'): failed to synthesize

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.2s, in=1125, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iInf, swap_sInf]
rw [Set.range_comp swap f]
rw [Function.comp]
```

**lean_error:** tail step 2/3 ('rw [Set.range_comp swap f]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 3.4s, verify 0.2s, in=1089, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iInf, iInf, Prod.swap_sInf, ← Set.range_comp]
simp_rw [Function.comp]
rfl
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=1114, out=49)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iInf, iInf, sInf_range, sInf_range, swap_sInf, Set.range_comp, Prod.swap_image_image_swap, Set.range_comp]
congr
exact Set.image_image_swap f
```

**lean_error:** tail step 1/3 ('rw [iInf, iInf, sInf_range, sInf_range, swap_sInf, Set.range_comp, Prod.swap_image_image_swap, Set.range_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.2s, in=2519, out=26)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [iInf, swap_sInf]
rw [Set.range_comp Function.swap]
rw [Set.image_comp Function.swap]
```

**lean_error:** tail step 2/3 ('rw [Set.range_comp Function.swap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 3.3s, verify 0.1s, in=2480, out=53)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext <| congr_arg sInf <| by simp_rw [← image_comp, Prod.swap, iInf, range_comp]
ext <| congr_arg sInf <| by simp_rw [← image_comp, Prod.swap, iInf, range_comp]
```

**lean_error:** tail step 1/2 ('ext <| congr_arg sInf <| by simp_rw [← image_comp, Prod.swap, iInf, range_comp]'): <stdin>:1:4: expected end of input

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=2508, out=67)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [iInf, swap_sInf, Set.range_comp, Function.comp, Set.range_comp, Function.comp]
```

**lean_error:** tail step 1/1 ('rw [iInf, swap_sInf, Set.range_comp, Function.comp, Set.range_comp, Function.comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.2s, in=2547, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iInf, swap_sInf]
rw [Set.range_comp Prod.swap]
rw [Function.comp]
```

**lean_error:** tail step 2/3 ('rw [Set.range_comp Prod.swap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 3.1s, verify 0.1s, in=2673, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iInf, iInf, swap_sInf, ← image_comp]
simp only [Function.comp, Prod.swap]
rw [range_comp]
```

**lean_error:** tail step 1/3 ('rw [iInf, iInf, swap_sInf, ← image_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 60.9s, verify 0.1s, in=2536, out=3849)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iInf, swap_sInf, Set.range_comp]
```

**lean_error:** tail step 1/1 ('rw [iInf, swap_sInf, Set.range_comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
