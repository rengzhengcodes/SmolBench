# IsCompl.bihimp_eq_bot   (k=0, 1 tactics total)

file: `Mathlib/Order/SymmDiff.lean`  

**Ground-truth tail (from k):**
```lean
rw [h.eq_compl, compl_bihimp_self]
```

**True premises at k:** `compl_bihimp_self`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-goedel | qwen3-lean-leannav | qwen3-lean-real |
| --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✓ | ✘ | · |
| `hint:3` | ✘ | ✓ | ✓ | ✓ |
| `noise:3` | ✘ | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 190.7s, verify 0.1s, in=239, out=10726)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw h.eq_neg
dsimp only
rw [biEquiv, inf_imp, sup_compl_right]
exact inf_neg a
```

**lean_error:** tail step 1/4 ('rw h.eq_neg'): <stdin>:1:3: expected '['

### `stepk:1` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 2.4s, verify 1.0s, in=239, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [← h.eq_compl_iff, inf_compl_eq_bot, sup_compl_eq_top]
```

**lean_error:** tail step 1/1 ('simp [← h.eq_compl_iff, inf_compl_eq_bot, sup_compl_eq_top]'): invalid field 'eq_compl_iff', the environment does not contain 'IsCompl.eq_compl_iff'

### `stepk:1` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=239, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [← h.eq_compl_iff, inf_compl_eq_bot, sup_compl_eq_top]
```

**lean_error:** tail step 1/1 ('simp [← h.eq_compl_iff, inf_compl_eq_bot, sup_compl_eq_top]'): invalid field 'eq_compl_iff', the environment does not contain 'IsCompl.eq_compl_iff'

### `stepk:1` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=239, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [← h.eq_compl_iff, inf_compl_eq_bot, sup_compl_eq_top]
```

**lean_error:** tail step 1/1 ('simp [← h.eq_compl_iff, inf_compl_eq_bot, sup_compl_eq_top]'): invalid field 'eq_compl_iff', the environment does not contain 'IsCompl.eq_compl_iff'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 52.2s, verify 0.1s, in=416, out=2691)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h.compl_eq, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [h.compl_eq, compl_bihimp_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-goedel · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=416, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [← compl_bihimp_self, h.eq_compl]
```

### `hint:2` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=416, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [← compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('simp [← compl_bihimp_self]'): simp made no progress

### `hint:2` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 0.7s, verify 0.6s, in=416, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← compl_bihimp_self, h.compl_eq]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
π : ι → Type u_4
inst✝ : HeytingAlgebra α
a✝ a b : α
...
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 115.5s, verify 0.1s, in=526, out=6023)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw h.compl_eq
apply compl_bihimp_self
```

**lean_error:** tail step 1/2 ('rw h.compl_eq'): <stdin>:1:3: expected '['

### `hint:3` · qwen3-lean-goedel · rollout 0 → **success**  (gen 7.8s, verify 0.8s, in=526, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← compl_bihimp_self, h.eq_compl]
```

### `hint:3` · qwen3-lean-leannav · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=526, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← compl_bihimp_self, h.eq_compl]
```

### `hint:3` · qwen3-lean-real · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=526, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← compl_bihimp_self, h.eq_compl]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 61.3s, verify 0.1s, in=552, out=3171)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h.compl_eq]
apply compl_bihimp_self
```

**lean_error:** tail step 1/2 ('rw [h.compl_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-goedel · rollout 0 → **success**  (gen 8.7s, verify 0.5s, in=552, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [← compl_bihimp_self, h.eq_compl]
```

### `noise:3` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=552, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [← compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('simp [← compl_bihimp_self]'): simp made no progress

### `noise:3` · qwen3-lean-real · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=552, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [← compl_bihimp_self, h.eq_compl]
```
