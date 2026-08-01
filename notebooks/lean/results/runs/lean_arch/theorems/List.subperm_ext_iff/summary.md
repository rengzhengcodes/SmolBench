# List.subperm_ext_iff   (k=3, 4 tactics total)

file: `.lake/packages/std/Std/Data/List/Perm.lean`  

**Ground-truth tail (from k):**
```lean
exact perm_append_comm.trans (subperm_append_diff_self_of_count_le h)
```

**True premises at k:** `List.subperm_append_diff_self_of_count_le`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 1.9s, in=281, out=61)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h' := h,
apply perm_ext (λ x, by
  rw [count_append, count_diff_self, add_comm]),
intro x,
cases h' x with h'x h'x,
{ exact h'x },
exact Nat.sub_add_cancel (h'x rfl)
```

**lean_error:** tail step 1/7 ("have h' := h,"): <stdin>:1:12: expected end of input

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=256, out=28)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [List.diff_comm]
exact Perm.symm this
rw [List.perm_append_comm]
exact List.subperm_to_perm this
```

**lean_error:** tail step 1/4 ('rw [List.diff_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=270, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply list.perm_ext
intro x
rw [count_append, count_diff_of_le h, add_comm]
```

**lean_error:** tail step 1/3 ('apply list.perm_ext'): unknown identifier 'list.perm_ext'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=765, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact List.subperm_append_diff_self_of_count_le h
rw [Perm.append_comm]
```

**lean_error:** tail step 1/2 ('exact List.subperm_append_diff_self_of_count_le h'): type mismatch

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=746, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [List.diff_comm]
exact subperm_append_diff_self_of_count_le h
exact Perm.symm this
```

**lean_error:** tail step 1/3 ('rw [List.diff_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=754, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply subperm_append_diff_self_of_count_le h
```

**lean_error:** tail step 1/1 ('apply subperm_append_diff_self_of_count_le h'): tactic 'apply' failed, failed to unify

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1802, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact subperm_append_diff_self_of_count_le h
done
```

**lean_error:** tail step 1/2 ('exact subperm_append_diff_self_of_count_le h'): type mismatch

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1800, out=40)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact subperm_append_diff_self_of_count_le h
rw [← List.diff_append_comm, List.append_comm]
exact Perm.subperm (List.diff_append_self_perm l₂.diff l₁)
```

**lean_error:** tail step 1/3 ('exact subperm_append_diff_self_of_count_le h'): type mismatch

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1791, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply subperm_append_diff_self_of_count_le h
```

**lean_error:** tail step 1/1 ('apply subperm_append_diff_self_of_count_le h'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1827, out=13)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact subperm_append_diff_self_of_count_le h
done
```

**lean_error:** tail step 1/2 ('exact subperm_append_diff_self_of_count_le h'): type mismatch

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=1929, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact subperm_append_diff_self_of_count_le h
rw [← List.diff_append_comm]
exact Perm.refl _
```

**lean_error:** tail step 1/3 ('exact subperm_append_diff_self_of_count_le h'): type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=1816, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply subperm_append_diff_self_of_count_le h
```

**lean_error:** tail step 1/1 ('apply subperm_append_diff_self_of_count_le h'): tactic 'apply' failed, failed to unify
