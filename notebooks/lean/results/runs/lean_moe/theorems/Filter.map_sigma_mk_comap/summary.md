# Filter.map_sigma_mk_comap   (k=2, 3 tactics total)

file: `Mathlib/Order/Filter/Bases.lean`  

**Ground-truth tail (from k):**
```lean
apply image_sigmaMk_preimage_sigmaMap hf
```

**True premises at k:** `Set.image_sigmaMk_preimage_sigmaMap`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✓ | ✘ |
| `noise:3` | ✘ | · | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 15.2s, verify 0.8s, in=424, out=3020)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext s
  rcases s with ⟨a', b⟩
  constructor
  · rintro ⟨c, hc, rfl⟩
    exact ⟨g a c, hc, rfl⟩
  · rintro h
    rcases h with ⟨y, hy, h_eq⟩
    have hfa : f a' = f a := congrArg Sigma.fst h_eq
    have ha : a' = a := hf hfa
    subst ha
    have hgb : g a b = y := by
      have := congrArg Sigma.snd h_eq
      simpa using this
    have hb : g a b ∈ x✝ := by
      simpa [hgb] using hy
    exact ⟨b, hb, rfl⟩
```

**lean_error:** tail step 4/16 ('· rintro ⟨c, hc, rfl⟩'): tactic 'subst' failed, invalid equality proof, it is not of the form (x = t) or (t = x)

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 92.3s, verify 0.6s, in=378, out=10299)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Set.ext
intro ⟨a', p'⟩
constructor
· intro h
  rcases h with ⟨p, h₁, h₂⟩
  rw [h₁]
  simp [Sigma.map_apply]
  refine' ⟨g a p, _⟩
  constructor
  · rfl
  · exact h₂
· intro h
  have h₁ : Sigma.map f g ⟨a', p'⟩ ∈ Sigma.mk (f a) '' id x✝ := h
  rcases h₁ with ⟨q, h₂, h₃⟩
  have h₄ : Sigma.map f g ⟨a', p'⟩ = ⟨f a', g a' p'⟩ := rfl
  rw [h₄] at h₂
  have h₅ : f a' = f a := by
    simp_all [Prod.mk.injEq]
    <;> aesop
  have h₆ : a' = a := hf h₅
  refine' ⟨p', _⟩
  constructor
  · -- prove a' = a
    simp_all [h₆]
    <;> aesop
  · -- prove p' ∈ g a ⁻¹' id x✝
    have h₇ : g a' p' = q := by
      simp_all [Prod.mk.injEq]
      <;> aesop
    have h₈ : g a p' = q := by
      rw [h₆] at h₇
      exact h₇
    have h₉ : q ∈ x✝ := h₃
    have h₁₀ : g a p' ∈ x✝ := by
      rw [h₈] at h₉
      exact h₉
    have h₁₁ : p' ∈ g a ⁻¹' id x✝ := by
      simp only [Set.mem_preimage]
      exact h₁₀
    exact h₁₁
```

**lean_error:** tail step 4/40 ('· intro h'): unsolved goals

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.7s, verify 0.2s, in=374, out=609)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext ⟨b, y⟩
simp only [Set.mem_image, Set.mem_preimage, Sigma.mk.inj_iff, Sigma.map_eq, and_imp, exists_and_right,
  exists_eq_right]
constructor
· rintro ⟨y', hy', h⟩
  simp_all
  aesop
· rintro ⟨hfa, hy⟩
  have : b = a := hf hfa
  subst this
  exact ⟨y, hy, rfl⟩
```

**lean_error:** tail step 2/11 ('simp only [Set.mem_image, Set.mem_preimage, Sigma.mk.inj_iff, Sigma.map_eq, and_imp, exists_and_right,'): <stdin>:1:102: unexpected end of input; expected ']'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.6s, verify 0.1s, in=916, out=730)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using Set.image_sigmaMk_preimage_sigmaMap hf g a (id x✝)
```

**lean_error:** tail step 1/1 ('simpa using Set.image_sigmaMk_preimage_sigmaMap hf g a (id x✝)'): <stdin>:1:60: expected token

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 121.3s, verify 0.1s, in=879, out=14027)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [show (g a ⁻¹' (id : Set (π' (f a)) → Set (π' (f a))) x✝) = g a ⁻¹' x✝ by simp [id]]
rw [show (Sigma.mk (f a) '' (id : Set (π' (f a)) → Set (π' (f a))) x✝) = Sigma.mk (f a) '' x✝ by simp [id]]
apply Set.image_sigmaMk_preimage_sigmaMap
```

**lean_error:** tail step 1/3 ("rw [show (g a ⁻¹' (id : Set (π' (f a)) → Set (π' (f a))) x✝) = g a ⁻¹' x✝ by simp [id]]"): <stdin>:1:58: expected token

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.5s, verify 0.1s, in=850, out=489)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Set.image_sigmaMk_preimage_sigmaMap hf g a (id x✝)]
```

**lean_error:** tail step 1/1 ('rw [Set.image_sigmaMk_preimage_sigmaMap hf g a (id x✝)]'): <stdin>:1:52: expected token

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.1s, in=1725, out=888)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using Set.image_sigmaMk_preimage_sigmaMap hf g a x✝
```

**lean_error:** tail step 1/1 ('simpa using Set.image_sigmaMk_preimage_sigmaMap hf g a x✝'): <stdin>:1:56: expected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 78.4s, verify 0.1s, in=1688, out=8725)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Set.image_sigmaMk_preimage_sigmaMap hf g
```

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.1s, in=1610, out=463)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Set.image_sigmaMk_preimage_sigmaMap hf g a (id x✝)
```

**lean_error:** tail step 1/1 ('exact Set.image_sigmaMk_preimage_sigmaMap hf g a (id x✝)'): <stdin>:1:54: expected token

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.9s, verify 0.1s, in=1611, out=1020)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using (Set.image_sigmaMk_preimage_sigmaMap hf g a x✝)
```

**lean_error:** tail step 1/1 ('simpa using (Set.image_sigmaMk_preimage_sigmaMap hf g a x✝)'): <stdin>:1:57: expected token

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **incomplete**  (gen 41.7s, verify 0.1s, in=1785, out=4496)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Set.image_sigmaMk_preimage_sigmaMap
```

**final state (truncated):**
```
case h.e'_5.h.hf
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
ι' : Sort u_5
...
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.4s, verify 0.1s, in=1622, out=479)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact Set.image_sigmaMk_preimage_sigmaMap hf g a (id x✝)
```

**lean_error:** tail step 1/1 ('exact Set.image_sigmaMk_preimage_sigmaMap hf g a (id x✝)'): <stdin>:1:54: expected token
