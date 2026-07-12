# IsPerfectClosure.equiv_symm_apply   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/IsPerfectClosure.lean`  

**Ground-truth tail (from k):**
```lean
rw [equiv_symm, equiv_apply j i p _ _ _ h]
```

**True premises at k:** `IsPerfectClosure.equiv_symm`, `IsPerfectClosure.equiv_apply`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-goedel | qwen3-lean-leannav | qwen3-lean-real |
| --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | · | · |
| `hint:3` | ✘ | ✘ | ✘ | · |
| `noise:3` | ✓ | ✘ | · | · |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 176.2s, verify 0.1s, in=449, out=9608)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply RingEquiv.injective (iterateFrobeniusEquiv L p n),
rw [RingEquiv.map_pow, h, RingEquiv.symm_apply_apply],
rw [RingEquiv.map_pow, RingEquiv.apply_symm_apply]
```

**lean_error:** tail step 1/3 ('apply RingEquiv.injective (iterateFrobeniusEquiv L p n),'): <stdin>:1:55: expected end of input

### `stepk:1` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 3.6s, verify 0.4s, in=449, out=64)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [RingEquiv.symm_apply_apply, RingEquiv.apply_symm_apply, RingEquiv.apply_eq_iff_eq,
  iterateFrobeniusEquiv_apply, IsPerfectClosure.equiv_eq_iff, FrobeniusEquiv_apply, ← map_pow,
  h]
```

**lean_error:** tail step 1/3 ('simp only [RingEquiv.symm_apply_apply, RingEquiv.apply_symm_apply, RingEquiv.apply_eq_iff_eq,'): <stdin>:1:93: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 3.1s, verify 0.2s, in=449, out=101)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [RingEquiv.symm_apply_apply, RingEquiv.apply_symm_apply, RingEquiv.apply_eq_iff_eq,
  iterateFrobeniusEquiv_apply, IsPerfectClosure.equiv_apply, h, ← FrobeniusEquiv_apply,
  iterateFrobeniusEquiv_symm_apply, ← map_pow, ← map_frobenius, ← FrobeniusEquiv_symm_apply,
  RingEquiv.apply_symm_apply]
```

**lean_error:** tail step 1/4 ('simp only [RingEquiv.symm_apply_apply, RingEquiv.apply_symm_apply, RingEquiv.apply_eq_iff_eq,'): <stdin>:1:93: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-real · rollout 0 → **lean_error**  (gen 4.5s, verify 0.1s, in=449, out=93)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [RingEquiv.symm_apply_apply, RingEquiv.apply_symm_apply, RingEquiv.apply_eq_iff_eq,
  iterateFrobeniusEquiv_apply, equiv, h, FrobeniusEquiv.symm_apply, FrobeniusEquiv_apply,
  FrobeniusEquiv_trans_apply, iterateFrobeniusEquiv_trans_apply, RingHom.comp_apply,
  RingEquiv.trans_apply]
```

**lean_error:** tail step 1/4 ('simp only [RingEquiv.symm_apply_apply, RingEquiv.apply_symm_apply, RingEquiv.apply_eq_iff_eq,'): <stdin>:1:93: unexpected end of input; expected ']'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 211.6s, verify 0.2s, in=814, out=12135)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [equiv_symm]
exact (equiv_apply j i p x n y h)
```

### `hint:2` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 3.1s, verify 0.5s, in=814, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [equiv_symm, equiv_apply _ _ n _ h]
```

**lean_error:** tail step 1/1 ('simp [equiv_symm, equiv_apply _ _ n _ h]'): application type mismatch

### `hint:2` · qwen3-lean-leannav · rollout 0 → **incomplete**  (gen 3.0s, verify 0.2s, in=814, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [equiv_symm, equiv_apply, RingEquiv.symm_symm]
```

**final state (truncated):**
```
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹¹ : CommRing K
inst✝¹⁰ : CommRing L
...
```

### `hint:2` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 4.4s, verify 0.2s, in=814, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [equiv_symm, equiv_apply i j, h]
```

**final state (truncated):**
```
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹¹ : CommRing K
inst✝¹⁰ : CommRing L
...
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 165.9s, verify 0.2s, in=1532, out=9010)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [equiv_symm]
apply equiv_apply x n y h
```

**lean_error:** tail step 2/2 ('apply equiv_apply x n y h'): application type mismatch

### `hint:3` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 4.1s, verify 0.1s, in=1532, out=101)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [RingEquiv.apply_symm_apply, RingEquiv.apply_coe, equiv_apply, h, map_pow, map_pow,
  map_pow, map_pow, iterateFrobeniusEquiv_symm, RingEquiv.apply_symm_apply,
  iterateFrobeniusEquiv_symm, RingEquiv.apply_symm_apply, RingEquiv.apply_coe, RingEquiv.apply_coe,
  RingEquiv.apply_symm_apply]
```

**lean_error:** tail step 1/4 ('simp only [RingEquiv.apply_symm_apply, RingEquiv.apply_coe, equiv_apply, h, map_pow, map_pow,'): <stdin>:1:93: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-leannav · rollout 0 → **lean_error**  (gen 2.9s, verify 0.1s, in=1532, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [RingEquiv.apply_symm_apply, equiv_apply]
```

**lean_error:** tail step 1/1 ('simp only [RingEquiv.apply_symm_apply, equiv_apply]'): simp made no progress

### `hint:3` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 1.8s, verify 1.5s, in=1532, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [equiv_symm, equiv_apply i j, h]
```

**final state (truncated):**
```
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹¹ : CommRing K
inst✝¹⁰ : CommRing L
...
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 87.7s, verify 0.1s, in=1556, out=4719)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [equiv_symm, equiv_apply j i p x n y h]
```

### `noise:3` · qwen3-lean-goedel · rollout 0 → **lean_error**  (gen 2.2s, verify 1.0s, in=1556, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [equiv_symm, equiv_apply _ _ n _ h]
```

**lean_error:** tail step 1/1 ('simp [equiv_symm, equiv_apply _ _ n _ h]'): application type mismatch

### `noise:3` · qwen3-lean-leannav · rollout 0 → **incomplete**  (gen 1.4s, verify 1.5s, in=1556, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [equiv_symm, equiv_apply i j, h]
```

**final state (truncated):**
```
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹¹ : CommRing K
inst✝¹⁰ : CommRing L
...
```

### `noise:3` · qwen3-lean-real · rollout 0 → **incomplete**  (gen 3.3s, verify 1.0s, in=1556, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [equiv_symm, equiv_apply i j, h]
```

**final state (truncated):**
```
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹¹ : CommRing K
inst✝¹⁰ : CommRing L
...
```
