# List.insertNth_eq_insertNthTR   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/List/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp [insertNthTR, insertNthTR_go_eq]
```

**True premises at k:** `List.insertNthTR`, `List.insertNthTR_go_eq`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✓ | ✓ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.2s, in=248, out=39)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l generalizing n
case nil => rfl
case cons x xs h' =>
  cases f
  case zero => rfl
  case succ f' => apply h'
```

**lean_error:** tail step 2/6 ('case nil => rfl'): type mismatch

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=222, out=70)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l generalizing n
case nil =>
  simp [insertNth, insertNthTR]
case cons a l IH =>
  simp only [insertNth, insertNthTR]
  cases n
  · simp
  · apply congr_arg _ (IH _)
    simp [Nat.succ_eq_add_one]
```

**lean_error:** tail step 2/9 ('case nil =>'): <stdin>:1:11: unexpected end of input; expected '{'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=237, out=28)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l with _ _ IH
refl
simp [insertNth, insertNthTR, IH]
```

**lean_error:** tail step 1/3 ('induction l with _ _ IH'): <stdin>:1:17: expected '|'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.6s, verify 0.1s, in=728, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold List.insertNthTR
simp [List.insertNthTR_go_eq]
done
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.2s, in=705, out=73)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
induction l generalizing n
case nil => simp [List.insertNth, List.insertNthTR]
case cons a l ih =>
  cases n
  case zero =>
    simp [List.insertNth, List.insertNthTR]
  case succ n =>
    simp [List.insertNth, List.insertNthTR, ih]
```

**lean_error:** tail step 2/8 ('case nil => simp [List.insertNth, List.insertNthTR]'): unsolved goals

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=717, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply List.insertNthTR_go_eq
simp [List.insertNth, List.insertNthTR]
```

**lean_error:** tail step 1/2 ('apply List.insertNthTR_go_eq'): tactic 'apply' failed, failed to unify

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=2060, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold List.insertNthTR
simp [List.insertNthTR_go_eq]
done
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=2055, out=73)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
induction l generalizing n
case nil => simp [List.insertNth, List.insertNthTR]
case cons a l ih =>
  cases n
  case zero =>
    simp [List.insertNth, List.insertNthTR]
  case succ n =>
    simp [List.insertNth, List.insertNthTR, ih]
```

**lean_error:** tail step 2/8 ('case nil => simp [List.insertNth, List.insertNthTR]'): unsolved goals

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=2049, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply List.insertNthTR_go_eq
simp [insertNthTR, insertNth]
```

**lean_error:** tail step 1/2 ('apply List.insertNthTR_go_eq'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=2085, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
unfold insertNthTR
simp [insertNthTR_go_eq]
```

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=2216, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [insertNthTR, insertNthTR_go_eq]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 1.0s, verify 0.1s, in=2074, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [insertNthTR, insertNth]
```

**final state (truncated):**
```
case h.h.h.h
α : Type u_1
f : Nat
n : α
l : List α
⊢ modifyNthTail (cons n) f l = insertNthTR.go n f l #[]
```
