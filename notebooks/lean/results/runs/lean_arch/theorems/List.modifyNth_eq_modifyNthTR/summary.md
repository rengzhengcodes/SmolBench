# List.modifyNth_eq_modifyNthTR   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/List/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp [modifyNthTR, modifyNthTR_go_eq]
```

**True premises at k:** `List.modifyNthTR`, `List.modifyNthTR_go_eq`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✘ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.2s, in=250, out=63)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction n generalizing l
case zero =>
  cases l
  case nil => rfl
  case cons x xs => rfl
case succ n ih =>
  cases l
  case nil => rfl
  case cons x xs => simp [modifyNth, modifyNthTR, ih]
```

**lean_error:** tail step 2/9 ('case zero =>'): <stdin>:1:12: unexpected end of input; expected '{'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=224, out=53)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l generalizing n with
| nil => rfl
| cons a l IH =>
  cases n with
  | zero => rfl
  | succ n => simp [modifyNth, modifyNthTR]; congr; apply IH
```

**lean_error:** tail step 1/6 ('induction l generalizing n with'): <stdin>:1:31: unexpected end of input; expected '|'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=239, out=53)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l with
| nil => rfl
| cons hd tl => cases n with
  | zero => rfl
  | succ n => dsimp [modifyNth, modifyNthTR]; congr; apply ih_tl
```

**lean_error:** tail step 1/5 ('induction l with'): <stdin>:1:16: unexpected end of input; expected '|'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=749, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold List.modifyNthTR
simp [List.modifyNthTR_go_eq _ _ #[]]
```

**lean_error:** tail step 2/2 ('simp [List.modifyNthTR_go_eq _ _ #[]]'): function expected at

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=725, out=73)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
induction l generalizing n
case nil =>
  cases n <;> simp [modifyNth, modifyNthTR]
case cons head tail ih =>
  cases n
  case zero =>
    simp [modifyNth, modifyNthTR]
  case succ n =>
    simp [modifyNth, modifyNthTR, ih n]
```

**lean_error:** tail step 2/9 ('case nil =>'): <stdin>:1:11: unexpected end of input; expected '{'

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=738, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply modifyNthTR_go_eq
```

**lean_error:** tail step 1/1 ('apply modifyNthTR_go_eq'): tactic 'apply' failed, failed to unify

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.1s, verify 0.1s, in=1981, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold List.modifyNthTR
simp [List.modifyNthTR_go_eq]
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=1976, out=70)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
induction l generalizing n
case nil => cases n <;> simp [modifyNth, modifyNthTR]
case cons head tail ih =>
  cases n
  case zero => simp [modifyNth, modifyNthTR]
  case succ n => simp [modifyNth, modifyNthTR, ih n]
```

**lean_error:** tail step 2/6 ('case nil => cases n <;> simp [modifyNth, modifyNthTR]'): unsolved goals

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1970, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply modifyNthTR_go_eq
simp [modifyNthTR]
```

**lean_error:** tail step 1/2 ('apply modifyNthTR_go_eq'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=2006, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [modifyNthTR]
exact modifyNthTR_go_eq _ _ #[]
```

**lean_error:** tail step 2/2 ('exact modifyNthTR_go_eq _ _ #[]'): function expected at

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=2125, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [modifyNthTR, modifyNthTR_go_eq, List.nil_append]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1995, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply modifyNthTR_go_eq
simp [modifyNthTR]
```

**lean_error:** tail step 1/2 ('apply modifyNthTR_go_eq'): tactic 'apply' failed, failed to unify
