# LinearMap.ker_prodMap   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Prod.lean`  

**Ground-truth tail (from k):**
```lean
rw [← prodMap_comap_prod, Submodule.prod_bot]
```

**True premises at k:** `LinearMap.prodMap_comap_prod`, `Submodule.prod_bot`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✓ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 19.0s, verify 0.9s, in=581, out=3104)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
  rcases x with ⟨x₁, x₂⟩
  constructor
  · intro hx
    change (prodMap f g) (x₁, x₂) ∈ (⊥ : Submodule R (M₂ × M₄)) at hx
    have h0 : (prodMap f g) (x₁, x₂) = 0 := by
      simpa [Submodule.mem_bot] using hx
    have hfst : f x₁ = 0 := by
      have := congrArg Prod.fst h0
      simpa using this
    have hsnd : g x₂ = 0 := by
      have := congrArg Prod.snd h0
      simpa using this
    exact ⟨by
            change f x₁ ∈ (⊥ : Submodule R M₂)
            simpa [Submodule.mem_bot] using hfst,
          by
            change g x₂ ∈ (⊥ : Submodule R M₄)
            simpa [Submodule.mem_bot] using hsnd⟩
  · rintro ⟨hx1, hx2⟩
    change (prodMap f g) (x₁, x₂) ∈ (⊥ : Submodule R (M₂ × M₄))
    have hfst : f x₁ = 0 := by
      simpa [Submodule.mem_bot] using hx1
    have hsnd : g x₂ = 0 := by
      simpa [Submodule.mem_bot] using hx2
    have : (prodMap f g) (x₁, x₂) = (0, 0) := by
      ext <;> simp [LinearMap.prodMap, hfst, hsnd]
    simpa [Submodule.mem_bot] using this
```

**lean_error:** tail step 4/28 ('· intro hx'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 43.9s, verify 0.1s, in=550, out=5236)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
theorem submodule_comap_prodMap_bottom {R : Type u} {K : Type u'} {M : Type v} {V : Type v'} {M₂ : Type w} {V₂ : Type w'} {M₃ : Type y} {V₃ : Type y'} {M₄ : Type z} {ι : Type x} {M₅ : Type u_1} {M₆ : Type u_2} {S : Type u_3} [Semiring R] [Semiring S] [AddCommMonoid M] [AddCommMonoid M₂] [AddCommMonoid M₃] [AddCommMonoid M₄] [AddCommMonoid M₅] [AddCommMonoid M₆] [Module R M] [Module R M₂] [Module R M₃] [Module R M₄] [Module R M₅] [Module R M₆] (f✝ f : M →ₗ[R] M₂) (g : M₃ →ₗ[R] M₄) :
    Submodule.comap (prodMap f g) ⊥ = Submodule.prod (Submodule.comap f ⊥) (Submodule.comap g ⊥) := by
  have h_main : Submodule.comap (prodMap f g) ⊥ = Submodule.prod (Submodule.comap f ⊥) (Submodule.comap g ⊥) := by
    apply Submodule.ext
    intro ⟨x, y⟩
    simp [Submodule.mem_comap_iff, Submodule.mem_prod, Prod.mem_bottom, prodMap_apply, Submodule.mem_bottom]
    <;>
    aesop
  
  exact h_main
```

**lean_error:** tail step 1/9 ("theorem submodule_comap_prodMap_bottom {R : Type u} {K : Type u'} {M : Type v} {V : Type v'} {M₂ : Type w} {V₂ : Type w'} {M₃ : Type y} {V₃ : Type y'} {M₄ : Type z} {ι : Type x} {M₅ : Type u_1} {M₆ : Type u_2} {S : Type u_3} [Semiring R] [Semiring S] [AddCommMonoid M] [AddCommMonoid 

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.8s, verify 0.3s, in=526, out=589)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext ⟨m, n⟩
simp [Submodule.mem_comap, Submodule.mem_prod, LinearMap.prodMap]
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.9s, verify 0.1s, in=1042, out=884)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Submodule.prod_bot] using
  (LinearMap.prodMap_comap_prod f g (⊥ : Submodule R M₂) (⊥ : Submodule R M₄))
```

**lean_error:** tail step 1/2 ('simpa [Submodule.prod_bot] using'): <stdin>:1:32: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 85.0s, verify 0.1s, in=1038, out=10373)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h₁ : (Submodule.prod ⊥ ⊥ : Submodule R (M₂ × M₄)) = ⊥ := by
  apply Submodule.prod_bot
have h₂ : (Submodule.prod ⊥ ⊥).comap (prodMap f g) = (⊥.comap f).prod (⊥.comap g) :=
  LinearMap.prodMap_comap_prod f g ⊥ ⊥
have h₃ : comap (prodMap f g) ⊥ = (comap f ⊥).prod (comap g ⊥) := by
  calc
    comap (prodMap f g) ⊥ = (⊥ : Submodule R (M₂ × M₄)).comap (prodMap f g) := by rfl
    _ = (⊥.comap f).prod (⊥.comap g) := by
      rw [h₁] at h₂
      exact h₂
    _ = (comap f ⊥).prod (comap g ⊥) := by
      have h₄ : ⊥.comap f = comap f ⊥ := by rfl
      have h₅ : ⊥.comap g = comap g ⊥ := by rfl
      rw [h₄, h₅]
exact h₃
```

**lean_error:** tail step 1/15 ('have h₁ : (Submodule.prod ⊥ ⊥ : Submodule R (M₂ × M₄)) = ⊥ := by'): <stdin>:1:64: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.1s, verify 0.1s, in=988, out=421)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Submodule.prod_bot, LinearMap.prodMap_comap_prod]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.0s, verify 0.1s, in=1604, out=936)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Submodule.prod_bot] using
  (LinearMap.prodMap_comap_prod f g (⊥ : Submodule R M₂) (⊥ : Submodule R M₄))
```

**lean_error:** tail step 1/2 ('simpa [Submodule.prod_bot] using'): <stdin>:1:32: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 33.4s, verify 0.1s, in=1613, out=3926)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h : (⊥ : Submodule R (M₂ × M₄)) = Submodule.prod ⊥ ⊥ := by
  rw [← Submodule.prod_bot]
rw [h]
rw [LinearMap.prodMap_comap_prod f g]
```

**lean_error:** tail step 1/4 ('have h : (⊥ : Submodule R (M₂ × M₄)) = Submodule.prod ⊥ ⊥ := by'): <stdin>:1:63: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.6s, verify 0.1s, in=1541, out=569)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← Submodule.prod_bot, LinearMap.prodMap_comap_prod]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.0s, verify 0.1s, in=1552, out=926)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Submodule.prod_bot] using
  (LinearMap.prodMap_comap_prod (f:=f) (g:=g)
    (S:=(⊥ : Submodule R M₂)) (S':=(⊥ : Submodule R M₄)))
```

**lean_error:** tail step 1/3 ('simpa [Submodule.prod_bot] using'): <stdin>:1:32: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 32.7s, verify 0.1s, in=1698, out=3843)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : (Submodule.prod ⊥ ⊥).comap (prodMap f g) = (⊥.comap f).prod (⊥.comap g) := LinearMap.prodMap_comap_prod f g ⊥ ⊥
have h₂ : Submodule.comap (prodMap f g) ⊥ = (Submodule.prod ⊥ ⊥).comap (prodMap f g) := by
  rw [← Submodule.prod_bot]
  <;> rfl
calc
  Submodule.comap (prodMap f g) ⊥ = (Submodule.prod ⊥ ⊥).comap (prodMap f g) := h₂
  _ = (⊥.comap f).prod (⊥.comap g) := h₁
```

**lean_error:** tail step 1/7 ('have h₁ : (Submodule.prod ⊥ ⊥).comap (prodMap f g) = (⊥.comap f).prod (⊥.comap g) := LinearMap.prodMap_comap_prod f g ⊥ ⊥'): type mismatch

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 12.8s, verify 0.1s, in=1551, out=862)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Submodule.prod_bot, LinearMap.prodMap_comap_prod f g ⊥ ⊥]
```
