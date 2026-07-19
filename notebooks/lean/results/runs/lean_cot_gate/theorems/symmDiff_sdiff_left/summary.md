# symmDiff_sdiff_left   (k=0, 1 tactics total)

file: `Mathlib/Order/SymmDiff.lean`  

**Ground-truth tail (from k):**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_idem, sdiff_sdiff_self, bot_sup_eq]
```

**True premises at k:** `symmDiff_def`, `sup_sdiff`, `sdiff_idem`, `sdiff_sdiff_self`, `bot_sup_eq`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ · ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✘ ✓ ✘ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `noise:3` | ✓ ✓ ✘ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 82.6s, verify 0.1s, in=238, out=3413)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [symmDiff_eq], 
rw [sdiff_union], 
simp,
```

**lean_error:** tail step 1/3 ('rw [symmDiff_eq],'): <stdin>:1:16: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 110.7s, verify 0.1s, in=238, out=4539)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [symmDiff_eq_sup_sdiff]
rw [sdiff_union_sdiff_left]
rw [sdiff_sdiff_self_left]
rw [sdiff_sdiff_self_right]
rw [sup_empty_left]
```

**lean_error:** tail step 1/5 ('rw [symmDiff_eq_sup_sdiff]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 173.4s, verify 0.1s, in=238, out=7237)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw symmDiff_eq_union_sdiff
rw sdiff_union
congr
· rw sdiff_sdiff_left
  exact sdiff_eq_bot_iff_le.mpr (sup_ge_left a b)
· rw sdiff_sdiff_left
  rw sup_self
```

**lean_error:** tail step 1/7 ('rw symmDiff_eq_union_sdiff'): <stdin>:1:3: expected '['

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 180.3s, verify 0.1s, in=238, out=7561)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [symm_diff_eq, sdiff_union]
rw [sdiff_sdiff_right]
rw [sup_comm]
rw [sdiff_self_sup]
rw [sdiff_sdiff_self]
rw [bot_sup_eq]
```

**lean_error:** tail step 1/6 ('rw [symm_diff_eq, sdiff_union]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=238, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [symmDiff_eq, sup_sdiff]
```

**lean_error:** tail step 1/1 ('simp [symmDiff_eq, sup_sdiff]'): unknown identifier 'symmDiff_eq'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.3s, verify 0.1s, in=238, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [sdiff, symmDiff, inf_comm, sup_inf_sdiff]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
π : ι → Type u_4
inst✝ : GeneralizedBooleanAlgebra α
a b c d : α
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.5s, verify 0.1s, in=238, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [symmDiff_eq_sup_sdiff_inf, sup_sdiff_self_left, bot_sdiff]
```

**lean_error:** tail step 1/1 ('rw [symmDiff_eq_sup_sdiff_inf, sup_sdiff_self_left, bot_sdiff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.0s, verify 0.1s, in=238, out=34)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [symmDiff_eq_sup_sdiff_inf, sup_sdiff_self_right, inf_sdiff_self_right, sdiff_bot_eq_self]
```

**lean_error:** tail step 1/1 ('rw [symmDiff_eq_sup_sdiff_inf, sup_sdiff_self_right, inf_sdiff_self_right, sdiff_bot_eq_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 13.5s, verify 0.1s, in=238, out=388)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [sdiff_sdiff_left, sdiff_sdiff_left]
```

**lean_error:** tail step 1/1 ('simp [sdiff_sdiff_left, sdiff_sdiff_left]'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 14.3s, verify 0.1s, in=238, out=415)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [symmDiff, iSup_or, iInf_self, iInf_bot, iInf_sup, iSup_bot]
```

**lean_error:** tail step 1/1 ('simp only [symmDiff, iSup_or, iInf_self, iInf_bot, iInf_sup, iSup_bot]'): unknown identifier 'iSup_or'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 16.0s, verify 0.1s, in=238, out=472)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sdiff_sdiff_comm, sdiff_sdiff_right, sup_sdiff, sup_sdiff, sup_sdiff_sup]
```

**lean_error:** tail step 1/1 ('rw [sdiff_sdiff_comm, sdiff_sdiff_right, sup_sdiff, sup_sdiff, sup_sdiff_sup]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 21.4s, verify 0.1s, in=238, out=726)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [symmDiff_eq_sup_sdiff_inf, sdiff_sdiff, sup_inf_right, sdiff_self, bot_sdiff]
```

**lean_error:** tail step 1/1 ('rw [symmDiff_eq_sup_sdiff_inf, sdiff_sdiff, sup_inf_right, sdiff_self, bot_sdiff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 42.3s, verify 0.4s, in=849, out=1699)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_def]
rw [sup_sdiff]
rw [sdiff_sdiff_self]
rw [sdiff_idem]
rw [bot_sup_eq]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 45.2s, verify 0.2s, in=849, out=1812)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff]
rw [sdiff_sdiff_self, sdiff_idem]
rw bot_sup_eq
```

**lean_error:** tail step 3/3 ('rw bot_sup_eq'): <stdin>:1:3: expected '['

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 55.1s, verify 0.1s, in=849, out=2257)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 56.0s, verify 0.1s, in=849, out=2291)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw symmDiff_def
rw sup_sdiff
rw [sdiff_sdiff_self, sdiff_idem]
rw bot_sup_eq
```

**lean_error:** tail step 1/4 ('rw symmDiff_def'): <stdin>:1:3: expected '['

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.6s, verify 0.1s, in=849, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [symmDiff_def, sup_sdiff, sdiff_sdiff_self, bot_sup_eq, sdiff_idem]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.8s, verify 0.1s, in=849, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, bot_sup_eq, sdiff_idem]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.6s, verify 0.1s, in=849, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.7s, verify 0.1s, in=849, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, bot_sup_eq, sdiff_idem]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 8.4s, verify 0.1s, in=849, out=226)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 8.5s, verify 0.1s, in=849, out=226)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 8.8s, verify 0.1s, in=849, out=230)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 9.7s, verify 0.1s, in=849, out=258)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 59.0s, verify 0.1s, in=1777, out=1642)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 95.6s, verify 0.1s, in=1777, out=3459)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 128.5s, verify 0.1s, in=1777, out=3580)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 137.1s, verify 0.1s, in=1777, out=5266)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.8s, verify 0.1s, in=1777, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [symmDiff_def, sup_sdiff, sdiff_sdiff_self, bot_sup_eq, sdiff_idem]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.9s, verify 0.1s, in=1777, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, bot_sup_eq, sdiff_idem]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.9s, verify 0.1s, in=1777, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [symmDiff_def, sup_sdiff, sdiff_sdiff_self, bot_sup_eq, sdiff_idem]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 3.0s, verify 0.1s, in=1777, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [symmDiff_def, sup_sdiff, sdiff_sdiff_self, bot_sup_eq, sdiff_idem]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 15.6s, verify 0.1s, in=1777, out=230)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 15.9s, verify 0.1s, in=1777, out=242)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 16.9s, verify 0.1s, in=1777, out=280)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 18.1s, verify 0.1s, in=1777, out=319)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 9.6s, verify 0.4s, in=1795, out=391)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_def]
rw [sup_sdiff]
rw [sdiff_sdiff_self]
rw [sdiff_idem]
rw [bot_sup_eq]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 11.8s, verify 0.4s, in=1795, out=478)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_def]
rw [sup_sdiff]
rw [sdiff_sdiff_self]
rw [sdiff_idem]
rw [bot_sup_eq]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 18.6s, verify 0.2s, in=1795, out=754)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff]
rw [sdiff_sdiff_self, sdiff_idem]
rw bot_sup_eq
```

**lean_error:** tail step 3/3 ('rw bot_sup_eq'): <stdin>:1:3: expected '['

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 50.9s, verify 0.1s, in=1795, out=2084)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.7s, verify 0.1s, in=1795, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.9s, verify 0.1s, in=1795, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, bot_sup_eq, sdiff_idem]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.9s, verify 0.1s, in=1795, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [symmDiff_def, sup_sdiff, sdiff_sdiff_self, bot_sup_eq, sdiff_idem]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.1s, verify 0.5s, in=1795, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, bot_sup_eq, sdiff_idem]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 8.5s, verify 0.1s, in=1795, out=226)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 8.9s, verify 0.1s, in=1795, out=231)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 9.7s, verify 0.1s, in=1795, out=255)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 10.8s, verify 0.1s, in=1795, out=294)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_def, sup_sdiff, sdiff_sdiff_self, sdiff_idem, bot_sup_eq]
```
