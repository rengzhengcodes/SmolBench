# Filter.tendsto_lift'   (k=0, 1 tactics total)

file: `Mathlib/Order/Filter/Lift.lean`  

**Ground-truth tail (from k):**
```lean
simp only [Filter.lift', tendsto_lift, tendsto_principal, comp]
```

**True premises at k:** `Filter.lift'`, `Filter.tendsto_lift`, `Filter.tendsto_principal`, `Function.comp`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.7s, verify 0.3s, in=374, out=1572)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· intro hm s hs
  have hmem := ((tendsto_def).1 hm) (h s) ?_
  · exact hmem
  · exact ⟨s, hs, subset_rfl⟩
· intro hcond
  refine ((tendsto_def).2 ?_)
  intro t ht
  rcases (mem_lift').1 ht with ⟨s, hs, hsub⟩
  have hmem := hcond s hs
  filter_upwards [hmem] with a ha
  exact hsub ha
```

**lean_error:** tail step 2/12 ('· intro hm s hs'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 248.9s, verify 0.1s, in=312, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : Tendsto m l (Filter.lift' f h) ↔ (∀ t ∈ f, ∀ᶠ a in l, m a ∈ h t) := by
  constructor
  · -- →
    intro h
    have h₂ : ∀ s ∈ Filter.lift' f h, ∀ᶠ a in l, m a ∈ s := by
      simpa [Filter.tendsto_iff] using h
    intro t ht
    have h₃ : h t ∈ Filter.lift' f h := by
      dsimp [Filter.lift'] at *
      refine' ⟨t, ht, _⟩
      <;> simp_all
    have h₄ : ∀ᶠ a in l, m a ∈ h t := h₂ h t h₃
    exact h₄
  · -- ←
    intro h
    have h₂ : ∀ s ∈ Filter.lift' f h, ∀ᶠ a in l, m a ∈ s := by
      intro s hs
      dsimp [Filter.lift'] at hs
      rcases hs with ⟨t, ht, hts⟩
      have h₃ : ∀ᶠ a in l, m a ∈ h t := h t ht
      have h₄ : ∀ᶠ a in l, m a ∈ s := by
        filter_upwards [h₃] with a hab
        exact hts hab
      exact h₄
    -- Now we need to show that Tendsto m l (Filter.lift' f h)
    -- which is ∀ s ∈ Filter.lift' f h, ∀ᶠ a in l, m a ∈ s
    exact h₂
exact h₁
```

**lean_error:** tail step 1/28 ("have h₁ : Tendsto m l (Filter.lift' f h) ↔ (∀ t ∈ f, ∀ᶠ a in l, m a ∈ h t) := by"): <stdin>:1:80: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.0s, verify 1.3s, in=305, out=486)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [tendsto_lift'_iff]
```

**lean_error:** tail step 1/1 ("simp [tendsto_lift'_iff]"): unknown identifier 'tendsto_lift'_iff'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.5s, verify 0.1s, in=1333, out=473)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Filter.lift', Function.comp] using
  (Filter.tendsto_lift (f:=f) (g:=fun s => (𝓟 (h s))) (m:=m) (l:=l))
```

**lean_error:** tail step 1/2 ("simpa [Filter.lift', Function.comp] using"): <stdin>:1:41: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 31.0s, verify 0.3s, in=1261, out=3679)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Filter.lift']
rw [Filter.tendsto_lift]
apply funext
intro s hs
have h₁ : (𝓟 ∘ h) s = 𝓟 (h s) := by simp [Function.comp_apply]
rw [h₁]
exact Filter.tendsto_principal
```

**lean_error:** tail step 3/7 ('apply funext'): tactic 'apply' failed, failed to unify

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.3s, verify 0.1s, in=1262, out=544)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Filter.lift', Function.comp, Filter.tendsto_lift, Filter.tendsto_principal]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.0s, verify 0.1s, in=4057, out=1143)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Filter.lift', Function.comp] using
    (Filter.tendsto_lift (f:=f) (g:=fun s => 𝓟 (h s)) (m:=m) (l:=l))
```

**lean_error:** tail step 1/2 ("simpa [Filter.lift', Function.comp] using"): <stdin>:1:41: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 32.0s, verify 0.1s, in=4015, out=3798)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.tendsto_lift]
constructor
· intro h
  intro s hs
  have h₁ : Tendsto m l ((𝓟 ∘ h) s) := h s hs
  have h₂ : Tendsto m l (𝓟 (h s)) := by simpa [Function.comp_apply] using h₁
  have h₃ : ∀ᶠ (a : γ) in l, m a ∈ h s := by
    rw [Filter.tendsto_principal] at h₂
    exact h₂
  exact h₃
· intro h
  intro s hs
  have h₁ : ∀ᶠ (a : γ) in l, m a ∈ h s := h s hs
  have h₂ : Tendsto m l (𝓟 (h s)) := by
    rw [Filter.tendsto_principal]
    exact h₁
  have h₃ : Tendsto m l ((𝓟 ∘ h) s) := by
    simpa [Function.comp_apply] using h₂
  exact h₃
```

**lean_error:** tail step 1/19 ('rw [Filter.tendsto_lift]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 11.1s, verify 0.3s, in=4027, out=1256)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.lift']
rw [Filter.tendsto_lift]
simp [Function.comp, Filter.tendsto_principal]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.6s, verify 0.1s, in=3768, out=1539)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Filter.lift', Function.comp] using
  (Filter.tendsto_lift (f:=f) (g:=𝓟 ∘ h) (m:=m) (l:=l))
```

**lean_error:** tail step 1/2 ("simpa [Filter.lift', Function.comp] using"): <stdin>:1:41: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 61.0s, verify 0.3s, in=4446, out=7873)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.lift']
rw [Filter.tendsto_lift]
apply forall_congr
intro s hs
simp [Function.comp_apply]
rw [Filter.tendsto_principal]
```

**lean_error:** tail step 3/6 ('apply forall_congr'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.4s, verify 0.3s, in=3973, out=603)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.lift']
rw [Filter.tendsto_lift]
simp [Function.comp, Filter.tendsto_principal]
```
