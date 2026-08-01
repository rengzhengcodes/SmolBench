# List.range_add   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simpa [range_eq_range', Nat.add_comm] using (range'_append_1 0 a b).symm
```

**True premises at k:** `List.range_eq_range'`, `Nat.add_comm`, `List.range'_append_1`, `Eq.symm`

## Verdict matrix

| rung | llama-31-405b-base |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 0.9s, verify 0.8s, in=227, out=24)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [range_eq_range']
rw [range'_eq_range'']
rw [range''_eq_append_range']
```

**lean_error:** tail step 2/3 ("rw [range'_eq_range'']"): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.7s, verify 0.2s, in=227, out=54)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [range_eq_range', range_eq_range' a]
rw [range'_eq_range'_offset]
rw [add_comm]
rw [range'_split]
rw [range'_eq_range'_offset]
rw [zero_add]
rw [range'_eq_range]
```

**lean_error:** tail step 2/7 ("rw [range'_eq_range'_offset]"): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 2.9s, verify 0.3s, in=227, out=62)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [range_eq_range']
rw [range_eq_range' a]
rw [Nat.add_comm]
rw [range'_eq_range'']
rw [range'_eq_range'' a]
rw [Nat.add_comm] at range''
rw [range_eq_range'']
rw [range_eq_range'' a]
```

**lean_error:** tail step 4/8 ("rw [range'_eq_range'']"): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 3.2s, verify 0.1s, in=227, out=73)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [range_eq_range']
rw [range_eq_range' a] at range' a b
rw [range_eq_range']
rw [Nat.add_comm] at range' a b
rw [range'_eq_range]
rw [Nat.add_comm] at range' a b
rw [range_eq_range']
exact (range_split a b).symm
```

**lean_error:** tail step 2/8 ("rw [range_eq_range' a] at range' a b"): unexpected term '@List.range''; expected single reference to variable

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.2s, in=1058, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [range_eq_range', Nat.add_comm a b]
rw [range'_append_1 0 a b]
apply Eq.symm
```

**lean_error:** tail step 2/3 ("rw [range'_append_1 0 a b]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.9s, verify 0.3s, in=1058, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [range_eq_range', Nat.add_comm a b]
rw [range'_append_1 0 a b]
apply Eq.symm
```

**lean_error:** tail step 2/3 ("rw [range'_append_1 0 a b]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 2.2s, verify 0.2s, in=1058, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [range_eq_range']
rw [Nat.add_comm]
rw [range'_append_1]
rw [Nat.add_comm]
apply Eq.symm
```

**lean_error:** tail step 3/5 ("rw [range'_append_1]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 2.5s, verify 0.2s, in=1058, out=45)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [range_eq_range' (a + b)]
rw [Nat.add_comm a b]
rw [range'_append_1 0 a b]
apply Eq.symm
rw [Nat.add_comm a b]
```

**lean_error:** tail step 3/5 ("rw [range'_append_1 0 a b]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
