# List.range_add   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simpa [range_eq_range', Nat.add_comm] using (range'_append_1 0 a b).symm
```

**True premises at k:** `List.range_eq_range'`, `Nat.add_comm`, `List.range'_append_1`, `Eq.symm`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | · | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.2s, in=227, out=34)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [range_eq_range', range_eq_range' a]
rw [range'_eq_range'_offset]
rw [Nat.add_comm]
rw [range'_append]
```

**lean_error:** tail step 2/4 ("rw [range'_eq_range'_offset]"): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=201, out=39)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction a
simp [Nat.add_succ, range_succ, range'_succ, add_assoc, Nat.zero_add, range'_zero, add_zero, *]
simp [*]
```

**lean_error:** tail step 2/3 ("simp [Nat.add_succ, range_succ, range'_succ, add_assoc, Nat.zero_add, range'_zero, add_zero, *]"): unknown identifier 'range'_succ'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 107.0s, verify 0.1s, in=216, out=6552)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction a; simp [range_succ, range'_succ, *]
```

**lean_error:** tail step 1/1 ("induction a; simp [range_succ, range'_succ, *]"): <stdin>:1:11: expected end of input

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.2s, in=1058, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [range_eq_range', Nat.add_comm a b]
rw [range'_append_1 0 a b]
apply Eq.symm
```

**lean_error:** tail step 2/3 ("rw [range'_append_1 0 a b]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=1032, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [range_eq_range']
simp [Nat.add_comm, range'_append_1]
```

**lean_error:** tail step 2/2 ("simp [Nat.add_comm, range'_append_1]"): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.1s, in=1047, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [range_eq_range', range_eq_range', ← range'_append_1 0 a b, add_comm]
```

**lean_error:** tail step 1/1 ("rw [range_eq_range', range_eq_range', ← range'_append_1 0 a b, add_comm]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.2s, in=4096, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [range_eq_range', Nat.add_comm a b]
rw [range'_append_1 0 a b]
apply Eq.symm
```

**lean_error:** tail step 2/3 ("rw [range'_append_1 0 a b]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.7s, verify 0.1s, in=4095, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [range_eq_range']
simp [Nat.add_comm a b, range'_append_1]
```

**final state (truncated):**
```
a b : Nat
⊢ range' 0 (b + a) = range a ++ range' a b
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=4085, out=33)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [range_eq_range', range'_append_1 0 a b, add_comm, add_comm b a, Eq.symm]
```

**lean_error:** tail step 1/1 ("rw [range_eq_range', range'_append_1 0 a b, add_comm, add_comm b a, Eq.symm]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.2s, in=4121, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [range_eq_range', Nat.add_comm a b]
rw [range'_append_1 0 a b]
apply Eq.symm
```

**lean_error:** tail step 2/3 ("rw [range'_append_1 0 a b]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.2s, in=4445, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [range_eq_range']
simp only [Nat.add_comm a b, range'_append_1]
rfl
```

**lean_error:** tail step 3/3 ('rfl'): type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=4110, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [range_eq_range', ← range'_append_1, add_comm, add_comm b a, range'_eq_map_range]
```

**lean_error:** tail step 1/1 ("rw [range_eq_range', ← range'_append_1, add_comm, add_comm b a, range'_eq_map_range]"): tactic 'rewrite' failed, equality or iff proof expected
