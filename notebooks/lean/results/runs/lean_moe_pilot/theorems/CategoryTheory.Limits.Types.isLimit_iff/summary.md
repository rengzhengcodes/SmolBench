# CategoryTheory.Limits.Types.isLimit_iff   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Limits/Types.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨x, fun c j ↦ funext fun y ↦ (hx c y).1 j,
  fun c f hf ↦ funext fun y ↦ (hx c y).2 (f y) (fun j ↦ congr_fun (hf j) y)⟩
```

**True premises at k:** `funext`, `funext`, `congr_fun`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base |
| --- | --- | --- |
| `stepk:1` | ✘ | X |
| `hint:2` | ✘ | ✘ |
| `hint:3` | ✘ | ✘ |
| `noise:3` | ✘ | X |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 23.4s, verify 0.1s, in=444, out=2674)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine
    { lift := fun s => fun y => x s y,
      fac' := by
        intro s j
        funext y
        exact (hx s y).1 j,
      uniq' := by
        intro s m w
        funext y
        have hprop : ∀ j, c.π.app j (m y) = (sectionOfCone s y : _) j := by
          intro j
          have := congrArg (fun f => f y) (w j)
          simpa using this
        exact (hx s y).2 (m y) hprop }
```

**lean_error:** tail step 1/14 ('refine'): <stdin>:1:6: unexpected end of input

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **exception**  (gen 260.5s, verify 300.1s, in=394, out=28442)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' IsLimit.mk _
intro c₁
use fun y => x c₁ y
constructor
· -- Prove it's a cone homomorphism
  intro j
  funext y
  have h₁ : (fun x => ∀ (j : J), c.π.app j x = ↑(sectionOfCone c₁ y) j) (x c₁ y) := (hx c₁ y).1
  have h₂ : ↑(sectionOfCone c₁ y) j = c₁.π.app j y := by
    -- By definition of sectionOfCone, (sectionOfCone c₁ y) j = c₁.π.app j y
    rfl
  have h₃ : c.π.app j (x c₁ y) = ↑(sectionOfCone c₁ y) j := by
    simpa using h₁
  have h₄ : c.π.app j (x c₁ y) = c₁.π.app j y := by
    rw [h₂] at h₃
    exact h₃
  simpa [Function.comp_apply] using h₄
· -- Prove uniqueness
  intro g hg
  have h₁ : g = fun y => x c₁ y := by
    funext y
    have h₂ : ∀ (j : J), c.π.app j (g y) = c₁.π.app j y := by
      have h₃ : ∀ (j : J), c.π.app j ∘ g = c₁.π.app j := hg
      have h₄ : (c.π.app j ∘ g) y = c₁.π.app j y := h₃ j
      simpa [Function.comp_apply] using h₄
    have h₃ : ∀ (j : J), c.π.app j (g y) = ↑(sectionOfCone c₁ y) j := by
      intro j
      have h₄ : c.π.app j (g y) = c₁.π.app j y := h₂ j
      have h₅ : ↑(sectionOfCone c₁ y) j = c₁.π.app j y := by
        -- By definition of sectionOfCone, (sectionOfCone c₁ y) j = c₁.π.app j y
        rfl
      linarith
    have h₄ : (fun x => ∀ (j : J), c.π.app j x = ↑(sectionOfCone c₁ y) j) (g y) := by
      intro j
      exact h₃ j
    have h₅ : (fun x => ∀ (j : J), c.π.app j x = ↑(sectionOfCone c₁ y) j) (x c₁ y) := (hx c₁ y).1
    have h₆ : g y = x c₁ y := by
      apply (hx c₁ y).2 y
      exact h₄
    exact h₆
  exact h₁
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 29.5s, verify 0.1s, in=1667, out=4076)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine
  { lift := fun s => fun y => x s y,
    fac := fun s j => funext (fun y => (hx s y).1 j),
    uniq := fun s m hm =>
      funext (fun y => (hx s y).2 (by
        intro j
        have := congr_fun (hm j) y
        exact this)) }
```

**lean_error:** tail step 1/8 ('refine'): <stdin>:1:6: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 181.9s, verify 0.1s, in=1637, out=19561)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine ⟨fun t => x t, _, _⟩
· -- Prove the fac' condition: t.π j y = c.π j (x t y)
  intro t y j
  have h₁ : (∀ (j : J), c.π.app j (x t y) = ↑(sectionOfCone t y) j) := (hx t y).1
  have h₂ : ∀ (j : J), ↑(sectionOfCone t y) j = t.π j y := by
    intro j
    simp [sectionOfCone]
    <;>
    aesop
  have h₃ : ∀ (j : J), c.π.app j (x t y) = t.π j y := by
    intro j
    have h₄ := h₁ j
    have h₅ := h₂ j
    linarith
  have h₄ : t.π j y = c.π.app j (x t y) := by
    linarith
  exact h₄
· -- Prove the uniq' condition: uniqueness of the morphism making triangles commute
  intro t f g hf hg
  have h₁ : f = g := by
    funext y
    have h₂ : f y = g y := by
      have h₃ : ∀ (j : J), c.π.app j (f y) = t.π j y := by
        intro j
        have h₄ := hf j y
        linarith
      have h₄ : ∀ (j : J), c.π.app j (g y) = t.π j y := by
        intro j
        have h₅ := hg j y
        linarith
      have h₅ : f y = x t y := by
        have h₆ : (∀ (j : J), c.π.app j (x t y) = t.π j y) := by
          have h₇ : (∀ (j : J), c.π.app j (x t y) = ↑(sectionOfCone t y) j) := (hx t y).1
          have h₈ : ∀ (j : J), ↑(sectionOfCone t y) j = t.π j y := by
            intro j
            simp [sectionOfCone]
            <;>
            aesop
          have h₉ : ∀ (j : J), c.π.app j (x t y) = t.π j y := by
            intro j
            have h₁₀ := h₇ j
            have h₁₁ := h₈ j
            linarith
          exact h₉
        have h₇ : (∀ (j : J), c.π.app j (f y) = t.π j y) := h₃
        have h₈ : ∀ (j : J), c.π.app j (f y) = c.π.app j (x t y) := by
          intro j
          have h₉ := h₇ j
          have h₁₀ := h₆ j
          linarith
        have h₉ : f y = x t y := by
          apply funext
          <;> simp_all [Pi.apply_def]
          <;> aesop
        exact h₉
      have h₆ : g y = x t y := by
        have h₇ : (∀ (j : J), c.π.app j (x t y) = t.π j y) := by
          have h₈ : (∀ (j : J), c.π.app j (x t y) = ↑(sectionOfCone t y) j) := (hx t y).1
          have h₉ : ∀ (j : J), ↑(sectionOfCone t y) j = t.π j y := by
            intro j
            simp [sectionOfCone]
            <;>
            aesop
          have h₁₀ : ∀ (j : J), c.π.app j (x t y) = t.π j y := by
            intro j
            have h₁₁ := h₈ j
            have h₁₂ := h₉ j
            linarith
          exact h₁₀
        have h₈ : (∀ (j : J), c.π.app j (g y) = t.π j y) := h₄
        have h₉ : ∀ (j : J), c.π.app j (g y) = c.π.app j (x t y) := by
          intro j
          have h₁₀ := h₈ j
          have h₁₁ := h₇ j
          linarith
        have h₁₀ : g y = x t y := by
          apply funext
          <;> simp_all [Pi.apply_def]
          <;> aesop
        exact h₁₀
      linarith
    exact h₂
  exact h₁
```

**lean_error:** tail step 1/83 ('refine ⟨fun t => x t, _, _⟩'): internal exception #7

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 32.4s, verify 0.7s, in=5340, out=4807)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
refine
  { lift := fun s y => x s y,
    fac := fun s j => funext (fun y => (hx s y).1 j),
    uniq := fun s m hm => 
      funext (fun y => 
        (hx s y).2 (by
          intro j
          have := congr_fun (hm j) y
          simpa using this)) }
```

**lean_error:** tail step 1/9 ('refine'): <stdin>:1:6: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 83.3s, verify 0.2s, in=5378, out=7768)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [CategoryTheory.Limits.Types.isLimit_iff]
exact h
```

**lean_error:** tail step 1/2 ('rw [CategoryTheory.Limits.Types.isLimit_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 46.3s, verify 0.5s, in=4965, out=6943)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine ⟨?_, ?_, ?_⟩
· intro s
  exact x s
· intro s j
  funext y
  exact (hx s y).1 j
· intro s m hm
  funext y
  apply (hx s y).2 (m y)
  intro j
  exact congr_fun (hm j) y
```

**lean_error:** tail step 2/11 ('· intro s'): unsolved goals

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **exception**  (gen 560.5s, verify 300.1s, in=5953, out=29668)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h : IsLimit c := ⟨fun t => x t, by
  intro t j
  apply funext
  intro y
  have h₁ : c.π.app j (x t y) = (sectionOfCone t y) j := (hx t y).1 j
  have h₂ : (sectionOfCone t y) j = t.π.app j y := rfl
  rw [h₁, h₂]
, by
  intro t x y hx hy
  apply funext
  intro y
  have h₁ : ∀ (j : J), c.π.app j (x y) = t.π.app j y := hx y
  have h₂ : ∀ (j : J), c.π.app j (y y) = t.π.app j y := hy y
  have h₃ : x y = x t y := by
    apply (hx t y).2
    intro j
    exact h₁ j
  have h₄ : y y = x t y := by
    apply (hx t y).2
    intro j
    exact h₂ j
  have h₅ : x y = y y := by
    rw [h₃] at *
    rw [h₄]
  exact h₅⟩
exact h
```

**lean_error:** DojoTacticTimeoutError: 
