# LinearMap.range_eq_top_of_cancel   (k=2, 3 tactics total)

file: `Mathlib/LinearAlgebra/Quotient.lean`  

**Ground-truth tail (from k):**
```lean
exact ker_zero
```

**True premises at k:** `LinearMap.ker_zero`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✓ |
| `hint:2` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.8s, in=538, out=614)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
  constructor
  · intro hx
    trivial
  · intro _
    change (0 : M₂ →ₗ[R₂] M₂ ⧸ range f) x = 0
    simp
```

**lean_error:** tail step 3/7 ('· intro hx'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 204.4s, verify 0.1s, in=497, out=26252)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₂ : ker 0 = ⊤ := by
  classical
  have h₃ : ∀ (x : M₂), (0 : M₂ → ?m) x = 0 := by
    intro x
    simp
  have h₄ : ker 0 = ⊤ := by
    apply le_antisymm
    · exact le_top
    · intro x hx
      have h₅ : (0 : M₂ → ?m) x = 0 := h₃ x
      exact h₅
  exact h₄
```

**lean_error:** tail step 1/12 ('have h₂ : ker 0 = ⊤ := by'): <stdin>:1:25: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 4.1s, verify 0.3s, in=473, out=431)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
simp
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 1.4s, verify 0.5s, in=812, out=295)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using LinearMap.ker_zero
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 39.2s, verify 0.1s, in=777, out=4459)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply LinearMap.ker_zero
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 1.8s, verify 0.1s, in=745, out=165)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [LinearMap.ker_zero]
```
