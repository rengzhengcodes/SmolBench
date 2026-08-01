# Prod.swap_iSup   (k=0, 1 tactics total)

file: `Mathlib/Order/CompleteLattice.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [iSup, swap_sSup, ← range_comp, Function.comp]
```

**True premises at k:** `iSup`, `Prod.swap_sSup`, `Set.range_comp`, `Function.comp`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | · | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✓ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=315, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold swap
rw iSup_prod
simp [swap]
```

**lean_error:** tail step 2/3 ('rw iSup_prod'): <stdin>:1:3: expected '['

### `stepk:1` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.3s, verify 0.2s, in=289, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext <;> simp [iSup]
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

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=304, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iSup, swap_sup, sup_iSup]
```

**lean_error:** tail step 1/1 ('rw [iSup, swap_sup, sup_iSup]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=1125, out=36)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup, iSup, Prod.swap_sSup],
rw [Set.range_comp swap f],
congr,
ext1 i,
simp only [Function.comp_apply]
```

**lean_error:** tail step 1/5 ('rw [iSup, iSup, Prod.swap_sSup],'): <stdin>:1:31: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=1089, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← sSup_range, ← sSup_range]
simp_rw [range_comp Prod.swap f, swap_sSup]
```

**lean_error:** tail step 2/2 ('simp_rw [range_comp Prod.swap f, swap_sSup]'): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 115.8s, verify 0.1s, in=1114, out=7334)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup, swap_sSup, Set.range_comp, Function.comp, Set.range_comp, Function.comp]
```

**lean_error:** tail step 1/1 ('rw [iSup, swap_sSup, Set.range_comp, Function.comp, Set.range_comp, Function.comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.2s, in=2519, out=28)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [iSup, swap_sSup]
rw [Set.range_comp Function.swap f]
rw [Set.image_comp Function.swap f]
```

**lean_error:** tail step 2/3 ('rw [Set.range_comp Function.swap f]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=2480, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [← iSup_range, ← range_comp, Prod.swap_sSup]
```

**lean_error:** tail step 1/1 ('simp_rw [← iSup_range, ← range_comp, Prod.swap_sSup]'): simp made no progress

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=2508, out=30)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [iSup, swap_sSup, Set.range_comp, Function.comp, Set.range_comp, Function.comp]
```

**lean_error:** tail step 1/1 ('rw [iSup, swap_sSup, Set.range_comp, Function.comp, Set.range_comp, Function.comp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=2547, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iSup, swap_sSup]
rw [Set.range_comp Prod.swap]
rw [iSup]
```

**lean_error:** tail step 2/3 ('rw [Set.range_comp Prod.swap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.2s, in=2673, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [iSup, Prod.swap_sSup, ← Set.range_comp]
simp [Function.comp]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 48.7s, verify 0.4s, in=2536, out=2997)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [iSup]
rw [swap_sSup]
rw [← Set.range_comp]
rw [iSup]
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
