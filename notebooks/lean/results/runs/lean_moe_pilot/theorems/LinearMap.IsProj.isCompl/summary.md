# LinearMap.IsProj.isCompl   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Projection.lean`  

**Ground-truth tail (from k):**
```lean
exact isCompl_of_proj h.codRestrict_apply_cod
```

**True premises at k:** `LinearMap.isCompl_of_proj`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.0s, verify 0.1s, in=1161, out=1440)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [LinearMap.ker_codRestrict] using h.isCompl_ker
exact h
exact p
```

**lean_error:** tail step 1/3 ('simpa [LinearMap.ker_codRestrict] using h.isCompl_ker'): invalid field 'isCompl_ker', the environment does not contain 'LinearMap.IsProj.isCompl_ker'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 79.1s, verify 0.1s, in=1194, out=10367)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨p, _, p, _, p⟩ <;>
  (try
    {
      have h₁ : f '' E ⊆ p := by
        have h₂ : f.range = p := h.2
        have h₃ : f '' E = f.range := by simp [Image.range]
        rw [h₃] at h₂
        exact h₂
      have h₂ : ker (f.codRestrict p h₁) = ker f := by
        apply Submodule.ext
        intro x
        constructor
        · intro hx
          have h₃ : (f.codRestrict p h₁) x = 0 := hx
          have h₄ : (f.codRestrict p h₁) x = f x := by
            rw [LinearMap.codRestrict_apply]
          rw [h₄] at h₃
          exact h₃
        · intro hx
          have h₃ : f x = 0 := hx
          have h₄ : (f.codRestrict p h₁) x = f x := by
            rw [LinearMap.codRestrict_apply]
          rw [h₄] at h₃
          exact h₃
      have h₃ : IsCompl (ker f) (f.range) := LinearMap.isCompl_ker_of_idempotent h.1
      have h₄ : IsCompl (ker f) p := by
        rw [h.2] at h₃
        exact h₃
      have h₅ : IsCompl p (ker f) := by
        rw [IsCompl.symm] at h₄
        exact h₄
      have h₆ : IsCompl p (ker (f.codRestrict p h₁)) := by
        rw [h₂]
        exact h₅
      exact h₆
    }) <;>
  (try
    {
      exact h
    }) <;>
  (try
    {
      exact p
    })
```

**lean_error:** tail step 1/44 ("refine' ⟨p, _, p, _, p⟩ <;>"): <stdin>:1:27: unexpected end of input; expected '['

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 9.8s, verify 0.1s, in=1130, out=685)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.ker_compl
```

**lean_error:** tail step 1/1 ('exact h.ker_compl'): invalid field 'ker_compl', the environment does not contain 'LinearMap.IsProj.ker_compl'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 14.6s, verify 0.3s, in=1521, out=3700)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rcases h with ⟨h_mem, h_id⟩
  have hf : ∀ x, f x ∈ p := h_mem
  simpa [codRestrict_ker] using
    (LinearMap.isCompl_of_proj (f := LinearMap.codRestrict f hf) (by
      intro x
      cases x with
      | mk x hx =>
        ext
        simpa using h_id x hx))
```

**lean_error:** tail step 3/9 ('simpa [codRestrict_ker] using'): <stdin>:1:29: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 108.9s, verify 0.1s, in=1574, out=15131)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
change IsCompl p (ker (codRestrict f p)) at ⊢
rw [codRestrict_ker]
have h_map_into_p : ∀ x : E, f x ∈ p := by
  intro x
  have h₁ : p = range f := h.2
  rw [h₁]
  exact ⟨x, rfl⟩
have h_preimage_top : f ⁻¹' p = ⊤ := by
  apply eq_top
  intro x
  have h₂ : f x ∈ p := h_map_into_p x
  exact h₂
rw [h_preimage_top]
have h_is_compl : IsCompl p (ker f) := by
  have h₁ : ∀ x : E, f x ∈ p := h_map_into_p
  let g : E →ₗ[R] p := LinearMap.codRestrict f h₁
  have h₂ : ∀ x : p, g x = x := by
    intro x
    have h₃ : g x = f x := by
      simp [LinearMap.codRestrict]
    rw [h₃]
    have h₄ : f (x : E) = (x : E) := by
      have h₅ : p = range f := h.2
      have h₆ : (x : E) ∈ p := by exact_mod_cast x
      rw [h₅] at h₆
      obtain ⟨y, hy⟩ := h₆
      have h₇ : f y = (x : E) := by simpa using hy
      have h₈ : f (f y) = f y := by
        apply h.1
      have h₉ : f (x : E) = (x : E) := by
        calc
          f (x : E) = f (f y) := by rw [h₇]
          _ = f y := by rw [h₈]
          _ = (x : E) := by rw [h₇]
      exact h₉
    have h₁₀ : (f (x : E) : p) = (x : p) := by
      norm_cast at h₄ ⊢
      <;> simp_all [Submodule.ext_iff]
      <;> aesop
    exact h₁₀
  have h₃ : IsCompl p (ker g) := LinearMap.isCompl_of_proj g h₂
  have h₄ : ker g = ker f := by
    apply Submodule.ext
    intro x
    constructor
    · -- g x = 0 => f x = 0
      intro hx
      have h₅ : g x = 0 := hx
      have h₆ : (g x : E) = 0 := by
        simpa [Submodule.coe_zero] using h₅
      have h₇ : (g x : E) = f x := by
        simp [LinearMap.codRestrict, h₁]
      rw [h₇] at h₆
      exact h₆
    · -- f x = 0 => g x = 0
      intro hx
      have h₅ : f x = 0 := hx
      have h₆ : g x = f x := by
        simp [LinearMap.codRestrict, h₁]
      rw [h₆]
      exact h₅
  rw [h₄] at h₃
  exact h₃
exact h_is_compl
refine' ⟨p, _⟩
exact h
exact ⊥
```

**lean_error:** tail step 1/67 ('change IsCompl p (ker (codRestrict f p)) at ⊢'): <stdin>:1:44: expected '*' or term

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 100.9s, verify 0.1s, in=1488, out=13138)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rotate 2
exact p
rotate
assumption
refine isCompl_of_proj (codRestrict f p (LinearMap.range_le_iff.mpr h.map_mem)) ?_
intro x
exact h.idempotent x x.property
```

**lean_error:** tail step 1/7 ('rotate 2'): <stdin>:1:1: unknown tactic

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.1s, verify 0.5s, in=2191, out=2779)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rcases h with ⟨hmem, hproj⟩
refine LinearMap.isCompl_of_proj ?_
intro x
cases x with
| mk x hx =>
  ext
  simpa [LinearMap.codRestrict_apply] using hproj x hx
```

**lean_error:** tail step 4/7 ('cases x with'): <stdin>:1:12: unexpected end of input; expected '|'

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 91.4s, verify 0.2s, in=2246, out=12164)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsProj.isCompl
<;> exact h
exact h
exact p
```

**lean_error:** tail step 1/4 ('apply IsProj.isCompl'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 37.0s, verify 0.5s, in=2136, out=3976)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
intro x
exact h.2 x
```

**lean_error:** tail step 3/3 ('exact h.2 x'): type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=2113, out=503)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using h.isCompl
```

**lean_error:** tail step 1/1 ('simpa using h.isCompl'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 104.6s, verify 0.1s, in=2342, out=14361)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
<;> exact p <;> exact h
<;> exact p
<;> try
  {
    refine' ⟨p, _⟩
    have h₁ : ∀ x : E, f x ∈ p := by
      have h₂ : p = map f ⊤ := h.2
      intro x
      rw [h₂]
      exact mem_map _ x
    have h₂' : ∀ x : p, f x = x := by
      intro x
      have h₃ : x ∈ p := x
      have h₄ : p = map f ⊤ := h.2
      rw [h₄] at h₃
      obtain ⟨y, hy⟩ := h₃
      have h₅ : f x = f (f y) := by rw [hy]
      have h₆ : f (f y) = f y := by
        have h₇ : f ∘ f = f := h.1
        have h₈ : (f ∘ f) y = f y := by rw [h₇]
        exact h₈
      rw [h₅, h₆]
      <;> simp [hy]
    have h₂ : ∀ x : p, (codRestrict p f) x = x := by
      intro x
      have h₃ : (codRestrict p f) x = f x := by
        apply LinearMap.codRestrict_apply
      rw [h₃]
      exact h₂' x
    have h₃ : IsCompl p (ker (codRestrict p f)) := by
      apply LinearMap.isCompl_of_proj
      exact h₂
    exact h₃
  }
```

**lean_error:** tail step 1/34 ('<;> exact p <;> exact h'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 9.0s, verify 0.3s, in=2143, out=593)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply isCompl_of_proj
intro x hx
exact h.1 x hx
```

**lean_error:** tail step 2/3 ('intro x hx'): tactic 'introN' failed, insufficient number of binders
