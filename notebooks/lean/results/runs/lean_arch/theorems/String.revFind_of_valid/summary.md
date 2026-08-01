# String.revFind_of_valid   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/String/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simpa using revFindAux_of_valid p s.1.reverse []
```

**True premises at k:** `String.revFindAux_of_valid`, `List.reverse`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | · |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.7s, verify 0.2s, in=288, out=69)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold revFind
rw [StringImp.data_eq]
unfold utf8Rev
rw [Option.map_map]
rw [List.map_tail]
rw [List.map_dropWhile]
rw [List.map_reverse]
rw [List.map_map]
rw [StringImp.length_eq]
rw [List.length_map]
rw [List.length_reverse]
congr
```

**lean_error:** tail step 2/12 ('rw [StringImp.data_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.2s, in=262, out=52)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [revFind]
simp [utf8Len]
rw [← List.dropWhile_reverse_eq_dropWhile]
simp [List.dropWhile_eq_nil_iff]
rw [List.dropWhile_reverse_eq_dropWhile]
simp [List.tail?_dropWhile]
rfl
```

**lean_error:** tail step 2/7 ('simp [utf8Len]'): tactic 'simp' failed, nested error:

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=277, out=37)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply congrArg
exact (congrFun (List.reverse_dropWhile _).symm _)
simp [utf8Len, List.tail?, revFind]
```

**lean_error:** tail step 1/3 ('apply congrArg'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.3s, in=843, out=42)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold revFind String.revFindAux
rw [String.revFindAux_of_valid]
unfold List.tail?
rw [Option.map_map]
simp [fun x => { byteIdx := utf8Len x }]
```

**lean_error:** tail step 2/5 ('rw [String.revFindAux_of_valid]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 1.8s, in=812, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold revFind
simp only [revFindAux_of_valid, List.reverse_reverse]
rfl
```

**lean_error:** tail step 2/3 ('simp only [revFindAux_of_valid, List.reverse_reverse]'): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 1.5s, verify 0.3s, in=832, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold String.revFind
rw [← revFindAux_of_valid p (List.reverse s.data) []]
simp [List.reverse_reverse]
```

**final state (truncated):**
```
p : Char → Bool
s : String
⊢ revFindAux s p (endPos s) = revFindAux { data := s.data } p { byteIdx := utf8Len s.data }
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.3s, in=2583, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold revFind String.revFindAux
rw [String.revFindAux_of_valid]
unfold String.utf8Len
simp [List.reverse]
```

**lean_error:** tail step 2/4 ('rw [String.revFindAux_of_valid]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.3s, in=2553, out=32)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold revFind
simp [revFindAux_of_valid, List.reverse]
rw [List.dropWhile_reverse (!·)]
simp [utf8Len]
```

**lean_error:** tail step 3/4 ('rw [List.dropWhile_reverse (!·)]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=2572, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold revFind
rw [reverse_reverse]
exact revFindAux_of_valid p [] s.data
```

**lean_error:** tail step 2/3 ('rw [reverse_reverse]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.3s, in=2609, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
unfold revFind String.revFindAux
rw [List.reverse_reverse]
exact String.revFindAux_of_valid p s.data []
```

**lean_error:** tail step 2/3 ('rw [List.reverse_reverse]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.7s, verify 0.2s, in=2776, out=40)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
unfold revFind
simp [revFindAux_of_valid, List.reverse_append]
simp [String.data_eq]
rw [List.dropWhile_reverse (!p ·)]
simp [List.reverse_reverse]
```

**lean_error:** tail step 2/5 ('simp [revFindAux_of_valid, List.reverse_append]'): simp made no progress

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 1.0s, verify 0.3s, in=2598, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
unfold revFind
rw [← revFindAux_of_valid p (s.data.reverse) []]
simp [List.reverse_reverse]
```

**final state (truncated):**
```
p : Char → Bool
s : String
⊢ revFindAux s p (endPos s) = revFindAux { data := s.data } p { byteIdx := utf8Len s.data }
```
