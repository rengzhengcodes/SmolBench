# Rat.divInt_mul_right   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/Rat/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [← divInt_mul_left (d := d) a0, Int.mul_comm]
```

**True premises at k:** `Rat.divInt_mul_left`, `Int.mul_comm`

## Verdict matrix

| rung | llama-31-405b-base |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.1s, verify 0.1s, in=234, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [mul_comm d a]
rw [mul_comm n a]
rw [Int.div_mul_div_cancel a0]
```

**lean_error:** tail step 1/3 ('rw [mul_comm d a]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 3.2s, verify 1.8s, in=234, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [mul_comm a, Int.mul_ediv_cancel_left a0]
rw [Int.ediv_mul_cancel_left a0]
```

**lean_error:** tail step 1/2 ('rw [mul_comm a, Int.mul_ediv_cancel_left a0]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 7.7s, verify 1.4s, in=234, out=33)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [mul_comm d a]
rw [Int.div_mul_cancel a0]
rw [mul_comm n a]
rw [Int.div_mul_cancel a0]
```

**lean_error:** tail step 1/4 ('rw [mul_comm d a]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 9.1s, verify 0.1s, in=234, out=42)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [mul_comm d a]
rw [mul_assoc]
rw [Int.ediv_mul_cancel a0]
rw [Int.mul_ediv_assoc]
rw [Int.mul_ediv_cancel_left a0]
```

**lean_error:** tail step 1/5 ('rw [mul_comm d a]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.7s, verify 2.1s, in=600, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Int.mul_comm]
apply Rat.divInt_mul_left a0
```

**lean_error:** tail step 2/2 ('apply Rat.divInt_mul_left a0'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.8s, verify 0.1s, in=600, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Int.mul_comm n a, Rat.divInt_mul_left a0]
```

**lean_error:** tail step 1/1 ('rw [Int.mul_comm n a, Rat.divInt_mul_left a0]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 2.9s, verify 0.1s, in=600, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Int.mul_comm a n]
exact Rat.divInt_mul_left a0
```

**lean_error:** tail step 1/2 ('rw [Int.mul_comm a n]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 4.9s, verify 2.7s, in=600, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Int.mul_comm a n]
rw [Int.mul_comm d a]
exact Rat.divInt_mul_left a0
```

**lean_error:** tail step 1/3 ('rw [Int.mul_comm a n]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
