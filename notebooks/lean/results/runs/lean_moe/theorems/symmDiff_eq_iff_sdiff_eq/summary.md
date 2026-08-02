# symmDiff_eq_iff_sdiff_eq   (k=1, 2 tactics total)

file: `Mathlib/Order/SymmDiff.lean`  

**Ground-truth tail (from k):**
```lean
exact ((symmDiff_right_involutive a).toPerm _).apply_eq_iff_eq_symm_apply.trans eq_comm
```

**True premises at k:** `symmDiff_right_involutive`, `Function.Involutive.toPerm`, `eq_comm`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | · |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.9s, verify 0.2s, in=315, out=2929)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  simpa [h] using (symmDiff_self_left a b)
· intro h
  simpa [h] using (symmDiff_self_left a c)
```

**lean_error:** tail step 2/5 ('· intro h'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 131.4s, verify 0.2s, in=257, out=16629)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · intro h
    have h₁ : a ∆ c = b := by
      calc
        a ∆ c = a ∆ (a ∆ b) := by rw [h]
        _ = (a ∆ a) ∆ b := by rw [symmDiff_assoc]
        _ = 0 ∆ b := by rw [symmDiff_self]
        _ = b := by rw [symmDiff_zero_left]
    exact h₁
  · intro h
    have h₂ : a ∆ b = c := by
      calc
        a ∆ b = a ∆ (a ∆ c) := by rw [h]
        _ = (a ∆ a) ∆ c := by rw [symmDiff_assoc]
        _ = 0 ∆ c := by rw [symmDiff_self]
        _ = c := by rw [symmDiff_zero_left]
    exact h₂
```

**lean_error:** tail step 2/17 ('· intro h'): unsolved goals

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.6s, verify 0.2s, in=257, out=587)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro h
  rw [← h]
  simp [symmDiff_symmDiff_cancel_left]
· intro h
  rw [← h]
  simp [symmDiff_symmDiff_cancel_left]
```

**lean_error:** tail step 2/7 ('· intro h'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 13.8s, verify 0.2s, in=757, out=3389)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
constructor
· intro h
  have h' := congrArg (fun x => a ∆ x) h
  have : b = a ∆ c := by
    simpa [symmDiff_right_involutive a] using h'
  simpa [eq_comm] using this
· intro h
  have h' := congrArg (fun x => a ∆ x) h
  have : c = a ∆ b := by
    simpa [symmDiff_right_involutive a] using h'
  simpa [eq_comm] using this
```

**lean_error:** tail step 2/11 ('· intro h'): unsolved goals

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 72.4s, verify 0.1s, in=708, out=8723)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
theorem symmDiff_eq_iff_sdiff_eq (ι : Type u_1) (α : Type u_2) (β : Type u_3) (π : ι → Type u_4)
  (inst✝ : GeneralizedBooleanAlgebra α) (a b c d : α) (ha : a ≤ c) :
  a ∆ b = c ↔ a ∆ c = b := by
  have h_imp : a ∆ b = c → a ∆ c = b := by
    intro h
    have h₁ : a ∆ (a ∆ b) = b := symmDiff_right_involutive a b
    rw [h] at h₁
    exact h₁
  
  have h_conv : a ∆ c = b → a ∆ b = c := by
    intro h
    have h₁ : a ∆ (a ∆ c) = c := symmDiff_right_involutive a c
    rw [h] at h₁
    exact h₁
  
  have h_main : a ∆ b = c ↔ a ∆ c = b := by
    constructor
    · -- Prove the forward direction: if a ∆ b = c, then a ∆ c = b
      exact h_imp
    · -- Prove the backward direction: if a ∆ c = b, then a ∆ b = c
      exact h_conv
  
  exact h_main
```

**lean_error:** tail step 1/20 ('theorem symmDiff_eq_iff_sdiff_eq (ι : Type u_1) (α : Type u_2) (β : Type u_3) (π : ι → Type u_4)'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 7.0s, verify 0.1s, in=699, out=681)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [symmDiff_right_involutive, eq_comm]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
π : ι → Type u_4
inst✝ : GeneralizedBooleanAlgebra α
a b c d : α
...
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.1s, verify 0.8s, in=1140, out=2219)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
constructor
· intro h
  have h' := congrArg (fun x => a ∆ x) h
  simpa [symmDiff_symmDiff_cancel_left, eq_comm] using h'
· intro h
  have h' := congrArg (fun x => a ∆ x) h
  simpa [symmDiff_symmDiff_cancel_left, eq_comm] using h'
```

**lean_error:** tail step 2/7 ('· intro h'): unsolved goals

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 31.7s, verify 0.1s, in=1103, out=4024)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
theorem symmDiff_eq_iff_sdiff_eq {ι : Type u_1} {α : Type u_2} {β : Type u_3} {π : ι → Type u_4} {inst✝ : GeneralizedBooleanAlgebra α} {a b c d : α} (ha : a ≤ c) :
    a ∆ b = c ↔ a ∆ c = b := by
  rw [← symmDiff_of_le ha]
  have h_main : a ∆ b = c ↔ c \ a = b := by
    constructor
    · -- Prove the forward direction: a ∆ b = c → c \ a = b
      intro h
      have h1 : a ∆ c = b := by
        rw [h]
        rw [symmDiff_symmDiff_cancel_left]
      have h2 : a ∆ c = c \ a := symmDiff_of_le ha
      rw [h2] at h1
      exact h1
    · -- Prove the backward direction: c \ a = b → a ∆ b = c
      intro h
      have h1 : a ∆ c = c \ a := symmDiff_of_le ha
      have h2 : a ∆ c = b := by
        rw [h1]
        exact h
      have h3 : a ∆ b = c := by
        rw [h2]
        rw [symmDiff_symmDiff_cancel_left]
      exact h3
  exact h_main
```

**lean_error:** tail step 1/24 ('theorem symmDiff_eq_iff_sdiff_eq {ι : Type u_1} {α : Type u_2} {β : Type u_3} {π : ι → Type u_4} {inst✝ : GeneralizedBooleanAlgebra α} {a b c d : α} (ha : a ≤ c) :'): <stdin>:1:0: expected tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 297.7s, verify 0.0s, in=1084, out=32768)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
(empty)
```

**lean_error:** empty tail

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 17.8s, verify 0.1s, in=1114, out=4269)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [eq_comm] using (symmDiff_right_involutive a).eq_iff
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 106.7s, verify 0.2s, in=1172, out=13282)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h : a ∆ (a ∆ b) = b := by apply symmDiff_right_involutive
rw [h]
apply eq_comm
```

**lean_error:** tail step 2/3 ('rw [h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 11.4s, verify 0.1s, in=1094, out=1095)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← symmDiff_right_involutive a]
simp [eq_comm]
```

**lean_error:** tail step 1/2 ('rw [← symmDiff_right_involutive a]'): tactic 'rewrite' failed, pattern is a metavariable
