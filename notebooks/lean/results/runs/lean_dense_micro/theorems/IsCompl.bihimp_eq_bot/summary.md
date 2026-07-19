# IsCompl.bihimp_eq_bot   (k=0, 1 tactics total)

file: `Mathlib/Order/SymmDiff.lean`  

**Ground-truth tail (from k):**
```lean
rw [h.eq_compl, compl_bihimp_self]
```

**True premises at k:** `compl_bihimp_self`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 0.6s, verify 0.1s, in=264, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [IsCompl.iff_eq_bot h]
```

**lean_error:** tail step 1/1 ('rw [IsCompl.iff_eq_bot h]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.9s, verify 0.1s, in=264, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Iff_eq_eq_iff]
rw [h.eq_bot]
```

**lean_error:** tail step 1/2 ('rw [Iff_eq_eq_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=264, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h.compl_iff, iff_self],
exact bot_eq ⊥
```

**lean_error:** tail step 1/2 ('rw [h.compl_iff, iff_self],'): <stdin>:1:26: expected end of input

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=264, out=60)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Iff, h.symm.inf_eq_bot]
rw [h.symm.sup_eq_top]
rw [Compl.compl_sup_bot]
rw [Compl.bot_sup_compl]
rw [inf_bot_eq]
rw [sup_bot_eq] 
rw [Compl.bot_unique]
```

**lean_error:** tail step 1/7 ('rw [Iff, h.symm.inf_eq_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 2.6s, verify 0.1s, in=264, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Iff, h.eq_bot, h.eq_bot]
```

**lean_error:** tail step 1/1 ('rw [Iff, h.eq_bot, h.eq_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 2.9s, verify 0.1s, in=264, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h.1.eq_bot, h.2.eq_bot, biheyting.iff_bot]
```

**lean_error:** tail step 1/1 ('rw [h.1.eq_bot, h.2.eq_bot, biheyting.iff_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 3.0s, verify 0.1s, in=264, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h.1, h.2, isCompl_bot_top.inf_eq, isCompl_bot_top.imp_eq]
```

**lean_error:** tail step 1/1 ('rw [h.1, h.2, isCompl_bot_top.inf_eq, isCompl_bot_top.imp_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 3.1s, verify 0.1s, in=264, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h.1.eq_bot, h.2.eq_bot, inf_bot_eq, bot_sup_eq, imp_bot, bot_imp]
```

**lean_error:** tail step 1/1 ('rw [h.1.eq_bot, h.2.eq_bot, inf_bot_eq, bot_sup_eq, imp_bot, bot_imp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=449, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h.compl_bihimp_self b]
```

**lean_error:** tail step 1/1 ('rw [h.compl_bihimp_self b]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.7s, verify 0.1s, in=449, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h.compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [h.compl_bihimp_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.8s, verify 0.1s, in=449, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [IsCompl.compl_bihimp_self h]
```

**lean_error:** tail step 1/1 ('rw [IsCompl.compl_bihimp_self h]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=449, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [IsCompl.compl_eq h],
exact compl_bihimp_self
```

**lean_error:** tail step 1/2 ('rw [IsCompl.compl_eq h],'): <stdin>:1:23: expected end of input

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 0.9s, verify 1.6s, in=449, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← h.compl_eq, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [← h.compl_eq, compl_bihimp_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 2.5s, verify 0.1s, in=449, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← h.compl_unique, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [← h.compl_unique, compl_bihimp_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 2.7s, verify 0.1s, in=449, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h.compl_unique, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [h.compl_unique, compl_bihimp_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 2.8s, verify 0.1s, in=449, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h.compl_bihimp_self, h.symm.compl_eq]
```

**lean_error:** tail step 1/1 ('rw [h.compl_bihimp_self, h.symm.compl_eq]'): tactic 'rewrite' failed, equality or iff proof expected
