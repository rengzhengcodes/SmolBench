# card_le_of_surjective'   (k=2, 3 tactics total)

file: `Mathlib/LinearAlgebra/InvariantBasisNumber.lean`  

**Ground-truth tail (from k):**
```lean
exact
  card_le_of_surjective R ((P.toLinearMap.comp f).comp Q.toLinearMap)
    ((P.surjective.comp i).comp Q.surjective)
```

**True premises at k:** `card_le_of_surjective`, `LinearMap.comp`, `Function.Surjective.comp`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 26.7s, verify 0.1s, in=408, out=4249)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : (Cardinal.mk β) ≤ Cardinal.mk α := by
    simpa [Finsupp.rank_eq_card] using
      (LinearMap.lift_rank_le_of_surjective (f:=f) i)
  exact_mod_cast h
```

**lean_error:** tail step 1/4 ('have h : (Cardinal.mk β) ≤ Cardinal.mk α := by'): <stdin>:1:46: unexpected end of input; expected '{'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 48.6s, verify 0.1s, in=363, out=5048)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have hM : FiniteDimensional R (α →₀ R) := Fintype.finiteDimensional_finsupp
have hN : FiniteDimensional R (β →₀ R) := Fintype.finiteDimensional_finsupp
have h : finiteDimensional.finrank R (α →₀ R) ≥ finiteDimensional.finrank R (β →₀ R) :=
  LinearMap.finiteDimensional_le_of_surjective i hM hN
rw [Fintype.finrank_finsupp] at h
rw [Fintype.finrank_finsupp] at h
linarith
```

**lean_error:** tail step 1/7 ('have hM : FiniteDimensional R (α →₀ R) := Fintype.finiteDimensional_finsupp'): unknown identifier 'FiniteDimensional'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.5s, verify 0.1s, in=350, out=723)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : Module.rank R (β →₀ R) ≤ Module.rank R (α →₀ R) :=
    Module.rank_le_of_surjective f i
have h₁ : Module.rank R (β →₀ R) = Fintype.card β := by
  rw [Module.rank_fun_on_finite]
have h₂ : Module.rank R (α →₀ R) = Fintype.card α := by
  rw [Module.rank_fun_on_finite]
rw [h₁, h₂] at h
exact h
```

**lean_error:** tail step 1/8 ('have h : Module.rank R (β →₀ R) ≤ Module.rank R (α →₀ R) :='): <stdin>:1:59: unexpected end of input

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 14.0s, verify 0.1s, in=1202, out=1156)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact
  (card_le_of_surjective (R:=R)
    ((Q.symm.toLinearMap.comp f).comp P.toLinearMap)
    (((LinearEquiv.symm Q).surjective.comp i).comp (LinearEquiv.surjective P)))
```

**lean_error:** tail step 1/4 ('exact'): <stdin>:1:5: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 57.1s, verify 0.5s, in=1186, out=5955)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have hP : Function.Surjective P := P.surjective
have hf : Function.Surjective f := i
have hQ : Function.Surjective Q := Q.surjective
have hfQ : Function.Surjective (f.comp Q) := Function.Surjective.comp hf hQ
have hg : Function.Surjective (P.comp f.comp Q) := Function.Surjective.comp hP hfQ
have h_card : Fintype.card β ≤ Fintype.card α := card_le_of_surjective (P.comp f.comp Q) hg
exact h_card
```

**lean_error:** tail step 4/7 ('have hfQ : Function.Surjective (f.comp Q) := Function.Surjective.comp hf hQ'): application type mismatch

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.1s, verify 0.1s, in=1161, out=572)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact
  card_le_of_surjective R
    (P.toLinearMap.comp (f.comp Q.toLinearMap))
    (P.surjective.comp (i.comp Q.surjective))
```

**lean_error:** tail step 1/4 ('exact'): <stdin>:1:5: unexpected end of input

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 42.6s, verify 0.1s, in=3685, out=8383)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
refine
  card_le_of_surjective (R:=R) (α:=α) (β:=β)
    ((P.symm.toLinearMap.comp f).comp Q.symm.toLinearMap) ?_
exact
  ((LinearEquiv.symm P).surjective.comp i).comp (LinearEquiv.symm Q).surjective
```

**lean_error:** tail step 1/5 ('refine'): <stdin>:1:6: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 59.7s, verify 0.1s, in=3733, out=6233)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have hg_surj : Surjective ⇑(P.toLinearMap.comp f.comp Q.toLinearMap) := by
  have h1 : Surjective (⇑f ∘ ⇑(Q.toLinearMap)) := by
    apply Surjective.comp
    · exact i
    · exact Q.surjective
  exact Surjective.comp P.surjective h1

have h_card : Fintype.card β ≤ Fintype.card α := by
  apply card_le_of_surjective
  <;> infer_instance
  <;> 
    (try
      {
        exact (P.toLinearMap.comp f.comp Q.toLinearMap)
      })
  <;> 
    (try
      {
        exact hg_surj
      })

exact h_card
```

**lean_error:** tail step 1/20 ('have hg_surj : Surjective ⇑(P.toLinearMap.comp f.comp Q.toLinearMap) := by'): <stdin>:1:74: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.9s, verify 0.1s, in=3640, out=749)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact card_le_of_surjective R (P.toLinearMap.comp (f.comp Q.toLinearMap))
  (P.surjective.comp (i.comp Q.surjective))
```

**lean_error:** tail step 1/2 ('exact card_le_of_surjective R (P.toLinearMap.comp (f.comp Q.toLinearMap))'): type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 17.2s, verify 0.1s, in=3394, out=1881)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have hsurj :
    Surjective ((P.toLinearMap.comp f).comp Q.toLinearMap) := by
    exact ((LinearEquiv.surjective P).comp i).comp (LinearEquiv.surjective Q)
  exact
    (card_le_of_surjective (R:=R) ((P.toLinearMap.comp f).comp Q.toLinearMap) hsurj)
```

**lean_error:** tail step 1/5 ('have hsurj :'): <stdin>:1:12: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 57.9s, verify 0.1s, in=4052, out=6048)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine' card_le_of_surjective _ _
· exact P.toLinearMap.comp (f.comp Q.toLinearMap)
· exact P.surjective.comp (f.surjective.comp Q.surjective)
```

**lean_error:** tail step 1/3 ("refine' card_le_of_surjective _ _"): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.0s, verify 0.1s, in=3601, out=668)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact
  card_le_of_surjective R
    (P.toLinearMap.comp f.comp Q.toLinearMap)
    ((P.surjective.comp i).comp Q.surjective)
```

**lean_error:** tail step 1/4 ('exact'): <stdin>:1:5: unexpected end of input
