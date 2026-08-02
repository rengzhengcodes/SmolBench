# Polynomial.natSepDegree_smul_nonzero   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/SeparableDegree.lean`  

**Ground-truth tail (from k):**
```lean
simp only [natSepDegree_eq_of_isAlgClosed (AlgebraicClosure F), aroots_smul_nonzero _ hx]
```

**True premises at k:** `Polynomial.natSepDegree_eq_of_isAlgClosed`, `AlgebraicClosure`, `Polynomial.aroots_smul_nonzero`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.1s, verify 0.1s, in=332, out=723)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (natSepDegree_smul (x:=x) (f:=f) hx)
```

**lean_error:** tail step 1/1 ('simpa using (natSepDegree_smul (x:=x) (f:=f) hx)'): unknown identifier 'natSepDegree_smul'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 66.4s, verify 0.1s, in=282, out=8057)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply natSepDegree_cmul
<;> assumption
```

**lean_error:** tail step 1/2 ('apply natSepDegree_cmul'): unknown identifier 'natSepDegree_cmul'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.1s, verify 0.1s, in=277, out=612)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [hx]
```

**lean_error:** tail step 1/1 ('simp [hx]'): simp made no progress

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.0s, verify 0.1s, in=979, out=1175)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Polynomial.natSepDegree_eq_of_isAlgClosed (f := x • f) (E := AlgebraicClosure F),
        Polynomial.natSepDegree_eq_of_isAlgClosed (f := f) (E := AlgebraicClosure F)]
```

**lean_error:** tail step 1/2 ('simpa [Polynomial.natSepDegree_eq_of_isAlgClosed (f := x • f) (E := AlgebraicClosure F),'): <stdin>:1:88: unexpected end of input; expected '*' or '-'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 99.8s, verify 0.1s, in=973, out=12139)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
by
  have h₁ : natSepDegree f = (f.aroots (AlgebraicClosure F)).toFinset.card := by
    apply Polynomial.natSepDegree_eq_of_isAlgClosed
    <;> infer_instance
  
  have h₂ : natSepDegree (x • f) = ((x • f).aroots (AlgebraicClosure F)).toFinset.card := by
    apply Polynomial.natSepDegree_eq_of_isAlgClosed
    <;> infer_instance
  
  have h₃ : (x • f).aroots (AlgebraicClosure F) = f.aroots (AlgebraicClosure F) := by
    apply Polynomial.aroots_smul_nonzero
    <;> infer_instance
  
  have h₄ : natSepDegree (x • f) = natSepDegree f := by
    rw [h₂]
    rw [h₃]
    rw [h₁]
  
  exact h₄
```

**lean_error:** tail step 1/15 ('by'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.4s, verify 0.1s, in=943, out=641)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [natSepDegree_eq_of_isAlgClosed, natSepDegree_eq_of_isAlgClosed]
rw [aroots_smul_nonzero _ hx]
```

**lean_error:** tail step 1/2 ('rw [natSepDegree_eq_of_isAlgClosed, natSepDegree_eq_of_isAlgClosed]'): failed to synthesize

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 9.2s, verify 0.5s, in=2921, out=1448)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ := (Polynomial.natSepDegree_eq_of_isAlgClosed (f := x • f) (E := AlgebraicClosure F))
have h₂ := (Polynomial.natSepDegree_eq_of_isAlgClosed (f := f) (E := AlgebraicClosure F))
rw [h₁, h₂]
simp [Polynomial.aroots_smul_nonzero _ hx]
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 73.2s, verify 0.7s, in=2992, out=8939)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ : natSepDegree f = (f.aroots (AlgebraicClosure F)).toFinset.card := by
  apply Polynomial.natSepDegree_eq_of_isAlgClosed
  <;> infer_instance
have h₂ : natSepDegree (x • f) = ((x • f).aroots (AlgebraicClosure F)).toFinset.card := by
  apply Polynomial.natSepDegree_eq_of_isAlgClosed
  <;> infer_instance
have h₃ : (x • f).aroots (AlgebraicClosure F) = f.aroots (AlgebraicClosure F) := by
  apply Polynomial.aroots_smul_nonzero
  <;> infer_instance
have h₄ : ((x • f).aroots (AlgebraicClosure F)).toFinset.card = (f.aroots (AlgebraicClosure F)).toFinset.card := by
  rw [h₃]
have h₅ : natSepDegree (x • f) = natSepDegree f := by
  calc
    natSepDegree (x • f) = ((x • f).aroots (AlgebraicClosure F)).toFinset.card := by rw [h₂]
    _ = (f.aroots (AlgebraicClosure F)).toFinset.card := by rw [h₃]
    _ = natSepDegree f := by rw [h₁.symm]
exact h₅
```

**lean_error:** tail step 1/17 ('have h₁ : natSepDegree f = (f.aroots (AlgebraicClosure F)).toFinset.card := by'): <stdin>:1:78: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.0s, verify 0.1s, in=2902, out=593)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [natSepDegree_eq_of_isAlgClosed, natSepDegree_eq_of_isAlgClosed]
rw [aroots_smul_nonzero _ _ hx]
```

**lean_error:** tail step 1/2 ('rw [natSepDegree_eq_of_isAlgClosed, natSepDegree_eq_of_isAlgClosed]'): failed to synthesize

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.5s, verify 0.5s, in=2717, out=1141)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Polynomial.natSepDegree_eq_of_isAlgClosed (f:=x • f) (E:=AlgebraicClosure F),
       Polynomial.natSepDegree_eq_of_isAlgClosed (f:=f) (E:=AlgebraicClosure F),
       Polynomial.aroots_smul_nonzero (p:=f) hx]
```

**lean_error:** tail step 1/3 ('simpa [Polynomial.natSepDegree_eq_of_isAlgClosed (f:=x • f) (E:=AlgebraicClosure F),'): <stdin>:1:84: unexpected end of input; expected '*' or '-'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 136.4s, verify 0.1s, in=3245, out=16369)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
theorem Polynomial.natSepDegree_smul_nonzero {F : Type u} [Field F] {E : Type v} [Field E] [Algebra F E] {K : Type w} [Field K] [Algebra F K] (f : F[X]) (x : F) (hx : x ≠ 0) :
    natSepDegree (x • f) = natSepDegree f := by
  have h₁ : natSepDegree f = (f.aroots (AlgebraicClosure F)).toFinset.card := by
    apply Polynomial.natSepDegree_eq_of_isAlgClosed
    <;> infer_instance
  
  have h₂ : natSepDegree (x • f) = ((x • f).aroots (AlgebraicClosure F)).toFinset.card := by
    apply Polynomial.natSepDegree_eq_of_isAlgClosed
    <;> infer_instance
  
  have h₃ : (x • f).aroots (AlgebraicClosure F) = f.aroots (AlgebraicClosure F) := by
    apply Polynomial.aroots_smul_nonzero
    <;> infer_instance
    <;> exact hx
  
  have h₄ : ((x • f).aroots (AlgebraicClosure F)).toFinset.card = (f.aroots (AlgebraicClosure F)).toFinset.card := by
    rw [h₃]
  
  have h₅ : natSepDegree (x • f) = natSepDegree f := by
    rw [h₂]
    rw [h₄]
    rw [h₁]
  
  exact h₅
```

**lean_error:** tail step 1/19 ('theorem Polynomial.natSepDegree_smul_nonzero {F : Type u} [Field F] {E : Type v} [Field E] [Algebra F E] {K : Type w} [Field K] [Algebra F K] (f : F[X]) (x : F) (hx : x ≠ 0) :'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.9s, verify 0.1s, in=2877, out=590)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [natSepDegree_eq_of_isAlgClosed, natSepDegree_eq_of_isAlgClosed]
simp [aroots_smul_nonzero, hx]
```

**lean_error:** tail step 1/2 ('rw [natSepDegree_eq_of_isAlgClosed, natSepDegree_eq_of_isAlgClosed]'): failed to synthesize
