# antitone_dual_iff   (k=0, 1 tactics total)

file: `Mathlib/Order/Monotone/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

**True premises at k:** `antitone_toDual_comp_iff`, `monotone_comp_ofDual_iff`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✓ | ✓ |
| `noise:3` | ✘ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.2s, in=310, out=73)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h a b hab
  convert h (ofDual a) (ofDual b) _ using 2
  simpa only [toDual_ofDual]
· intro h a b hab
  convert h (toDual a) (toDual b) _ using 2
  simpa only [ofDual_toDual]
```

**lean_error:** tail step 2/7 ('· intro h a b hab'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.4s, in=280, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Antitone, Antitone, Function.comp]
simp only [toDual_le_toDual, ofDual_le_ofDual]
rfl
```

**lean_error:** tail step 3/3 ('rfl'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 94.9s, verify 0.2s, in=299, out=5897)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold Antitone
split
· intro h; intros; apply h; rw [le_dual]; assumption
· intro h; intros; rw [le_dual]; apply h; assumption
```

**lean_error:** tail step 2/4 ('split'): tactic 'split' failed

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=635, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Equiv.comp_assoc],
exact antitone_toDual_comp_iff.trans monotone_comp_ofDual_iff,
```

**lean_error:** tail step 1/2 ('rw [Equiv.comp_assoc],'): <stdin>:1:21: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=585, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← antitone_toDual_comp_iff, ← monotone_comp_ofDual_iff]
rfl
```

**lean_error:** tail step 1/2 ('rw [← antitone_toDual_comp_iff, ← monotone_comp_ofDual_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 11.5s, verify 0.8s, in=624, out=652)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=967, out=28)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Equiv.comp_assoc toDual ofDual]
rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

**lean_error:** tail step 1/2 ('rw [Equiv.comp_assoc toDual ofDual]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=917, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 12.8s, verify 0.1s, in=956, out=735)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=990, out=35)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Equiv.toFun_as_coe, Equiv.toFun_as_coe]
rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

**lean_error:** tail step 1/2 ('rw [Equiv.toFun_as_coe, Equiv.toFun_as_coe]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=978, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=979, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```
