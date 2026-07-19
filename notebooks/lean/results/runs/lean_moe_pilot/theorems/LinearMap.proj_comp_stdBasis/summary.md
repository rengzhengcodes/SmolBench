# LinearMap.proj_comp_stdBasis   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/StdBasis.lean`  

**Ground-truth tail (from k):**
```lean
rw [stdBasis_eq_pi_diag, proj_pi]
```

**True premises at k:** `LinearMap.stdBasis_eq_pi_diag`, `LinearMap.proj_pi`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.2s, verify 0.4s, in=349, out=2381)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
  by_cases h : i = j
  · subst h
    simp [LinearMap.comp_apply, diag]
  · simp [LinearMap.comp_apply, diag, h]
```

**lean_error:** tail step 3/5 ('· subst h'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 183.7s, verify 0.2s, in=297, out=19830)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
simp [LinearMap.comp_apply, proj_apply, stdBasis_apply_apply, diag]
<;> split_ifs <;> simp_all [smul_eq_mul, one_smul] <;> rfl
```

**lean_error:** tail step 2/3 ('simp [LinearMap.comp_apply, proj_apply, stdBasis_apply_apply, diag]'): unknown identifier 'stdBasis_apply_apply'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 33.0s, verify 0.1s, in=293, out=456)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.4s, verify 0.1s, in=739, out=1394)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [LinearMap.stdBasis_eq_pi_diag] using (LinearMap.proj_pi (diag j) i)
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 268.1s, verify 0.2s, in=706, out=29919)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext x
rw [stdBasis_eq_pi_diag j]
<;> dsimp [Pi, Pi.apply, LinearMap.comp_apply, LinearMap.proj_apply]
<;> rfl
```

**lean_error:** tail step 2/4 ('rw [stdBasis_eq_pi_diag j]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 32.7s, verify 0.2s, in=682, out=420)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
rw [proj_pi]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.5s, verify 0.2s, in=1163, out=1136)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [stdBasis_eq_pi_diag (R:=R) (φ:=φ) j] using (proj_pi (f:=diag j) i)
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 177.5s, verify 0.1s, in=1141, out=19167)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
calc
  proj i ∘ₗ stdBasis R φ j = proj i ∘ₗ pi (diag j) := by rw [stdBasis_eq_pi_diag j]
  _ = (proj i).comp (pi (diag j)) := rfl
  _ = (diag j) i := by
    apply @proj_pi R ι (φ j) (fun k : ι => diag j k) i
    <;> try exact inst✝² j
    <;> try exact inst✝¹ j
  _ = diag j i := by rfl
```

**lean_error:** tail step 1/8 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 32.5s, verify 0.2s, in=1115, out=407)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
rw [proj_pi]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.8s, verify 0.1s, in=1143, out=1267)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [stdBasis_eq_pi_diag] using (proj_pi (f := diag j) i)
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 291.1s, verify 0.3s, in=1226, out=32768)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h1 : stdBasis R φ j = pi (diag j) := by apply stdBasis_eq_pi_diag
have h2 : proj i ∘ₗ stdBasis R φ j = proj i ∘ₗ pi (diag j) := by rw [h1]
have h3 : (proj i).comp (pi (diag j)) = (diag j) i := by apply LinearMap.proj_pi
have h4 : proj i ∘ₗ pi (diag j) = (diag j) i := by
  rw [h3]
  <;> simp [Function.comp_apply]
have h5 : proj i ∘ₗ stdBasis R φ j = (diag j) i := by
  rw [h2, h4]
have h6 : (diag j) i = diag j i := by rfl
have h7 : proj i ∘ₗ stdBasis R φ j = diag j i := by
  rw [h5, h6]
```

**lean_error:** tail step 3/11 ('have h3 : (proj i).comp (pi (diag j)) = (diag j) i := by apply LinearMap.proj_pi'): internal exception #7

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 35.1s, verify 0.2s, in=1128, out=659)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [stdBasis_eq_pi_diag]
rw [proj_pi]
```
