# CategoryTheory.isDetector_unop_iff   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Generator.lean`  

**Ground-truth tail (from k):**
```lean
rw [IsDetector, IsCodetector, ← isDetecting_unop_iff, Set.singleton_unop]
```

**True premises at k:** `CategoryTheory.IsDetector`, `CategoryTheory.IsCodetector`, `CategoryTheory.isDetecting_unop_iff`, `Set.singleton_unop`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.6s, verify 1.2s, in=310, out=719)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (isDetector_iff_isCodetector_op (G.unop))
```

**lean_error:** tail step 1/1 ('simpa using (isDetector_iff_isCodetector_op (G.unop))'): unknown identifier 'isDetector_iff_isCodetector_op'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 266.3s, verify 0.2s, in=254, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · intro h
    -- Assume IsDetector G.unop, prove IsCodetector G
    sorry
  · intro h
    -- Assume IsCodetector G, prove IsDetector G.unop
    sorry
```

**lean_error:** tail step 2/7 ('· intro h'): unsolved goals

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.7s, verify 0.1s, in=250, out=453)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.5s, verify 0.1s, in=957, out=499)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [IsDetector, IsCodetector, Set.singleton_unop] using
  (isDetecting_unop_iff ({G} : Set Cᵒᵖ))
```

**lean_error:** tail step 1/2 ('simpa [IsDetector, IsCodetector, Set.singleton_unop] using'): <stdin>:1:58: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 79.3s, verify 0.1s, in=923, out=9027)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
calc
  IsDetector G.unop ↔ IsDetecting ({G.unop} : Set C) := by rfl
  _ ↔ IsCodetecting ({G} : Set Cᵒᵖ) := by
    have h_unop : unop G = G.unop := rfl
    have h_set : ({G.unop} : Set C) = ((({G} : Set Cᵒᵖ).unop : Set C)) := by
      apply Set.ext
      intro y
      simp only [Set.mem_singleton_iff, Set.mem_unop, Set.mem_singleton_iff]
      <;> aesop
    rw [h_set]
    exact isDetecting_unop_iff ({G} : Set Cᵒᵖ)
  _ ↔ IsCodetector G := by rfl
```

**lean_error:** tail step 1/12 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.9s, verify 0.1s, in=891, out=744)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector, ← isDetecting_unop_iff, Set.singleton_unop]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.8s, verify 0.8s, in=1736, out=829)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [IsDetector, IsCodetector, Set.singleton_unop] using (isDetecting_unop_iff ({G} : Set Cᵒᵖ))
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 149.0s, verify 0.1s, in=1709, out=18075)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h_main : IsDetector G.unop ↔ IsCodetecting ({G} : Set Cᵒᵖ) := by
  constructor
  · intro h_det
    have h₁ : IsDetecting ({G.unop} : Set C) := by
      simpa [IsDetector] using h_det
    have h₂ : ({G.unop} : Set C) = ({G} : Set Cᵒᵖ).unop := by
      rw [singleton_unop]
      <;> simp
    rw [h₂] at h₁
    have h₃ : IsDetecting (({G} : Set Cᵒᵖ).unop) := h₁
    have h₄ : IsDetecting (({G} : Set Cᵒᵖ).unop) ↔ IsCodetecting ({G} : Set Cᵒᵖ) :=
      isDetecting_unop_iff ({G} : Set Cᵒᵖ)
    exact (h₄.mp h₃)
  · intro h_codet
    have h₁ : IsCodetecting ({G} : Set Cᵒᵖ) := h_codet
    have h₂ : IsDetecting (({G} : Set Cᵒᵖ).unop) :=
      (isDetecting_unop_iff ({G} : Set Cᵒᵖ)).mp h₁
    have h₃ : ({G} : Set Cᵒᵖ).unop = ({G.unop} : Set C) := by
      rw [singleton_unop]
      <;> simp
    rw [h₃] at h₂
    exact IsDetector.mono h₂
  
-- Now, we need to show that IsCodetecting ({G} : Set Cᵒᵖ) is the same as IsCodetector G.
-- Since G : Cᵒᵖ, by definition IsCodetector G is IsCodetecting ({G} : Set Cᵒᵖ) for the category Cᵒᵖ.
-- Therefore, we can directly use h_main to conclude the proof.
have h_final : IsDetector G.unop ↔ IsCodetector G := by
  constructor
  · intro h
    have h₁ : IsCodettor G := by
      -- Here we use the fact that for G : Cᵒᵖ, IsCodetector G is defined as IsCodetecting ({G} : Set Cᵒᵖ)
      -- This is by the definition of IsCodetector for the category of G.
      -- Since we don't have the definition in the context, we rely on the typing: G : Cᵒᵖ implies
      -- that IsCodetector G refers to the codetector property in the category Cᵒᵖ.
      -- In Lean, this is handled by the type class resolution, but for the purpose of this proof,
      -- we can simply note that the goal's IsCodetector G is exactly the right-hand side of h_main.
      have h₂ : IsCodettor ({G} : Set Cᵒᵖ) := by
        simpa [IsCodetector] using h
      -- But we need to connect this to IsCodetector G.
      -- Instead, we observe that the property is the same, so we can use h to get the right-hand side
      -- and then note that by definition, IsCodetector G is that property.
      -- Since we cannot unfold IsCodetector G without its definition, we use the following:
      --   The goal's IsCodetector G is meant to be interpreted as the codetector property in the
      --   category of G, which is Cᵒᵖ, and that is exactly IsCodetecting ({G} : Set Cᵒᵖ).
      --   Therefore, we can use h to get IsCodettor ({G} : Set Cᵒᵖ) and then claim that this is
      --   IsCodetector G.
      --   In the absence of a definition, we will assume that the proof checker understands this
      --   from the type of G.
      exact h
    exact h₁
  · intro h
    have h₁ : IsCodettor ({G} : Set Cᵒᵖ) := by
      -- Similarly, we assume that IsCodetector G for G : Cᵒᵖ is IsCodetecting ({G} : Set Cᵒᵖ)
      simpa [IsCodetector] using h
    have h₂ : IsDetector G.unop := by
      have h₃ : IsDetecting ({G.unop} : Set C) := by
        simpa [IsDetector] using h_main.mpr h₁
      exact h₃
    exact h₂
  
exact h_final
```

**lean_error:** tail step 1/59 ('have h_main : IsDetector G.unop ↔ IsCodetecting ({G} : Set Cᵒᵖ) := by'): <stdin>:1:69: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.8s, verify 0.2s, in=1632, out=465)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector]
rw [isDetecting_unop_iff]
simp [singleton_unop]
```

**lean_error:** tail step 2/3 ('rw [isDetecting_unop_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.6s, verify 0.8s, in=1642, out=1015)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
dsimp [IsDetector, IsCodetector]
  simpa [Set.singleton_unop] using (isDetecting_unop_iff ({G} : Set Cᵒᵖ))
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 136.6s, verify 0.1s, in=1814, out=16396)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
theorem CategoryTheory.isDetector_unop_iff {C : Type} [Category.C] {G : Cᵒᵖ} :
    IsDetector G.unop ↔ IsCodetector G := by
  have h_main : IsDetector G.unop ↔ IsCodetector G := by
    constructor
    · -- Forward direction: IsDetector G.unop → IsCodetector G
      intro h
      have h₁ : IsDetecting ({G.unop} : Set C) := by
        simpa [IsDetector] using h
      have h₂ : ({G.unop} : Set C) = ({G} : Set Cᵒᵖ).unop := by
        ext x
        simp [Set.mem_singleton_iff]
        <;>
        (try aesop) <;>
        (try {
          constructor <;>
          intro h₃ <;>
          (try { simp_all [Opposite.unop_iff] }) <;>
          (try { aesop })
        }) <;>
        (try {
          aesop
        })
      rw [h₂] at h₁
      have h₃ : IsCodetecting ({G} : Set Cᵒᵖ) := by
        have h₄ : IsDetecting (( {G} : Set Cᵒᵖ ).unop) ↔ IsCodetecting ({G} : Set Cᵒᵖ) :=
          isDetecting_unop_iff
        exact (h₄.mp h₁)
      -- We will use the fact that IsCodetector G is IsCodetecting ({G} : Set Cᵒᵖ)
      -- by redefining it for this proof (even though it contradicts the given definition).
      have h₄ : IsCodetector G := by
        simpa [IsCodetector] using h₃
      exact h₄
    · -- Backward direction: IsCodetector G → IsDetector G.unop
      intro h
      have h₁ : IsCodetecting ({G} : Set Cᵒᵖ) := by
        simpa [IsCodetector] using h
      have h₂ : IsDetecting (( {G} : Set Cᵒᵖ ).unop) := by
        have h₃ : IsDetecting (( {G} : Set Cᵒᵖ ).unop) ↔ IsCodetecting ({G} : Set Cᵒᵖ) :=
          isDetecting_unop_iff
        exact (h₃.mpr h₁)
      have h₃ : ({G} : Set Cᵒᵖ).unop = {G.unop} : Set C := by
        ext x
        simp [Set.mem_singleton_iff]
        <;>
        (try aesop) <;>
        (try {
          constructor <;>
          intro h₄ <;>
          (try { simp_all [Opposite.unop_iff] }) <;>
          (try { aesop })
        }) <;>
        (try {
          aesop
        })
      rw [h₃] at h₂
      have h₄ : IsDetecting ({G.unop} : Set C) := h₂
      have h₅ : IsDetector G.unop := by
        simpa [IsDetector] using h₄
      exact h₅
  exact h_main
```

**lean_error:** tail step 1/60 ('theorem CategoryTheory.isDetector_unop_iff {C : Type} [Category.C] {G : Cᵒᵖ} :'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 20.0s, verify 0.1s, in=1650, out=2175)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [IsDetector, IsCodetector, ← Set.singleton_unop, isDetecting_unop_iff]
```
