# RatFunc.algebraMap_injective   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
exact ofFractionRing_injective.comp (IsFractionRing.injective _ _)
```

**True premises at k:** `IsFractionRing.injective`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.7s, verify 0.2s, in=300, out=1081)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intro p q h
simpa [Function.comp] using h
```

**lean_error:** tail step 2/2 ('simpa [Function.comp] using h'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 65.5s, verify 0.2s, in=250, out=7437)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have hKX : IsDomain (K[X]) := by infer_instance
have hFracKX : IsDomain (FractionRing (K[X])) := by infer_instance
have h : (algebraMap K[X] (FractionRing K[X]) : K[X] → FractionRing K[X]) = (ofFractionRing : K[X] → FractionRing K[X]) := by
  apply algebraMap_ofFractionRing
rw [h]
have h1 : Function.Injective (ofFractionRing : K[X] → FractionRing K[X]) := by
  apply injective_ofFractionRing
have h2 : Function.Injective (ofFractionRing : FractionRing K[X] → FractionRing (FractionRing K[X])) := by
  apply injective_ofFractionRing
exact Function.Injective.comp h2 h1
```

**lean_error:** tail step 3/10 ('have h : (algebraMap K[X] (FractionRing K[X]) : K[X] → FractionRing K[X]) = (ofFractionRing : K[X] → FractionRing K[X]) := by'): <stdin>:1:125: unexpected end of input; expected '{'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.8s, verify 0.7s, in=247, out=754)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Function.Injective.comp
· exact ofFractionRing_injective
· exact algebraMap_injective
```

**lean_error:** tail step 3/3 ('· exact algebraMap_injective'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.2s, verify 0.1s, in=476, out=967)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective'): type mismatch

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 58.6s, verify 0.1s, in=427, out=6641)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
theorem RatFunc.algebraMap_injective {K : Type u} [CommRing K] [IsDomain K] :
    Function.Injective (ofFractionRing ∘ ⇑(algebraMap K[X] (FractionRing K[X]))) := by
  have h₁ : Function.Injective (⇑(algebraMap K[X] (FractionRing K[X]))) := by
    apply IsFractionRing.injective
    <;>
    (try infer_instance) <;>
    (try
      {
        refine' ⟨K[X], _⟩
        <;> simp [FractionRing]
      })
  
  have h₂ : Function.Injective (ofFractionRing ∘ ⇑(algebraMap K[X] (FractionRing K[X]))) := by
    rw [← h₁]
    <;>
    simp [Function.Injective]
    <;>
    aesop
  
  exact h₂
```

**lean_error:** tail step 1/18 ('theorem RatFunc.algebraMap_injective {K : Type u} [CommRing K] [IsDomain K] :'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.1s, verify 0.1s, in=431, out=481)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('apply IsFractionRing.injective'): tactic 'apply' failed, failed to unify

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.3s, verify 0.5s, in=854, out=720)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective'): type mismatch

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 63.4s, verify 0.1s, in=809, out=7200)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('apply IsFractionRing.injective'): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.5s, verify 0.1s, in=806, out=446)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('apply IsFractionRing.injective'): tactic 'apply' failed, failed to unify

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.0s, verify 0.3s, in=829, out=1091)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('simpa using IsFractionRing.injective'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 35.2s, verify 0.1s, in=886, out=3977)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
theorem RatFunc.algebraMap_injective {K : Type u} [CommRing K] [IsDomain K] :
    Function.Injective (ofFractionRing ∘ ⇑(algebraMap K[X] (FractionRing K[X]))) := by
  rw [← ofFractionRing_comp_algebraMap]
  have hKX : IsDomain (K[X]) := by
    apply IsDomain.polynomial
    exact inst✝
  
  have h_main : Function.Injective (⇑(algebraMap K[X] (FractionRing K[X]))) := by
    apply IsFractionRing.injective
  
  exact h_main
```

**lean_error:** tail step 1/9 ('theorem RatFunc.algebraMap_injective {K : Type u} [CommRing K] [IsDomain K] :'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.3s, verify 0.1s, in=822, out=377)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsFractionRing.injective
```

**lean_error:** tail step 1/1 ('exact IsFractionRing.injective'): type mismatch
