# Prod.swap_iSup   (k=0, 1 tactics total)

file: `Mathlib/Order/CompleteLattice.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [iSup, swap_sSup, ← range_comp, Function.comp]
```

**True premises at k:** `iSup`, `Prod.swap_sSup`, `Set.range_comp`, `Function.comp`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.6s, verify 0.6s, in=315, out=39)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iSup, swap]
ext
simp [swap]
rw [iSup_lift'_eq_iSup_lift]
simp [swap]
rw [iSup_lift'_eq_iSup]
```

**lean_error:** tail step 4/6 ("rw [iSup_lift'_eq_iSup_lift]"): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 2.2s, verify 0.8s, in=315, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iSup, swap]
congr
funext i
rw [Prod.fst_swap, Prod.snd_swap]
```

**lean_error:** tail step 3/4 ('funext i'): tactic 'apply' failed, failed to unify

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.0s, verify 0.6s, in=315, out=35)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iSup, swap]
ext
simp [iSup, swap]
rw [←image_eq_range]
simp [iSup, swap]
apply iSup_image
```

**lean_error:** tail step 4/6 ('rw [←image_eq_range]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 3.6s, verify 0.3s, in=315, out=70)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [iSup, swap]
ext
simp only [Prod.fst, Prod.snd, swap, iSup, SupSet.supᵢ]
congr
· ext i
  simp only [SupSet.supᵢ, swap]
· ext i
  simp only [SupSet.supᵢ, swap]
```

**lean_error:** tail step 3/8 ('simp only [Prod.fst, Prod.snd, swap, iSup, SupSet.supᵢ]'): unknown constant 'SupSet.supᵢ'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=315, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [iSup, swap_iSup]
```

**lean_error:** tail step 1/1 ('simp_rw [iSup, swap_iSup]'): simp made no progress

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=315, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [iSup, swap_iSup, swap]
```

**lean_error:** tail step 1/1 ('simp_rw [iSup, swap_iSup, swap]'): simp made no progress

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=315, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [iSup, swap_iSup, swap_swap]
```

**lean_error:** tail step 1/1 ('simp_rw [iSup, swap_iSup, swap_swap]'): simp made no progress

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.1s, in=315, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [Prod.swap, iSup_prod, iSup_range]
```

**lean_error:** tail step 1/1 ('simp_rw [Prod.swap, iSup_prod, iSup_range]'): simp made no progress

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.2s, verify 0.2s, in=1125, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup, swap_sSup]
rw [Set.range_comp swap f]
rw [← iSup]
```

**lean_error:** tail step 2/3 ('rw [Set.range_comp swap f]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.4s, verify 0.1s, in=1125, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup, Prod.swap_sSup],
congr,
rw [Set.range_comp swap f],
refl
```

**lean_error:** tail step 1/4 ('rw [iSup, Prod.swap_sSup],'): <stdin>:1:25: expected end of input

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=1125, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup, swap_sSup, range_comp Prod.swap f]
exact sSup_congr (image_comp Prod.swap f : _)
```

**lean_error:** tail step 1/2 ('rw [iSup, swap_sSup, range_comp Prod.swap f]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.1s, in=1125, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup, iSup, Prod.swap_sSup],
rw [Set.range_comp Prod.swap f],
ext; congr_arg sSup; rfl
```

**lean_error:** tail step 1/3 ('rw [iSup, iSup, Prod.swap_sSup],'): <stdin>:1:31: expected end of input

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=1125, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [iSup, swap_sSup, range_comp swap]
```

**lean_error:** tail step 1/1 ('simp_rw [iSup, swap_sSup, range_comp swap]'): simp made no progress

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.3s, verify 0.1s, in=1125, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [iSup, swap_sSup, Set.range_comp]
```

**lean_error:** tail step 1/1 ('simp_rw [iSup, swap_sSup, Set.range_comp]'): simp made no progress

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.4s, verify 0.1s, in=1125, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [iSup, swap_sSup, range_comp swap]
```

**lean_error:** tail step 1/1 ('simp_rw [iSup, swap_sSup, range_comp swap]'): simp made no progress

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1125, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [iSup, iSup, swap_sSup, Set.range_comp Prod.swap]
```

**lean_error:** tail step 1/1 ('rw [iSup, iSup, swap_sSup, Set.range_comp Prod.swap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
