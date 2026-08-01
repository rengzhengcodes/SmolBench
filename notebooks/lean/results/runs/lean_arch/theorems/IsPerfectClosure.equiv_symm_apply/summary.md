# IsPerfectClosure.equiv_symm_apply   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/IsPerfectClosure.lean`  

**Ground-truth tail (from k):**
```lean
rw [equiv_symm, equiv_apply j i p _ _ _ h]
```

**True premises at k:** `IsPerfectClosure.equiv_symm`, `IsPerfectClosure.equiv_apply`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | · |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.2s, in=485, out=60)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h, RingEquiv.symm_apply, iterateFrobeniusEquiv_symm_apply]
simp only [equiv_apply, iterateFrobeniusEquiv_apply]
rw [RingEquiv.toRingHom_eq_coe, RingHom.iterateFrobenius_comp]
```

**lean_error:** tail step 1/3 ('rw [h, RingEquiv.symm_apply, iterateFrobeniusEquiv_symm_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.7s, in=453, out=163)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← h]
simp_rw [RingEquiv.symm_apply_eq]
simp_rw [equiv, RingEquiv.trans_apply, RingEquiv.symm_trans_apply]
rw [iterateFrobeniusEquiv_symm, ← iterateFrobenius i, ← map_iterateFrobenius]
simp_rw [IsPerfectClosure.lift_apply]
rw [IsScalarTower.algebraMap_eq K (PerfectClosure K p) L, ← IsScalarTower.algebraMap_eq K L (Lᵖⁿ)]
simp_rw [← map_iterateFrobenius j, IsPerfectClosure.lift_apply]
rw [IsScalarTower.algebraMap_eq K (PerfectClosure K p) M, ← IsScalarTower.algebraMap_eq K M (Mᵖⁿ)]
rfl
```

**lean_error:** tail step 1/9 ('rw [← h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=474, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply RingEquiv.symm_apply_apply
apply iterateFrobeniusEquiv_symm_apply
simp [h]
```

**lean_error:** tail step 1/3 ('apply RingEquiv.symm_apply_apply'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.2s, in=850, out=42)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [equiv_symm, equiv_apply _ n y]
rw [h] 
rw [(iterateFrobeniusEquiv L p n).symm_apply] 
rw [equiv_symm]
```

**lean_error:** tail step 1/4 ('rw [equiv_symm, equiv_apply _ n y]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.4s, in=817, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← IsPerfectClosure.equiv_symm]
symm
exact IsPerfectClosure.equiv_apply _ _ _ h.symm
```

**lean_error:** tail step 3/3 ('exact IsPerfectClosure.equiv_apply _ _ _ h.symm'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 39.6s, verify 0.2s, in=839, out=2521)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [equiv_symm, equiv_apply]
```

**final state (truncated):**
```
case h
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹¹ : CommRing K
...
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=1565, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [equiv_symm, equiv_apply _ _ y h]
simp only [RingEquiv.apply_symm_apply]
```

**lean_error:** tail step 1/2 ('rw [equiv_symm, equiv_apply _ _ y h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.2s, in=1522, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← equiv_symm, RingEquiv.apply_symm_apply, equiv_apply] <;> assumption
```

**lean_error:** tail step 1/1 ('rw [← equiv_symm, RingEquiv.apply_symm_apply, equiv_apply] <;> assumption'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.6s, verify 0.2s, in=1554, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [equiv_symm, equiv_apply]
simp only [h]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=1589, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [equiv_symm, equiv_apply _ _ y h],
simp only [RingEquiv.symm_symm]
```

**lean_error:** tail step 1/2 ('rw [equiv_symm, equiv_apply _ _ y h],'): <stdin>:1:36: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.6s, in=1638, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← equiv_symm]
symm
rw [equiv_apply i j p _ n y h]
rfl
```

**lean_error:** tail step 3/4 ('rw [equiv_apply i j p _ n y h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 37.5s, verify 0.3s, in=1578, out=2383)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [equiv_symm]
apply equiv_apply
```

**final state (truncated):**
```
case h
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹¹ : CommRing K
...
```
