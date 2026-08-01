# List.Sublist.erase   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
exact Sublist.eraseP h
```

**True premises at k:** `List.Sublist.eraseP`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✓ |
| `hint:3` | ✓ | ✓ | · |
| `noise:3` | ✓ | ✓ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 7.5s, verify 0.1s, in=294, out=248)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l₂ with
| nil => contradiction
| cons x xs =>
  cases h with
  | inl h => cases h; exact List.sublist.cons _ _ _ (List.sublist.refl _)
  | inr h =>
    cases heq : x == a with
    | true =>
      have : List.eraseP (fun x => a == x) (x :: xs) = List.eraseP (fun x => a == x) xs :=
        by simp [List.eraseP, heq]
      simp only [List.eraseP_cons, heq]
      exact List.sublist.cons _ _ _ (ih _ h)
    | false =>
      have : List.eraseP (fun x => a == x) (x :: xs) = x :: List.eraseP (fun x => a == x) xs :=
        by simp [List.eraseP, heq]
      simp only [List.eraseP_cons, heq]
      cases h with
      | inl h => cases h; exact List.sublist.cons _ _ _ (List.sublist.refl _)
      | inr h => exact List.sublist.cons _ _ _ (ih _ h)
```

**lean_error:** tail step 1/19 ('induction l₂ with'): <stdin>:1:17: unexpected end of input; expected '|'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=271, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [List.eraseP_eq_erase]
rw [List.eraseP_eq_erase]
exact List.erase_sublist_erase h
```

**lean_error:** tail step 1/3 ('rw [List.eraseP_eq_erase]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=283, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply list.sublist.eraseP
exact h
```

**lean_error:** tail step 1/2 ('apply list.sublist.eraseP'): unknown identifier 'list.sublist.eraseP'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=560, out=8)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact List.Sublist.eraseP h
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=538, out=7)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Sublist.eraseP h
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=549, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Sublist.eraseP
exact h
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=765, out=8)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact List.Sublist.eraseP h
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=742, out=8)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply List.Sublist.eraseP h
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.6s, verify 0.1s, in=754, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Sublist.eraseP
```

**final state (truncated):**
```
case a
α : Type u_1
inst✝¹ : BEq α
inst✝ : LawfulBEq α
a : α
l₁ l₂ : List α
...
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=791, out=8)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact List.Sublist.eraseP h
```

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.3s, verify 0.1s, in=792, out=7)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Sublist.eraseP h
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 8.0s, verify 0.1s, in=780, out=479)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Sublist.eraseP
```

**final state (truncated):**
```
case a
α : Type u_1
inst✝¹ : BEq α
inst✝ : LawfulBEq α
a : α
l₁ l₂ : List α
...
```
