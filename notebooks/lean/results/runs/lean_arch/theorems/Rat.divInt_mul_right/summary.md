# Rat.divInt_mul_right   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/Rat/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [← divInt_mul_left (d := d) a0, Int.mul_comm]
```

**True premises at k:** `Rat.divInt_mul_left`, `Int.mul_comm`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✓ | ✓ |
| `noise:3` | ✓ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=234, out=43)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [mul_comm d a]
rw [mul_assoc]
rw [Int.ediv_mul_cancel a0]
rw [Int.mul_ediv_assoc a0]
rw [Int.mul_ediv_cancel a0]
```

**lean_error:** tail step 1/5 ('rw [mul_comm d a]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 3.7s, verify 0.1s, in=208, out=34)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Int.ediv_mul_cancel (mul_ne_zero a0 a0)]
rw [Int.mul_ediv_cancel_left (mul_ne_zero a0 a0)]
```

**lean_error:** tail step 1/2 ('rw [Int.ediv_mul_cancel (mul_ne_zero a0 a0)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=223, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply eq_div_div_eq_div_cancel_left
apply a0
```

**lean_error:** tail step 1/2 ('apply eq_div_div_eq_div_cancel_left'): unknown identifier 'eq_div_div_eq_div_cancel_left'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=600, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Int.mul_comm n a, Rat.divInt_mul_left a0]
```

**lean_error:** tail step 1/1 ('rw [Int.mul_comm n a, Rat.divInt_mul_left a0]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 2.9s, in=567, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Int.mul_comm a n]
exact Rat.divInt_mul_left a0
```

**lean_error:** tail step 1/2 ('rw [Int.mul_comm a n]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 40.9s, verify 0.1s, in=589, out=2517)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Int.mul_comm n a, Int.mul_comm d a]
apply divInt_mul_left a0
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1509, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Int.mul_comm n a, Rat.divInt_mul_left a0]
```

**lean_error:** tail step 1/1 ('rw [Int.mul_comm n a, Rat.divInt_mul_left a0]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 3.4s, verify 0.2s, in=1470, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Int.mul_comm n a, Int.mul_comm d a]
exact Rat.divInt_mul_left a0
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 13.6s, verify 0.2s, in=1498, out=836)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Int.mul_comm n a, Int.mul_comm d a]
apply divInt_mul_left
exact a0
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=1533, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Int.mul_comm n a, Int.mul_comm d a]
exact Rat.divInt_mul_left a0
```

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 3.5s, verify 0.1s, in=1604, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Int.mul_comm n a, Int.mul_comm d a]
exact Rat.divInt_mul_left a0
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 15.1s, verify 0.2s, in=1522, out=929)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Int.mul_comm]
apply divInt_mul_left
exact a0
```

**lean_error:** tail step 2/3 ('apply divInt_mul_left'): tactic 'apply' failed, failed to unify
