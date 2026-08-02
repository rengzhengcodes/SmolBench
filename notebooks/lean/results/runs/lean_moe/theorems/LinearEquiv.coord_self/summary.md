# LinearEquiv.coord_self   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/Span.lean`  

**Ground-truth tail (from k):**
```lean
rw [← toSpanNonzeroSingleton_one R M x h, LinearEquiv.symm_apply_apply]
```

**True premises at k:** `LinearEquiv.toSpanNonzeroSingleton_one`, `LinearEquiv.symm_apply_apply`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | · |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.4s, verify 0.1s, in=376, out=1213)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using coord_self (R:=R) (M:=M) (x:=x) (h:=h)
```

**lean_error:** tail step 1/1 ('simpa using coord_self (R:=R) (M:=M) (x:=x) (h:=h)'): invalid argument name 'R' for function

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 133.2s, verify 0.1s, in=326, out=16791)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.5s, verify 0.2s, in=321, out=510)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [coord]
```

**final state (truncated):**
```
R : Type u_1
R₂ : Type u_2
K : Type u_3
M : Type u_4
M₂ : Type u_5
V : Type u_6
...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.2s, verify 0.2s, in=735, out=1117)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
dsimp [LinearEquiv.coord]
  simpa [LinearEquiv.toSpanNonzeroSingleton_one] using
    (LinearEquiv.symm_apply_apply (LinearEquiv.toSpanNonzeroSingleton (R:=R) (M:=M) (x:=x) (h:=h)) (1))
```

**lean_error:** tail step 2/3 ('simpa [LinearEquiv.toSpanNonzeroSingleton_one] using'): <stdin>:1:52: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 136.9s, verify 0.1s, in=706, out=17448)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h1 : (LinearEquiv.toSpanNonzeroSingleton R M x h) 1 = ({ val := x, property := ⋯ } : R ∙ x) := by
  apply Subtype.ext
  · -- Show the underlying values are equal
    have h2 : (LinearEquiv.toSpanNonzeroSingleton R M x h) 1 = (1 : R) • x := by
      simp [LinearEquiv.toSpanNonzeroSingleton_apply]
      <;>
      (try aesop)
    rw [h2]
    <;> simp [one_smul]
    <;>
    (try aesop)
  · -- Show the properties are equal (by proof irrelevance)
    have h3 : ((LinearEquiv.toSpanNonzeroSingleton R M x h) 1 : M) ∈ Submodule.span R ({x} : Set M) := by
      simp [LinearEquiv.toSpanNonzeroSingleton_apply, Submodule.mem_span_singleton] at *
      <;> aesop
    have h4 : (( { val := x, property := ⋯ } : R ∙ x) : M) ∈ Submodule.span R ({x} : Set M) := by
      simp [Submodule.mem_span_singleton] at *
      <;> aesop
    -- Now, we use the fact that the type of proofs is a subsingleton.
    exact ProofIrrelevance.proof_irrelevant _ _
  
have h2 : (LinearEquiv.toSpanNonzeroSingleton R M x h).symm ((LinearEquiv.toSpanNonzeroSingleton R M x h) 1) = (1 : R) := by
  apply LinearEquiv.symm_apply_apply
  
have h3 : (LinearEquiv.toSpanNonzeroSingleton R M x h).symm ({ val := x, property := ⋯ } : R ∙ x) = (1 : R) := by
  rw [h1] at h2
  exact h2
  
rw [coord]
<;> exact h3
```

**lean_error:** tail step 1/27 ('have h1 : (LinearEquiv.toSpanNonzeroSingleton R M x h) 1 = ({ val := x, property := ⋯ } : R ∙ x) := by'): <stdin>:1:102: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 6.0s, verify 0.3s, in=679, out=560)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← LinearEquiv.toSpanNonzeroSingleton_one]
simp
```

**final state (truncated):**
```
case h
R : Type u_1
R₂ : Type u_2
K : Type u_3
M : Type u_4
M₂ : Type u_5
...
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.2s, verify 0.1s, in=1007, out=993)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [LinearEquiv.coord, LinearEquiv.toSpanNonzeroSingleton_one] using
  (LinearEquiv.symm_apply_apply (LinearEquiv.toSpanNonzeroSingleton (R:=R) (M:=M) (x:=x) (h:=h)) (1 : R))
```

**lean_error:** tail step 1/2 ('simpa [LinearEquiv.coord, LinearEquiv.toSpanNonzeroSingleton_one] using'): <stdin>:1:71: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 73.0s, verify 0.1s, in=980, out=9522)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ : (toSpanNonzeroSingleton R M x h) 1 = { val := x, property := ⋯ } := by
  rw [LinearEquiv.toSpanNonzeroSingleton_one]
  apply Subtype.ext
  · rfl
  · apply proof_irrel

calc
  (coord R M x h) { val := x, property := ⋯ } = (toSpanNonzeroSingleton R M x h).symm { val := x, property := ⋯ } := by rfl
  _ = (toSpanNonzeroSingleton R M x h).symm ( (toSpanNonzeroSingleton R M x h) 1 ) := by rw [h₁]
  _ = 1 := by apply LinearEquiv.symm_apply_apply
```

**lean_error:** tail step 1/9 ('have h₁ : (toSpanNonzeroSingleton R M x h) 1 = { val := x, property := ⋯ } := by'): <stdin>:1:80: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.8s, verify 0.1s, in=948, out=541)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← LinearEquiv.toSpanNonzeroSingleton_one, LinearEquiv.symm_apply_apply]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.2s, verify 0.9s, in=995, out=918)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [LinearEquiv.coord, LinearEquiv.toSpanNonzeroSingleton_one] using
  (LinearEquiv.symm_apply_apply (LinearEquiv.toSpanNonzeroSingleton R M x h) 1)
```

**lean_error:** tail step 1/2 ('simpa [LinearEquiv.coord, LinearEquiv.toSpanNonzeroSingleton_one] using'): <stdin>:1:71: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 53.0s, verify 0.3s, in=1041, out=6794)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
unfold coord
apply LinearEquiv.symm_apply_apply
```

**lean_error:** tail step 2/2 ('apply LinearEquiv.symm_apply_apply'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 8.4s, verify 0.1s, in=965, out=774)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← LinearEquiv.toSpanNonzeroSingleton_one, LinearEquiv.symm_apply_apply]
```
