# Nat.gcd_gcd_self_left_right   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/Nat/Gcd.lean`  

**Ground-truth tail (from k):**
```lean
rw [gcd_comm, gcd_gcd_self_right_right]
```

**True premises at k:** `Nat.gcd_comm`, `Nat.gcd_gcd_self_right_right`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=221, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [gcd_assoc]
rw [gcd_comm]
rw [gcd_same]
```

**lean_error:** tail step 3/3 ('rw [gcd_same]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=195, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Nat.gcd_comm n m, Nat.gcd_assoc]
rw [Nat.gcd_comm m n]
rfl
```

**lean_error:** tail step 3/3 ('rfl'): type mismatch

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=210, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [gcd_comm, gcd_gcd_left]
```

**lean_error:** tail step 1/1 ('rw [gcd_comm, gcd_gcd_left]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.2s, verify 0.1s, in=576, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Nat.gcd_comm]
exact Nat.gcd_gcd_self_right_right _ _
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=549, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Nat.gcd_comm]
apply Nat.gcd_gcd_self_right_right
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=565, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [gcd_comm, gcd_gcd_self_right_right]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.2s, verify 0.1s, in=1426, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Nat.gcd_comm, Nat.gcd_gcd_self_right_right]
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=1403, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Nat.gcd_comm]
simp only [Nat.gcd_gcd_self_right_right]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=1415, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [gcd_comm n m]
exact gcd_gcd_self_right_right m n
```

**lean_error:** tail step 2/2 ('exact gcd_gcd_self_right_right m n'): type mismatch

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=1450, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Nat.gcd_comm m (Nat.gcd n m)]
rw [Nat.gcd_gcd_self_right_right]
```

**lean_error:** tail step 1/2 ('rw [Nat.gcd_comm m (Nat.gcd n m)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.2s, in=1522, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Nat.gcd_comm]
exact Nat.gcd_gcd_self_right_right n m
```

**lean_error:** tail step 2/2 ('exact Nat.gcd_gcd_self_right_right n m'): type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=1439, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [gcd_comm n m]
exact gcd_gcd_self_right_right n m
```

**lean_error:** tail step 2/2 ('exact gcd_gcd_self_right_right n m'): type mismatch
