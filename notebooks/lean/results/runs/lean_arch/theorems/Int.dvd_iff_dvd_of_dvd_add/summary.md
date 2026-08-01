# Int.dvd_iff_dvd_of_dvd_add   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/Int/DivMod.lean`  

**Ground-truth tail (from k):**
```lean
rw [Int.dvd_iff_dvd_of_dvd_sub H, Int.dvd_neg]
```

**True premises at k:** `Int.dvd_iff_dvd_of_dvd_sub`, `Int.dvd_neg`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.2s, in=228, out=48)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · intro h
    rw [← Int.sub_add_cancel b c]
    exact H.add h
  · intro h
    rw [Int.sub_eq_add_neg, Int.add_comm]
    exact H.add h
```

**lean_error:** tail step 2/7 ('· intro h'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=197, out=37)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [dvd_iff_dvd_sub, sub_eq_neg_add] at H
rw [← H, dvd_neg, dvd_iff_dvd_neg]
exact Iff.rfl
```

**lean_error:** tail step 1/3 ('rw [dvd_iff_dvd_sub, sub_eq_neg_add] at H'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 16.8s, verify 0.1s, in=217, out=1009)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split ; intro h ; exact dvd_sub H h
```

**lean_error:** tail step 1/1 ('split ; intro h ; exact dvd_sub H h'): <stdin>:1:6: expected end of input

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=642, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Int.dvd_iff_dvd_of_dvd_sub H
```

**lean_error:** tail step 1/1 ('exact Int.dvd_iff_dvd_of_dvd_sub H'): application type mismatch

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.1s, in=597, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Int.dvd_iff_dvd_of_dvd_sub H
```

**lean_error:** tail step 1/1 ('exact Int.dvd_iff_dvd_of_dvd_sub H'): application type mismatch

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=631, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Int.dvd_iff_dvd_of_dvd_sub
exact H
```

**lean_error:** tail step 2/2 ('exact H'): type mismatch

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1752, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Int.dvd_iff_dvd_of_dvd_sub H
```

**lean_error:** tail step 1/1 ('exact Int.dvd_iff_dvd_of_dvd_sub H'): application type mismatch

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=1692, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Int.dvd_iff_dvd_of_dvd_sub H
```

**lean_error:** tail step 1/1 ('exact Int.dvd_iff_dvd_of_dvd_sub H'): application type mismatch

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1741, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Int.dvd_iff_dvd_of_dvd_sub
exact H
```

**lean_error:** tail step 2/2 ('exact H'): type mismatch

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1777, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Int.dvd_iff_dvd_of_dvd_sub H
```

**lean_error:** tail step 1/1 ('exact Int.dvd_iff_dvd_of_dvd_sub H'): application type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=1861, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Int.dvd_iff_dvd_of_dvd_sub H]
rw [Int.dvd_neg]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=1766, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Int.dvd_iff_dvd_of_dvd_sub H
```

**lean_error:** tail step 1/1 ('exact Int.dvd_iff_dvd_of_dvd_sub H'): application type mismatch
