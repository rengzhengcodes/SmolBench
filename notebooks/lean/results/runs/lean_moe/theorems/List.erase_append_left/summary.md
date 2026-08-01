# List.erase_append_left   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
exact eraseP_append_left (beq_self_eq_true a) l₂ h
```

**True premises at k:** `List.eraseP_append_left`, `beq_self_eq_true`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 21.5s, verify 1.4s, in=350, out=4921)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l₁ with
  | nil =>
      cases h
  | cons hd tl ih =>
      cases h with
      | inl h_eq =>
          subst h_eq
          simp [List.eraseP_cons, List.append_assoc]
      | inr h_mem =>
          by_cases h_eq : a == hd
          · have : a = hd := (LawfulBEq.eq_of_beq_eq_true (a:=a) (b:=hd) h_eq)
            subst this
            simp [List.eraseP_cons, List.append_assoc, ih]
          · simp [List.eraseP_cons, h_eq, List.append_assoc, ih]
```

**lean_error:** tail step 1/14 ('induction l₁ with'): <stdin>:1:17: unexpected end of input; expected '|'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.4s, verify 0.1s, in=803, out=2274)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have pa : (fun x => a == x) a := by
    simpa [beq_self_eq_true]
  simpa using (List.eraseP_append_left (p:=fun x => a == x) (a:=a) pa (l₂:=l₂) h)
```

**lean_error:** tail step 1/3 ('have pa : (fun x => a == x) a := by'): <stdin>:1:35: unexpected end of input; expected '{'

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 12.1s, verify 0.1s, in=1698, out=2408)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [beq_self_eq_true] using
  (eraseP_append_left (p := fun x => a == x) (a := a)
    (by
      simpa [beq_self_eq_true])
    (l₁ := l₁) (l₂ := l₂) h)
```

**lean_error:** tail step 1/5 ('simpa [beq_self_eq_true] using'): <stdin>:1:30: unexpected end of input

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.9s, verify 0.1s, in=1621, out=1700)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have pa : (fun x => a == x) a := by
  simpa using (beq_self_eq_true a)
simpa using (eraseP_append_left (a:=a) (p:=fun x => a == x) pa (l₂:=l₂) h)
```

**lean_error:** tail step 1/3 ('have pa : (fun x => a == x) a := by'): <stdin>:1:35: unexpected end of input; expected '{'
