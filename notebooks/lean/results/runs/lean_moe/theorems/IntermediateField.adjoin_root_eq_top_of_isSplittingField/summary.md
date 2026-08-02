# IntermediateField.adjoin_root_eq_top_of_isSplittingField   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/KummerExtension.lean`  

**Ground-truth tail (from k):**
```lean
exact (Algebra.adjoin_root_eq_top_of_isSplittingField hζ H hα).symm
```

**True premises at k:** `Algebra.adjoin_root_eq_top_of_isSplittingField`, `Eq.symm`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | · | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 11.2s, verify 0.1s, in=379, out=2351)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (IsSplittingField.adjoin_root_eq_top (K:=K) (L:=L) (a:=a) (α:=α) hζ)
```

**lean_error:** tail step 1/1 ('simpa using (IsSplittingField.adjoin_root_eq_top (K:=K) (L:=L) (a:=a) (α:=α) hζ)'): unknown constant 'Polynomial.IsSplittingField.adjoin_root_eq_top'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **incomplete**  (gen 244.0s, verify 0.1s, in=329, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
obtain ⟨ζ, hζ⟩ := hζ
```

**final state (truncated):**
```
case intro
K : Type u
inst✝³ : Field K
n : ℕ
hn : 0 < n
a : K
...
```

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 14.2s, verify 0.5s, in=325, out=1433)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Subalgebra.ext
intro x
constructor
· intro hx
  have h_adjoin : Algebra.adjoin K ({α} : Set L) = ⊤ := by
    apply IsSplittingField.adjoin_eq_top
    intro y hy
    rw [mem_roots] at hy
    have hζ_exists : ∃ ζ : K, IsPrimitiveRoot ζ n := by
      obtain ⟨ζ, hζ⟩ := hζ
      exact ⟨ζ, hζ⟩
    obtain ⟨ζ, hζ⟩ := hζ_exists
    have hζ_in_K : (algebraMap K L) ζ ∈ Algebra.adjoin K ({α} : Set L) := by
      apply Algebra.subset_adjoin
      simp
    have hα_in_adjoin : α ∈ Algebra.adjoin K ({α} : Set L) := by
      apply Algebra.subset_adjoin
      simp
    have hy_pow : y ^ n = algebraMap K L a := by
      rw [hy]
      simp
    have hα_pow : α ^ n = algebraMap K L a := hα
    have h_y_α : y ^ n = α ^ n := by rw [hy_pow, hα_pow]
    -- y is a root of X^n - a, so y = α * ζ^k for some k
    -- Since ζ ∈ K and α ∈ Algebra.adjoin K {α}, we have y ∈ Algebra.adjoin K {α}
    have hζ_pow : IsPrimitiveRoot (algebraMap K L ζ) n := by
      apply IsPrimitiveRoot.algebraMap
      exact hζ
    -- Use that all roots are of the form α * ζ^k
    have h_y_in_adjoin : y ∈ Algebra.adjoin K ({α} : Set L) := by
      -- y^n = α^n implies y = α * ζ^k for some k < n
      have h_exists_k : ∃ (k : ℕ), k < n ∧ y = α * (algebraMap K L ζ) ^ k := by
        -- This follows from the theory of roots of unity
        sorry
      obtain ⟨k, hk, hk_eq⟩ := h_exists_k
      rw [hk_eq]
      apply Algebra.mul_mem
      · exact hα_in_adjoin
      · apply Algebra.pow_mem
        exact hζ_in_K
    exact h_y_in_adjoin
  rw [h_adjoin]
  exact hx
· intro hx
  exact Subalgebra.mem_top x
```

**lean_error:** tail step 4/45 ('· intro hx'): unsolved goals

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.8s, verify 0.2s, in=1071, out=1525)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using (Algebra.adjoin_root_eq_top_of_isSplittingField (K:=K) (α:=α)).symm
```

**lean_error:** tail step 1/1 ('simpa using (Algebra.adjoin_root_eq_top_of_isSplittingField (K:=K) (α:=α)).symm'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 117.8s, verify 0.2s, in=1046, out=15404)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h : Algebra.adjoin K {α} = (⊤ : Subalgebra K L) := Algebra.adjoin_root_eq_top_of_isSplittingField
have h₂ : (⊤ : IntermediateField K L).toSubalgebra = (⊤ : Subalgebra K L) := by
  apply Subalgebra.ext
  intro x
  simp only [Subalgebra.mem_carrier, IntermediateField.mem_carrier]
  <;> aesop
calc
  (⊤ : IntermediateField K L).toSubalgebra = (⊤ : Subalgebra K L) := h₂
  _ = Algebra.adjoin K {α} := by rw [h]
```

**lean_error:** tail step 1/9 ('have h : Algebra.adjoin K {α} = (⊤ : Subalgebra K L) := Algebra.adjoin_root_eq_top_of_isSplittingField'): type mismatch

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.6s, verify 0.1s, in=1022, out=715)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Algebra.adjoin_root_eq_top_of_isSplittingField
```

**lean_error:** tail step 1/1 ('apply Algebra.adjoin_root_eq_top_of_isSplittingField'): tactic 'apply' failed, failed to unify

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 15.9s, verify 0.1s, in=4049, out=3602)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using
    (congrArg Subalgebra.toIntermediateField
      (Algebra.adjoin_root_eq_top_of_isSplittingField (K:=K) (α:=α))).symm
```

**lean_error:** tail step 1/3 ('simpa using'): <stdin>:1:11: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 50.4s, verify 0.1s, in=4090, out=6275)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
calc
  Algebra.adjoin K {α} = ⊤ := Algebra.adjoin_root_eq_top_of_isSplittingField
  _ = ⊤.toSubalgebra := by simp
```

**lean_error:** tail step 1/3 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.6s, verify 0.2s, in=4013, out=610)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (Algebra.adjoin_root_eq_top_of_isSplittingField).symm
```

**lean_error:** tail step 1/1 ('exact (Algebra.adjoin_root_eq_top_of_isSplittingField).symm'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.8s, verify 0.2s, in=3715, out=1020)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using (Algebra.adjoin_root_eq_top_of_isSplittingField (K:=K) (α:=α)).symm
```

**lean_error:** tail step 1/1 ('simpa using (Algebra.adjoin_root_eq_top_of_isSplittingField (K:=K) (α:=α)).symm'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 118.1s, verify 0.1s, in=4503, out=15448)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine (IntermediateField.eq_adjoin_of_eq_algebra_adjoin ⊤ ⊤ (by simp [IntermediateField.top_toSubalgebra]) (Eq.symm Algebra.adjoin_root_eq_top_of_isSplittingField)).symm
```

**lean_error:** tail step 1/1 ('refine (IntermediateField.eq_adjoin_of_eq_algebra_adjoin ⊤ ⊤ (by simp [IntermediateField.top_toSubalgebra]) (Eq.symm Algebra.adjoin_root_eq_top_of_isSplittingField)).symm'): failed to synthesize instance

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 14.0s, verify 0.2s, in=3969, out=1418)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Eq.symm
apply Algebra.adjoin_root_eq_top_of_isSplittingField
```

**lean_error:** tail step 2/2 ('apply Algebra.adjoin_root_eq_top_of_isSplittingField'): failed to synthesize
