# IsCompl.bihimp_eq_bot   (k=0, 1 tactics total)

file: `Mathlib/Order/SymmDiff.lean`  

**Ground-truth tail (from k):**
```lean
rw [h.eq_compl, compl_bihimp_self]
```

**True premises at k:** `compl_bihimp_self`

## Verdict matrix

| rung | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✓ ✘ · | ✘ ✘ ✘ ✘ ✘ ✘ ✘ ✘ |
| `hint:3` | ✓ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ ✘ ✘ ✘ ✘ |
| `noise:3` | ✓ · ✘ ✓ | ✘ ✘ ✘ ✘ ✘ ✘ ✘ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.5s, verify 0.1s, in=239, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h.eq_compl, compl_iff_comm]
```

**lean_error:** tail step 1/1 ('rw [h.eq_compl, compl_iff_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.7s, verify 0.1s, in=239, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h.eq_bot, h.sup_eq_top]
```

**lean_error:** tail step 1/1 ('simp [h.eq_bot, h.sup_eq_top]'): invalid field 'eq_bot', the environment does not contain 'IsCompl.eq_bot'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=239, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← h.eq_compl, compl_iff_compl]
```

**lean_error:** tail step 1/1 ('rw [← h.eq_compl, compl_iff_compl]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 6.3s, verify 0.6s, in=239, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [biimp, h.inf_eq_bot, h.sup_eq_top, ite_true]
```

**lean_error:** tail step 1/1 ('rw [biimp, h.inf_eq_bot, h.sup_eq_top, ite_true]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 5.7s, verify 0.1s, in=239, out=176)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 7.5s, verify 0.1s, in=239, out=161)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h.iff_eq_bot, rfl]
```

**lean_error:** tail step 1/1 ('rw [h.iff_eq_bot, rfl]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 10.9s, verify 0.1s, in=239, out=344)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa only [h.eq_bot] using h.eq_bot
```

**lean_error:** tail step 1/1 ('simpa only [h.eq_bot] using h.eq_bot'): invalid field 'eq_bot', the environment does not contain 'IsCompl.eq_bot'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 11.9s, verify 0.1s, in=239, out=329)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [IsCompl.inf_eq_bot, inf_eq_bot_iff]
```

**lean_error:** tail step 1/1 ('rw [IsCompl.inf_eq_bot, inf_eq_bot_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 13.0s, verify 0.1s, in=239, out=397)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [bicond, h.inf_eq_bot, h.sup_eq_top, h.eq_compl_iff, h.eq_compl_iff.symm]
```

**lean_error:** tail step 1/1 ('simp only [bicond, h.inf_eq_bot, h.sup_eq_top, h.eq_compl_iff, h.eq_compl_iff.symm]'): unknown identifier 'bicond'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 13.9s, verify 0.1s, in=239, out=424)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [bicond, h.le_bot (le_inf_idem _), h.le_bot (le_inf_idem _), le_inf_comm, and_self,
  inf_eq_bot]
```

**lean_error:** tail step 1/2 ('rw [bicond, h.le_bot (le_inf_idem _), h.le_bot (le_inf_idem _), le_inf_comm, and_self,'): <stdin>:1:86: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 18.2s, verify 0.1s, in=239, out=551)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [h.eq_bot_iff, bicond, h.not_le.1, h.not_le.2, IsCompl.bot_iff]
```

**lean_error:** tail step 1/1 ('simp [h.eq_bot_iff, bicond, h.not_le.1, h.not_le.2, IsCompl.bot_iff]'): invalid field 'eq_bot_iff', the environment does not contain 'IsCompl.eq_bot_iff'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 18.8s, verify 0.1s, in=239, out=566)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [inf_eq_bot_iff_le_compl, le_compl_iff_disjoint_bot, disjoint_bot, h.inf_eq_bot]
```

**lean_error:** tail step 1/1 ('rw [inf_eq_bot_iff_le_compl, le_compl_iff_disjoint_bot, disjoint_bot, h.inf_eq_bot]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.6s, verify 0.1s, in=416, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [h.eq_compl_iff.2 rfl]
```

**lean_error:** tail step 1/1 ('simp [h.eq_compl_iff.2 rfl]'): invalid field 'eq_compl_iff', the environment does not contain 'IsCompl.eq_compl_iff'

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.9s, verify 0.1s, in=416, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h.eq_compl, compl_bihimp_self]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=416, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h.bihimp_eq, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [h.bihimp_eq, compl_bihimp_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.1s, verify 0.1s, in=416, out=19)

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

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 5.8s, verify 0.1s, in=416, out=185)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using compl_bihimp_self
```

**lean_error:** tail step 1/1 ('simpa using compl_bihimp_self'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 7.3s, verify 0.1s, in=416, out=233)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← h.compl_eq, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [← h.compl_eq, compl_bihimp_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 8.3s, verify 0.1s, in=416, out=264)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [← h.compl_eq, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('simp_rw [← h.compl_eq, compl_bihimp_self]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 10.6s, verify 0.1s, in=416, out=336)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [h.compl_eq, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('simp_rw [h.compl_eq, compl_bihimp_self]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 12.4s, verify 0.1s, in=416, out=198)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h.compl_eq, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [h.compl_eq, compl_bihimp_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 14.5s, verify 0.1s, in=416, out=256)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h.eq_compl, bihimp_comm, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [h.eq_compl, bihimp_comm, compl_bihimp_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 14.6s, verify 0.1s, in=416, out=211)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [h.eq_compl_iff.2 rfl]
```

**lean_error:** tail step 1/1 ('simp [h.eq_compl_iff.2 rfl]'): invalid field 'eq_compl_iff', the environment does not contain 'IsCompl.eq_compl_iff'

### `hint:2` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 17.9s, verify 0.1s, in=416, out=305)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [h.compl_eq, compl_bihimp_self, eq_comm]
```

**lean_error:** tail step 1/1 ('rw [h.compl_eq, compl_bihimp_self, eq_comm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.3s, verify 0.1s, in=526, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [h.eq_compl]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=526, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← compl_bihimp_self, h.compl_right]
```

**lean_error:** tail step 1/1 ('rw [← compl_bihimp_self, h.compl_right]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.5s, verify 0.1s, in=526, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h.bihimp_eq, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [h.bihimp_eq, compl_bihimp_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=526, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h.compl_eq, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [h.compl_eq, compl_bihimp_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 23.2s, verify 0.1s, in=526, out=244)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h.compl_eq, bihimp_comm, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [h.compl_eq, bihimp_comm, compl_bihimp_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 26.6s, verify 0.1s, in=526, out=204)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rwa [← compl_bihimp_self, bihimp_comm]
```

**lean_error:** tail step 1/1 ('rwa [← compl_bihimp_self, bihimp_comm]'): tactic 'assumption' failed

### `hint:3` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 27.4s, verify 0.1s, in=526, out=212)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h.compl_eq, bihimp_comm, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [h.compl_eq, bihimp_comm, compl_bihimp_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 27.9s, verify 0.1s, in=526, out=197)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h.eq_compl, bihimp_comm, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [h.eq_compl, bihimp_comm, compl_bihimp_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 28.6s, verify 0.1s, in=526, out=211)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [h.compl_eq, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [h.compl_eq, compl_bihimp_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 29.3s, verify 0.1s, in=526, out=299)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa only [h.compl_eq, eq_comm] using compl_bihimp_self
```

**lean_error:** tail step 1/1 ('simpa only [h.compl_eq, eq_comm] using compl_bihimp_self'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 32.3s, verify 0.1s, in=526, out=247)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rwa [← h.eq_compl, ← h.symm.eq_compl] at compl_bihimp_self
```

**lean_error:** tail step 1/1 ('rwa [← h.eq_compl, ← h.symm.eq_compl] at compl_bihimp_self'): unexpected term '@compl_bihimp_self'; expected single reference to variable

### `hint:3` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 34.7s, verify 0.1s, in=526, out=407)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact compl_bihimp_self.trans (h.symm.bihimp_comm.trans bot_eq_iff.mpr (h.symm.eq_compl.mpr rfl))
```

**lean_error:** tail step 1/1 ('exact compl_bihimp_self.trans (h.symm.bihimp_comm.trans bot_eq_iff.mpr (h.symm.eq_compl.mpr rfl))'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.5s, verify 0.1s, in=552, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [h.eq_compl]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.1s, verify 0.1s, in=552, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

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

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=552, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h.bihimp_eq, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [h.bihimp_eq, compl_bihimp_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 71.4s, verify 0.1s, in=552, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h.eq_compl, compl_bihimp_self]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 17.0s, verify 0.1s, in=552, out=128)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h.symm, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [h.symm, compl_bihimp_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 19.8s, verify 0.1s, in=552, out=256)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [h.compl_eq]
```

**lean_error:** tail step 1/1 ('simp [h.compl_eq]'): simp made no progress

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 20.1s, verify 0.1s, in=552, out=236)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa only [h.compl_eq] using compl_bihimp_self
```

**lean_error:** tail step 1/1 ('simpa only [h.compl_eq] using compl_bihimp_self'): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 22.8s, verify 0.1s, in=552, out=315)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h.eq_compl, bihimp_comm, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [h.eq_compl, bihimp_comm, compl_bihimp_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 22.9s, verify 0.1s, in=552, out=214)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rwa [h.compl_eq]
```

**lean_error:** tail step 1/1 ('rwa [h.compl_eq]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 24.3s, verify 0.1s, in=552, out=300)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← h.2, bihimp_comm, compl_bihimp_self]
```

**lean_error:** tail step 1/1 ('rw [← h.2, bihimp_comm, compl_bihimp_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 26.1s, verify 0.1s, in=552, out=293)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rwa [eq_comm, compl_bihimp_self] at h.symm.eq_compl
```

**lean_error:** tail step 1/1 ('rwa [eq_comm, compl_bihimp_self] at h.symm.eq_compl'): unexpected term 'IsCompl.eq_compl (IsCompl.symm h)'; expected single reference to variable

### `noise:3` · qwen3-lean-cot-r128 · rollout 5 → **success**  (gen 28.0s, verify 0.1s, in=552, out=249)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [h.eq_compl, compl_bihimp_self]
```
