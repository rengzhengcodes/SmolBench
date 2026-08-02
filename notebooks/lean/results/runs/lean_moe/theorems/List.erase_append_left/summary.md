# List.erase_append_left   (k=1, 2 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
exact eraseP_append_left (beq_self_eq_true a) l₂ h
```

**True premises at k:** `List.eraseP_append_left`, `beq_self_eq_true`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | · |
| `noise:3` | ✘ | ✘ | ✘ |

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

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 124.5s, verify 0.1s, in=295, out=16182)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₂ : a ∉ l2 := by sorry
have h₃ : eraseP (fun x => a == x) l2 = l2 := by
  intro h
  have h₄ : ∀ x ∈ l2, x ≠ a := by
    intro x hx
    have h₅ := h₂ x hx
    tauto
  have h₅ : eraseP (fun x => a == x) l2 = l2 := by
    apply List.eraseP_eq_iff_not_mem.mpr
    intro x hx
    have h₆ : x ∈ l2 := hx
    have h₇ : x ≠ a := h₄ x h₆
    simp_all [BEq.beq_eq]
  exact h₅
calc
  eraseP (fun x => a == x) (l1 ++ l2) = eraseP (fun x => a == x) l1 ++ eraseP (fun x => a == x) l2 := by rw [eraseP_append]
  _ = eraseP (fun x => a == x) l1 ++ l2 := by rw [h₃]
```

**lean_error:** tail step 1/17 ('have h₂ : a ∉ l2 := by sorry'): internal exception #7

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.3s, verify 0.1s, in=288, out=713)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l₁ generalizing a with
| nil => cases h
| cons x xs ih =>
  by_cases hax : a == x
  · simp [eraseP, hax]
  · simp [eraseP, hax, List.mem_cons] at h
    simp_all [eraseP, List.append_assoc]
```

**lean_error:** tail step 1/7 ('induction l₁ generalizing a with'): <stdin>:1:32: unexpected end of input; expected '|'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.4s, verify 0.1s, in=803, out=2274)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have pa : (fun x => a == x) a := by
    simpa [beq_self_eq_true]
  simpa using (List.eraseP_append_left (p:=fun x => a == x) (a:=a) pa (l₂:=l₂) h)
```

**lean_error:** tail step 1/3 ('have pa : (fun x => a == x) a := by'): <stdin>:1:35: unexpected end of input; expected '{'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 10.2s, verify 0.1s, in=754, out=1155)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
theorem List.erase_append_left {α : Type u_1} [BEq α] [LawfulBEq α] {a : α} {l₁ l₂ : List α} (h : a ∈ l₁) :
    eraseP (fun x => a == x) (l₁ ++ l₂) = eraseP (fun x => a == x) l₁ ++ l₂ := by
  have h₁ : (fun x => a == x) a = true := by
    simp [beq_self_eq_true]
    <;>
    rfl
  
  have h₂ : eraseP (fun x => a == x) (l₁ ++ l₂) = eraseP (fun x => a == x) l₁ ++ l₂ := by
    have h₃ : (fun x => a == x) a = true := h₁
    have h₄ : eraseP (fun x => a == x) (l₁ ++ l₂) = eraseP (fun x => a == x) l₁ ++ l₂ := by
      apply List.eraseP_append_left
      <;> simp_all [h₃]
      <;> aesop
    exact h₄
  
  exact h₂
```

**lean_error:** tail step 1/14 ('theorem List.erase_append_left {α : Type u_1} [BEq α] [LawfulBEq α] {a : α} {l₁ l₂ : List α} (h : a ∈ l₁) :'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.0s, verify 0.1s, in=735, out=548)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply eraseP_append_left (beq_self_eq_true a) l₂ h
```

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

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 124.6s, verify 0.1s, in=1650, out=16203)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h_erase_eq_eraseP : ∀ (l : List α), erase a l = eraseP (fun x => a == x) l := by
  intro l
  induction l with
  | nil => simp
  | cons y ys ih =>
    simp_all [List.erase_cons, List.eraseP_cons, beq_self_eq_true]
    <;>
    (try {
      have h₁ : a == y = true → a = y := by
        intro h
        exact LawfulBEq.eq_of_beq h
      have h₂ : a = y → a == y = true := by
        rw [h]
        exact beq_self_eq_true
      split_ifs at * <;> simp_all (config := {decide := true})
    }) <;>
    (try { aesop })
have h₁ : erase a (l₁ ++ l₂) = erase a l₁ ++ l₂ := List.erase_append_left h l₂
have h₂ : erase a (l₁ ++ l₂) = eraseP (fun x => a == x) (l₁ ++ l₂) := by
  apply h_erase_eq_eraseP
have h₃ : erase a l₁ = eraseP (fun x => a == x) l₁ := by
  apply h_erase_eq_eraseP
rw [h₂] at h₁
rw [h₃] at h₁
exact h₁
```

**lean_error:** tail step 1/25 ('have h_erase_eq_eraseP : ∀ (l : List α), erase a l = eraseP (fun x => a == x) l := by'): <stdin>:1:85: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.5s, verify 0.1s, in=1640, out=498)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply List.eraseP_append_left (beq_self_eq_true a)
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

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.9s, verify 0.1s, in=1621, out=1700)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have pa : (fun x => a == x) a := by
  simpa using (beq_self_eq_true a)
simpa using (eraseP_append_left (a:=a) (p:=fun x => a == x) pa (l₂:=l₂) h)
```

**lean_error:** tail step 1/3 ('have pa : (fun x => a == x) a := by'): <stdin>:1:35: unexpected end of input; expected '{'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 21.7s, verify 0.2s, in=1818, out=2481)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply List.eraseP_append_left
· simp [beq_self_eq_true]
· exact h
```

**lean_error:** tail step 2/3 ('· simp [beq_self_eq_true]'): unsolved goals

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.1s, verify 0.1s, in=1645, out=566)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply eraseP_append_left (beq_self_eq_true a) h
```

**lean_error:** tail step 1/1 ('apply eraseP_append_left (beq_self_eq_true a) h'): application type mismatch
