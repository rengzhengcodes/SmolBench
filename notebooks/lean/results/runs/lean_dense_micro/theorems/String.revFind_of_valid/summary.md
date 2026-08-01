# String.revFind_of_valid   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/String/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simpa using revFindAux_of_valid p s.1.reverse []
```

**True premises at k:** `String.revFindAux_of_valid`, `List.reverse`

## Verdict matrix

| rung | llama-31-405b-base |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 2.3s, verify 0.2s, in=288, out=44)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [revFind]
rw [String.data_eq_of]
rw [utf8Len]
rw [Option.map_some']
rw [List.reverse_reverse]
rw [List.dropWhile]
rw [List.tail]
refl
```

**lean_error:** tail step 2/8 ('rw [String.data_eq_of]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.2s, in=288, out=54)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold revFind
rw [String.data_eq_of]
rw [← List.map_reverse]
rw [← List.dropWhile_map]
rw [List.map_map]
rw [utf8Len_eq]
rw [List.map_some_eq_map]
rw [Option.map_map]
```

**lean_error:** tail step 2/8 ('rw [String.data_eq_of]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 2.7s, verify 0.2s, in=288, out=71)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold revFind
rw [String.data_eq (revFind s p)]
rw [List.reverse_dropWhile]
rw [List.dropWhile_reverse]
rw [List.tail_reverse]
rw [List.head?_reverse]
rw [Option.map_comm]
rw [Option.map_some']
rw [List.head?_dropWhile]
rw [utf8Len]
```

**lean_error:** tail step 2/10 ('rw [String.data_eq (revFind s p)]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 3.0s, verify 0.2s, in=288, out=72)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [revFind]
rw [StringImp.data_eq]
rw [utf8Len]
rw [← List.map_reverse]
rw [← List.dropWhile_map]
rw [← Option.map_map]
rw [List.map_tail]
rw [List.map_map]
rw [List.map_eq_id]
rw [Option.map_id]
rw [Option.map_some']
```

**lean_error:** tail step 2/11 ('rw [StringImp.data_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.9s, verify 0.7s, in=843, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [revFind, revFindAux_of_valid]
simp [utf8Len, String.data]
```

**lean_error:** tail step 1/2 ('rw [revFind, revFindAux_of_valid]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.6s, verify 0.1s, in=843, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [revFind, revFindAux_of_valid]
simp [utf8Len, List.reverse]
```

**lean_error:** tail step 1/2 ('rw [revFind, revFindAux_of_valid]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.7s, verify 0.3s, in=843, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold String.revFind String.revFindAux
rw [List.reverse_reverse]
apply String.revFindAux_of_valid
simp
```

**lean_error:** tail step 2/4 ('rw [List.reverse_reverse]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.0s, verify 0.3s, in=843, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold revFind String.revFindAux
rw [String.revFindAux_of_valid]
unfold List.tail?
rw [Option.map_map]
simp
```

**lean_error:** tail step 2/5 ('rw [String.revFindAux_of_valid]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
