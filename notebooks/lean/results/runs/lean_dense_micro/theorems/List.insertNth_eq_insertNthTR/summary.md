# List.insertNth_eq_insertNthTR   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/List/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp [insertNthTR, insertNthTR_go_eq]
```

**True premises at k:** `List.insertNthTR`, `List.insertNthTR_go_eq`

## Verdict matrix

| rung | llama-31-405b-base |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.5s, verify 0.3s, in=248, out=54)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l generalizing n
case nil => rfl
case cons x xs =>
  cases f
  case zero => rfl
  case succ f =>
    simp [insertNth, insertNthTR]
    apply congrArg
    apply ih_xs
```

**lean_error:** tail step 2/9 ('case nil => rfl'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=248, out=51)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l generalizing n
case nil => rfl
case cons x xs h => 
  cases f
  case zero => rfl
  case succ f => 
    simp [insertNth, insertNthTR]
    apply h
```

**lean_error:** tail step 2/8 ('case nil => rfl'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 2.0s, verify 0.2s, in=248, out=57)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l generalizing n
case nil => rfl
case cons x xs h => 
  cases f
  case zero => rfl
  case succ f => 
    simp only [insertNth, insertNthTR]
    apply congrArg
    exact h
```

**lean_error:** tail step 2/9 ('case nil => rfl'): type mismatch

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 2.2s, verify 0.2s, in=248, out=56)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l generalizing n
case nil => rfl
case cons x xs hxs =>
  cases f
  case zero => rfl
  case succ f =>
    simp [insertNth, insertNthTR]
    apply congrArg
    apply hxs
```

**lean_error:** tail step 2/9 ('case nil => rfl'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 1 → **success**  (gen 0.6s, verify 0.1s, in=728, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [insertNthTR, insertNthTR_go_eq]
```

### `hint:2` · llama-31-405b-base · rollout 3 → **success**  (gen 0.7s, verify 0.2s, in=728, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold insertNthTR
simp [insertNthTR_go_eq]
```

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 0.8s, verify 0.2s, in=728, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold List.insertNthTR
simp [List.insertNthTR_go_eq]
done
```

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 2.4s, verify 0.1s, in=728, out=62)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
cases n
case zero => simp [insertNth, insertNthTR, insertNthTR.go]
case succ n =>
  simp [insertNth, insertNthTR]
  apply insertNthTR_go_eq
  simp [Array.toList, Array.toListAppend, List.append]
```

**lean_error:** tail step 1/6 ('cases n'): tactic 'induction' failed, major premise type is not an inductive type 
