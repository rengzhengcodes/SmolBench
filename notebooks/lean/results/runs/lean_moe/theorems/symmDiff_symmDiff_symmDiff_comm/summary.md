# symmDiff_symmDiff_symmDiff_comm   (k=0, 1 tactics total)

file: `Mathlib/Order/SymmDiff.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [symmDiff_assoc, symmDiff_left_comm]
```

**True premises at k:** `symmDiff_assoc`, `symmDiff_left_comm`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | · |
| `hint:3` | ✓ | ✘ | · |
| `noise:3` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 28.6s, verify 0.1s, in=329, out=5950)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
calc
  a ∆ b ∆ (c ∆ d)
      = a ∆ b ∆ c ∆ d := by
        simpa using (symmDiff_assoc (a ∆ b) c d).symm
  _ = a ∆ c ∆ b ∆ d := by
        calc
          a ∆ b ∆ c ∆ d
              = a ∆ (b ∆ c) ∆ d := by
                simpa [symmDiff_assoc] using (symmDiff_assoc a b c).symm
          _ = a ∆ (c ∆ b) ∆ d := by
                simpa [symmDiff_comm]
          _ = a ∆ c ∆ b ∆ d := by
                simpa [symmDiff_assoc]
  _ = a ∆ c ∆ (b ∆ d) := by
        simpa using (symmDiff_assoc (a ∆ c) b d)
```

**lean_error:** tail step 1/15 ('calc'): <stdin>:1:4: unexpected end of input

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 85.9s, verify 0.1s, in=273, out=10305)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [symm_diff_assoc] at *
have h : b ∆ (c ∆ d) = c ∆ (b ∆ d) := by
  calc
    b ∆ (c ∆ d) = (b ∆ c) ∆ d := by rw [← symm_diff_assoc]
    _ = (c ∆ b) ∆ d := by rw [symm_diff_comm]
    _ = c ∆ (b ∆ d) := by rw [symm_diff_assoc]
rw [h] at *
<;> rfl

</think>
rw [symm_diff_assoc] at *
have h : b ∆ (c ∆ d) = c ∆ (b ∆ d) := by
  calc
    b ∆ (c ∆ d) = (b ∆ c) ∆ d := by rw [← symm_diff_assoc]
    _ = (c ∆ b) ∆ d := by rw [symm_diff_comm]
    _ = c ∆ (b ∆ d) := by rw [symm_diff_assoc]
rw [h] at *
<;> rfl
```

**lean_error:** tail step 1/17 ('rw [symm_diff_assoc] at *'): tactic 'rewrite' failed, did not find instance of the pattern in the current goal

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.2s, verify 0.1s, in=275, out=489)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
abel
```

**lean_error:** tail step 1/1 ('abel'): <stdin>:1:1: unknown tactic

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 14.9s, verify 0.1s, in=650, out=3184)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
calc
  a ∆ b ∆ (c ∆ d) = a ∆ (b ∆ (c ∆ d)) := by
    simpa [symmDiff_assoc]
  _ = a ∆ (c ∆ (b ∆ d)) := by
    apply congrArg (fun x => a ∆ x)
    calc
      b ∆ (c ∆ d) = (b ∆ c) ∆ d := by
        simpa [symmDiff_assoc] using (symmDiff_assoc (a:=b) (b:=c) (c:=d))
      _ = (c ∆ b) ∆ d := by
        simpa [symmDiff_comm]
      _ = c ∆ (b ∆ d) := by
        simpa [symmDiff_assoc] using (symmDiff_assoc (a:=c) (b:=b) (c:=d))
  _ = a ∆ c ∆ (b ∆ d) := by
    simpa [symmDiff_assoc]
```

**lean_error:** tail step 1/14 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 43.1s, verify 0.4s, in=600, out=5267)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_assoc]
rw [symmDiff_left_comm]
rw [← symmDiff_assoc]
rw [symmDiff_left_comm]
<;> rfl
```

**lean_error:** tail step 5/5 ('<;> rfl'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.4s, verify 0.1s, in=601, out=513)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_assoc, symmDiff_left_comm, ← symmDiff_assoc]
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

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 12.1s, verify 0.2s, in=1266, out=2573)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [symmDiff_assoc]
simp [symmDiff_left_comm]
rfl
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 112.5s, verify 0.6s, in=1224, out=13985)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_assoc]
rw [symmDiff_comm]
rw [symmDiff_assoc]
rw [symmDiff_assoc]
rw [symmDiff_comm]
rw [symmDiff_assoc]
<;> rfl
</code></pre>
```

**lean_error:** tail step 7/8 ('<;> rfl'): <stdin>:1:0: expected tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 6.8s, verify 0.1s, in=1171, out=674)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [symmDiff_assoc, symmDiff_left_comm, ← symmDiff_assoc]
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

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 12.8s, verify 0.1s, in=1179, out=2737)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
calc
  a ∆ b ∆ (c ∆ d) = a ∆ (b ∆ (c ∆ d)) := by
    simpa [symmDiff_assoc]
  _ = a ∆ (c ∆ (b ∆ d)) := by
    simpa using congrArg (fun x => a ∆ x) (symmDiff_left_comm (a:=b) (b:=c) (c:=d))
  _ = a ∆ c ∆ (b ∆ d) := by
    simpa [symmDiff_assoc]
```

**lean_error:** tail step 1/7 ('calc'): <stdin>:1:4: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 150.8s, verify 0.1s, in=1290, out=20057)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h1 : a ∆ b ∆ (c ∆ d) = a ∆ b ∆ c ∆ d := by
  have h1₁ : (a ∆ b) ∆ c ∆ d = (a ∆ b) ∆ (c ∆ d) := by rw [symmDiff_assoc]
  have h1₂ : a ∆ b ∆ (c ∆ d) = (a ∆ b) ∆ (c ∆ d) := rfl
  have h1₃ : a ∆ b ∆ c ∆ d = (a ∆ b) ∆ c ∆ d := rfl
  calc
    a ∆ b ∆ (c ∆ d) = (a ∆ b) ∆ (c ∆ d) := h1₂
    _ = (a ∆ b) ∆ c ∆ d := by rw [h1₁]
    _ = a ∆ b ∆ c ∆ d := h1₃

have h5 : a ∆ c ∆ (b ∆ d) = a ∆ c ∆ b ∆ d := by
  have h5₁ : (a ∆ c) ∆ b ∆ d = (a ∆ c) ∆ (b ∆ d) := by rw [symmDiff_assoc]
  have h5₂ : a ∆ c ∆ (b ∆ d) = (a ∆ c) ∆ (b ∆ d) := rfl
  have h5₃ : a ∆ c ∆ b ∆ d = (a ∆ c) ∆ b ∆ d := rfl
  calc
    a ∆ c ∆ (b ∆ d) = (a ∆ c) ∆ (b ∆ d) := h5₂
    _ = (a ∆ c) ∆ b ∆ d := by rw [h5₁]
    _ = a ∆ c ∆ b ∆ d := h5₃

have h2 : b ∆ c ∆ d = c ∆ b ∆ d := by
  calc
    b ∆ c ∆ d = b ∆ (c ∆ d) := rfl
    _ = c ∆ (b ∆ d) := by rw [symmDiff_left_comm]
    _ = (c ∆ b) ∆ d := by
      rw [← symmDiff_assoc]
      <;> rfl
    _ = c ∆ b ∆ d := rfl

have h3 : a ∆ b ∆ c ∆ d = a ∆ (b ∆ c ∆ d) := by
  calc
    a ∆ b ∆ c ∆ d = ((a ∆ b) ∆ c) ∆ d := rfl
    _ = (a ∆ (b ∆ c)) ∆ d := by
      rw [← symmDiff_assoc]
      <;> rfl
    _ = a ∆ ((b ∆ c) ∆ d) := by
      rw [symmDiff_assoc]
      <;> rfl
    _ = a ∆ (b ∆ c ∆ d) := rfl

have h4 : a ∆ (c ∆ b ∆ d) = a ∆ c ∆ b ∆ d := by
  calc
    a ∆ (c ∆ b ∆ d) = a ∆ ((c ∆ b) ∆ d) := rfl
    _ = (a ∆ (c ∆ b)) ∆ d := by
      rw [← symmDiff_assoc]
      <;> rfl
    _ = ((a ∆ c) ∆ b) ∆ d := by
      have h4₁ : a ∆ (c ∆ b) = (a ∆ c) ∆ b := by
        rw [← symmDiff_assoc]
        <;> rfl
      rw [h4₁]
      <;> rfl
    _ = a ∆ c ∆ b ∆ d := rfl

have h_main : a ∆ b ∆ c ∆ d = a ∆ c ∆ b ∆ d := by
  calc
    a ∆ b ∆ c ∆ d = a ∆ (b ∆ c ∆ d) := h3
    _ = a ∆ (c ∆ b ∆ d) := by rw [h2]
    _ = a ∆ c ∆ b ∆ d := h4

have h_final : a ∆ b ∆ (c ∆ d) = a ∆ c ∆ (b ∆ d) := by
  calc
    a ∆ b ∆ (c ∆ d) = a ∆ b ∆ c ∆ d := h1
    _ = a ∆ c ∆ b ∆ d := h_main
    _ = a ∆ c ∆ (b ∆ d) := by rw [h5.symm]

exact h_final
```

**lean_error:** tail step 1/58 ('have h1 : a ∆ b ∆ (c ∆ d) = a ∆ b ∆ c ∆ d := by'): <stdin>:1:47: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 4.7s, verify 0.3s, in=1188, out=432)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_assoc]
rw [symmDiff_left_comm]
rw [← symmDiff_assoc]
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
