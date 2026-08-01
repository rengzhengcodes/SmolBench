# isPurelyInseparable_iff_minpoly_eq_X_sub_C_pow   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/PurelyInseparable.lean`  

**Ground-truth tail (from k):**
```lean
simp_rw [isPurelyInseparable_iff_natSepDegree_eq_one,
  minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow q]
```

**True premises at k:** `isPurelyInseparable_iff_natSepDegree_eq_one`, `minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.2s, verify 0.3s, in=353, out=57)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine' ⟨fun h x => _, fun h => _⟩
· obtain ⟨n, hn⟩ := h x
  use n
  exact hn
· intro x
  obtain ⟨n, hn⟩ := h x
  exact ⟨n, hn⟩
```

**lean_error:** tail step 2/7 ('· obtain ⟨n, hn⟩ := h x'): function expected at

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.1s, in=322, out=124)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [IsPurelyInseparable]
simp_rw [purelyInseparable, ← map_minpoly]
simp only [separable_iff_map, hF, Algebra.id, map_pow, map_sub, map_X, map_C]
constructor
· intro h x
  obtain ⟨n, hxn⟩ := h x
  exact ⟨n, by rwa [hxn]⟩
· intro h x hx
  obtain ⟨n, hn⟩ := h x
  refine ⟨n, ?_⟩
  rw [← hn]
  simp only [hx, sub_zero]
```

**lean_error:** tail step 1/12 ('rw [IsPurelyInseparable]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 52.6s, verify 0.1s, in=342, out=3260)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split,
{ intros h x, obtain ⟨n, _⟩ := h x, use n, rw [minpoly.eq_X_pow_q_n, polynomial.map_X_pow_q_n] },
{ intros h x, obtain ⟨n, e⟩ := h x, use n, rw [← polynomial.map_injective, e, minpoly.eq_X_pow_q_n] }
```

**lean_error:** tail step 1/3 ('split,'): <stdin>:1:5: expected end of input

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.2s, in=1222, out=34)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isPurelyInseparable_iff_natSepDegree_eq_one]
simp_rw [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow]
```

**lean_error:** tail step 2/2 ('simp_rw [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow]'): simp made no progress

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.6s, in=1187, out=34)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isPurelyInseparable_iff_natSepDegree_eq_one]
simp_rw [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow]
```

**lean_error:** tail step 2/2 ('simp_rw [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow]'): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=1211, out=33)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [isPurelyInseparable_iff_natSepDegree_eq_one, natSepDegree_eq_one_iff_eq_X_sub_C_pow]
```

**lean_error:** tail step 1/1 ('simp_rw [isPurelyInseparable_iff_natSepDegree_eq_one, natSepDegree_eq_one_iff_eq_X_sub_C_pow]'): unknown identifier 'natSepDegree_eq_one_iff_eq_X_sub_C_pow'

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 2.7s, verify 0.2s, in=4764, out=35)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isPurelyInseparable_iff_natSepDegree_eq_one]
simp_rw [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow q]
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=4696, out=34)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isPurelyInseparable_iff_natSepDegree_eq_one]
simp_rw [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow]
```

**lean_error:** tail step 2/2 ('simp_rw [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow]'): simp made no progress

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.3s, in=4753, out=43)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isPurelyInseparable_iff_natSepDegree_eq_one]
apply forall_congr
exact (natSepDegree_eq_one_iff_eq_X_sub_C_pow q).symm
```

**lean_error:** tail step 2/3 ('apply forall_congr'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 3.0s, verify 0.2s, in=4791, out=40)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isPurelyInseparable_iff_natSepDegree_eq_one]
simp_rw [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow q]
exact Iff.rfl
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.2s, in=5163, out=34)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isPurelyInseparable_iff_natSepDegree_eq_one]
simp_rw [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow]
```

**lean_error:** tail step 2/2 ('simp_rw [minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow]'): simp made no progress

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=4780, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isPurelyInseparable_iff_natSepDegree_eq_one, natSepDegree_eq_one_iff_eq_X_sub_C_pow]
```

**lean_error:** tail step 1/1 ('rw [isPurelyInseparable_iff_natSepDegree_eq_one, natSepDegree_eq_one_iff_eq_X_sub_C_pow]'): tactic 'rewrite' failed, equality or iff proof expected
