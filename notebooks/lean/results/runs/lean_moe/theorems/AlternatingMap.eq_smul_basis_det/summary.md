# AlternatingMap.eq_smul_basis_det   (k=3, 4 tactics total)

file: `Mathlib/LinearAlgebra/Determinant.lean`  

**Ground-truth tail (from k):**
```lean
simp [AlternatingMap.map_perm, Basis.det_self]
```

**True premises at k:** `AlternatingMap.map_perm`, `Basis.det_self`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | · |
| `hint:2` | ✘ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 9.5s, verify 0.4s, in=450, out=1773)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [AlternatingMap.map_perm, smul_comm]
```

**final state (truncated):**
```
R : Type u_1
inst✝⁶ : CommRing R
M : Type u_2
inst✝⁵ : AddCommGroup M
inst✝⁴ : Module R M
M' : Type u_3
...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 17.6s, verify 0.2s, in=954, out=3305)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have hdet := (AlternatingMap.map_perm (g:=e.det) (v:=e) σ)
  simpa [AlternatingMap.smul_apply, Basis.det_self, Units.smul_def, mul_comm, hdet] using
    (AlternatingMap.map_perm (g:=f) (v:=e) σ)
```

**lean_error:** tail step 2/3 ('simpa [AlternatingMap.smul_apply, Basis.det_self, Units.smul_def, mul_comm, hdet] using'): <stdin>:1:87: unexpected end of input

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 12.3s, verify 0.7s, in=2123, out=2242)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [AlternatingMap.map_perm, Basis.det_self, mul_comm, mul_left_comm, mul_assoc]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 11.0s, verify 0.5s, in=2005, out=2124)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [AlternatingMap.map_perm, Basis.det_self, smul_smul, mul_comm, mul_left_comm, mul_assoc]
```
