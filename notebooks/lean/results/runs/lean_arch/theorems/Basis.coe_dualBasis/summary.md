# Basis.coe_dualBasis   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Dual.lean`  

**Ground-truth tail (from k):**
```lean
apply dualBasis_apply
```

**True premises at k:** `Basis.dualBasis_apply`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✓ |
| `hint:2` | ✓ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=326, out=53)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [dualBasis_apply, coord_apply, Finsupp.inner_sum]
congr
funext
rw [Finsupp.single_apply]
split_ifs
next h => exact h.symm
next h => exact zero_smul _ _
```

**lean_error:** tail step 1/7 ('rw [dualBasis_apply, coord_apply, Finsupp.inner_sum]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.3s, verify 0.1s, in=295, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [dualBasis_repr, coord_repr]
rfl
```

**lean_error:** tail step 1/2 ('rw [dualBasis_repr, coord_repr]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 6.5s, verify 0.1s, in=315, out=390)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [dualBasis_apply, coord_apply]
simp only [LinearEquiv.apply_apply, LinearEquiv.symm_apply_apply]
```

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 0.8s, verify 0.2s, in=522, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.dualBasis_apply]
rw [Basis.coord_apply]
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=474, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.dualBasis_apply, Basis.coord_apply]
rfl
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=511, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [dualBasis_apply, Basis.repr_self]
```

**lean_error:** tail step 1/1 ('rw [dualBasis_apply, Basis.repr_self]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
