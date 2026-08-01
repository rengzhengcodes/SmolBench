# symmDiff_eq_iff_sdiff_eq   (k=1, 2 tactics total)

file: `Mathlib/Order/SymmDiff.lean`  

**Ground-truth tail (from k):**
```lean
exact ((symmDiff_right_involutive a).toPerm _).apply_eq_iff_eq_symm_apply.trans eq_comm
```

**True premises at k:** `symmDiff_right_involutive`, `Function.Involutive.toPerm`, `eq_comm`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.2s, in=274, out=54)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  refine' (cancel_bsupr a c ha b).mpr _
  rwa [←h]
· intro h
  refine' (cancel_bsupr a c ha b).mp _
  rwa [h]
```

**lean_error:** tail step 2/7 ('· intro h'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=242, out=86)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [symmDiff_eq_iff_sdiff_eq_and_sdiff_eq, symmDiff_eq_iff_sdiff_eq_and_sdiff_eq]
simp_rw [sdiff_eq_iff, sup_comm, inf_comm, and_comm]
exact ⟨fun ⟨h1, h2⟩ => ⟨ha.trans h1, h2⟩, fun ⟨h1, h2⟩ => ⟨h1, ha.trans h2⟩⟩
```

**lean_error:** tail step 1/3 ('rw [symmDiff_eq_iff_sdiff_eq_and_sdiff_eq, symmDiff_eq_iff_sdiff_eq_and_sdiff_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=263, out=18)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [delta_eq_iff, delta_eq_iff]
simp [ha]
```

**lean_error:** tail step 1/2 ('rw [delta_eq_iff, delta_eq_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=697, out=34)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Equiv.Perm.apply_inv_self (toPerm (a ∆ ·) (symmDiff_right_involutive a))]
rw [eq_comm]
```

**lean_error:** tail step 1/2 ('rw [Equiv.Perm.apply_inv_self (toPerm (a ∆ ·) (symmDiff_right_involutive a))]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=658, out=36)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [symmDiff_comm, eq_comm, ← symmDiff_assoc, symmDiff_right_involutive a]
simp only [symmDiff_idem]
```

**lean_error:** tail step 1/2 ('simp_rw [symmDiff_comm, eq_comm, ← symmDiff_assoc, symmDiff_right_involutive a]'): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 80.1s, verify 0.1s, in=686, out=5079)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_right_involutive, apply_toPerm, inv_apply_eq, eq_comm]
```

**lean_error:** tail step 1/1 ('rw [symmDiff_right_involutive, apply_toPerm, inv_apply_eq, eq_comm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1061, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_right_involutive c, Function.Involutive.toPerm, Equiv.Perm.inv_left],
exact eq_comm
```

**lean_error:** tail step 1/2 ('rw [symmDiff_right_involutive c, Function.Involutive.toPerm, Equiv.Perm.inv_left],'): <stdin>:1:81: expected end of input

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1020, out=40)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [symmDiff_right_involutive a, Function.Involutive.toPerm _ (symmDiff_right_involutive a).apply_eq_iff] 
rw [eq_comm]
```

**lean_error:** tail step 1/2 ('simp_rw [symmDiff_right_involutive a, Function.Involutive.toPerm _ (symmDiff_right_involutive a).apply_eq_iff]'): simp made no progress

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=1050, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_right_involutive, Function.Involutive.toPerm, eq_comm]
```

**lean_error:** tail step 1/1 ('rw [symmDiff_right_involutive, Function.Involutive.toPerm, eq_comm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=1086, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Equiv.Perm.apply_inv_self (toPerm _ (symmDiff_right_involutive _))]
exact eq_comm
```

**lean_error:** tail step 1/2 ('rw [Equiv.Perm.apply_inv_self (toPerm _ (symmDiff_right_involutive _))]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1091, out=36)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [symmDiff_right_involutive a, Function.Involutive.toPerm_apply, eq_comm]
simp only [symmDiff_eq_iff_sdiff_eq]
```

**lean_error:** tail step 1/2 ('simp_rw [symmDiff_right_involutive a, Function.Involutive.toPerm_apply, eq_comm]'): simp made no progress

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1075, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact eq_comm
```

**lean_error:** tail step 1/1 ('exact eq_comm'): type mismatch
