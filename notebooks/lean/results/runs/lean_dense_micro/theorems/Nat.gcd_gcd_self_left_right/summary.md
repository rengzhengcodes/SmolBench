# Nat.gcd_gcd_self_left_right   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/Nat/Gcd.lean`  

**Ground-truth tail (from k):**
```lean
rw [gcd_comm, gcd_gcd_self_right_right]
```

**True premises at k:** `Nat.gcd_comm`, `Nat.gcd_gcd_self_right_right`

## Verdict matrix

| rung | llama-31-405b-base |
| --- | --- |
| `stepk:1` | ✘ · · ✘ |
| `hint:2` | ✘ ✓ ✓ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=221, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Nat.gcd_assoc]
rw [Nat.gcd_comm]
rw [Nat.gcd_idem]
```

**lean_error:** tail step 3/3 ('rw [Nat.gcd_idem]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 2 → **incomplete**  (gen 1.2s, verify 0.3s, in=221, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [gcd_assoc]
rw [gcd_comm]
rw [gcd_self]
```

**final state (truncated):**
```
m n : Nat
⊢ gcd m n = gcd n m
```

### `stepk:1` · llama-31-405b-base · rollout 1 → **incomplete**  (gen 1.5s, verify 0.6s, in=221, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [gcd_assoc]
rw [gcd_comm]
rw [gcd_comm m]
rw [gcd_self]
```

**final state (truncated):**
```
m n : Nat
⊢ gcd m n = gcd n m
```

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 2.3s, verify 0.2s, in=221, out=33)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [gcd_assoc]
rw [gcd_comm m]
rw [gcd_comm (gcd m n)] 
rw [gcd_self] 
rw [gcd_comm]
```

**lean_error:** tail step 3/5 ('rw [gcd_comm (gcd m n)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.7s, verify 0.1s, in=576, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [gcd_comm m (gcd n m), gcd_gcd_self_right_right]
```

**lean_error:** tail step 1/1 ('rw [gcd_comm m (gcd n m), gcd_gcd_self_right_right]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=576, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Nat.gcd_comm]
exact Nat.gcd_gcd_self_right_right _ _
```

### `hint:2` · llama-31-405b-base · rollout 3 → **success**  (gen 2.1s, verify 0.1s, in=576, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [gcd_comm (gcd n m) m]
rw [gcd_gcd_self_right_right m n]
```

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 2.2s, verify 0.1s, in=576, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Nat.gcd_comm m (gcd n m)]
exact Nat.gcd_gcd_self_right_right m n
```

**lean_error:** tail step 1/2 ('rw [Nat.gcd_comm m (gcd n m)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
