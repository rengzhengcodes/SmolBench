# IsCompl.bihimp_eq_bot   (k=0, 1 tactics total)

file: `Mathlib/Order/SymmDiff.lean`  

**Ground-truth tail (from k):**
```lean
rw [h.eq_compl, compl_bihimp_self]
```

**True premises at k:** `compl_bihimp_self`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=264, out=40)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Iff, h.symm.inf_eq_bot, h.symm.sup_eq_top, inf_bot_eq, sup_top_eq]
rw [imp_bot, imp_top]
exact top_ne_bot
```

**lean_error:** tail step 1/3 ('rw [Iff, h.symm.inf_eq_bot, h.symm.sup_eq_top, inf_bot_eq, sup_top_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.1s, in=233, out=35)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [isCompl_iff, compl_eq_bot, hinf_eq_left, hnot_eq_right] at h
simp [h.1, h.2]
```

**lean_error:** tail step 1/2 ('rw [isCompl_iff, compl_eq_bot, hinf_eq_left, hnot_eq_right] at h'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=253, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h.compl_iff]
```

**lean_error:** tail step 1/1 ('rw [h.compl_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=449, out=11)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h.compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [h.compl_bihimp_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=408, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [bihimp_eq_compl_symmDiff, h.symmDiff_eq_bot, compl_compl]
```

**lean_error:** tail step 1/1 ('rw [bihimp_eq_compl_symmDiff, h.symmDiff_eq_bot, compl_compl]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=438, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h.bihimp_eq_bot]
```

**lean_error:** tail step 1/1 ('rw [h.bihimp_eq_bot]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=558, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsCompl.compl_bihimp_self]
rw [h.compl_eq]
```

**lean_error:** tail step 1/2 ('rw [IsCompl.compl_bihimp_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=516, out=28)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [bihimp_iff, h.symmDiff_eq_bot, h.compl_eq]
simp only [compl_bihimp_self]
```

**lean_error:** tail step 1/2 ('rw [bihimp_iff, h.symmDiff_eq_bot, h.compl_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 15.9s, verify 0.1s, in=547, out=957)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [compl_bihimp_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.1s, in=582, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h.eq_compl],
exact compl_bihimp_self
```

**lean_error:** tail step 1/2 ('rw [h.eq_compl],'): <stdin>:1:15: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 1.1s, in=552, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [bihimp, h.symm, h.compl_eq_bot.symm, bot_sdiff]
simp
```

**lean_error:** tail step 1/2 ('rw [bihimp, h.symm, h.compl_eq_bot.symm, bot_sdiff]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=571, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h.bihimp_eq_bot]
```

**lean_error:** tail step 1/1 ('rw [h.bihimp_eq_bot]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'
