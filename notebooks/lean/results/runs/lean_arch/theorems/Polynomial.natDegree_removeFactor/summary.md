# Polynomial.natDegree_removeFactor   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/SplittingField/Construction.lean`  

**Ground-truth tail (from k):**
```lean
rw [removeFactor, natDegree_divByMonic (map (AdjoinRoot.of f.factor) f) (monic_X_sub_C _),
  natDegree_map, natDegree_X_sub_C]
```

**True premises at k:** `Polynomial.removeFactor`, `Polynomial.natDegree_divByMonic`, `Polynomial.map`, `AdjoinRoot.of`, `Polynomial.monic_X_sub_C`, `Polynomial.natDegree_map`, `Polynomial.natDegree_X_sub_C`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | · | ✘ |
| `noise:3` | ✘ | · | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.2s, in=265, out=33)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
unfold removeFactor
rw [natDegree_mul, natDegree_X_sub_C]
· exact natDegree_f_fin
· exact degree_X_sub_C
· simp
```

**lean_error:** tail step 2/5 ('rw [natDegree_mul, natDegree_X_sub_C]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=239, out=50)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [removeFactor, natDegree_mul_X_sub_C]
simp only [natDegree_X, natDegree_C, sub_zero, min_eq_left, tsub_le_iff_right, le_add_iff_nonneg_left, zero_le]
ring_nf
```

**lean_error:** tail step 1/3 ('rw [removeFactor, natDegree_mul_X_sub_C]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.0s, in=254, out=2)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
(empty)
```

**lean_error:** empty tail

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.7s, verify 0.2s, in=1457, out=44)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [removeFactor, natDegree_divByMonic (monic_X_sub_C (AdjoinRoot.root f.factor))]
rw [natDegree_map (AdjoinRoot.of f.factor), natDegree_X_sub_C]
```

**lean_error:** tail step 1/2 ('rw [removeFactor, natDegree_divByMonic (monic_X_sub_C (AdjoinRoot.root f.factor))]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.3s, in=1411, out=66)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [removeFactor, natDegree_divByMonic]
· simp only [monic_X_sub_C]
· simp only [natDegree_X_sub_C, tsub_self]
rw [← natDegree_map (AdjoinRoot.of f.factor)]
simp only [Polynomial.factor, AdjoinRoot.root, map_X_sub_C]
```

**lean_error:** tail step 2/5 ('· simp only [monic_X_sub_C]'): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.2s, in=1446, out=52)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [removeFactor, map, AdjoinRoot.of, natDegree_divByMonic, monic_X_sub_C, natDegree_X_sub_C, natDegree_map, natDegree_map, add_comm, add_tsub_swap]
```

**lean_error:** tail step 1/1 ('rw [removeFactor, map, AdjoinRoot.of, natDegree_divByMonic, monic_X_sub_C, natDegree_X_sub_C, natDegree_map, natDegree_map, add_comm, add_tsub_swap]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.2s, in=4181, out=44)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [removeFactor, natDegree_divByMonic (monic_X_sub_C (AdjoinRoot.root f.factor))]
rw [natDegree_map (AdjoinRoot.of f.factor), natDegree_X_sub_C]
```

**lean_error:** tail step 1/2 ('rw [removeFactor, natDegree_divByMonic (monic_X_sub_C (AdjoinRoot.root f.factor))]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.8s, verify 0.9s, in=4102, out=41)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [removeFactor, natDegree_divByMonic]
simp only [Polynomial.monic_X_sub_C, natDegree_map, AdjoinRoot.of]
rw [natDegree_X_sub_C]
ring
```

**final state (truncated):**
```
case hg
F : Type u
K : Type v
L : Type w
inst✝² : Field K
inst✝¹ : Field L
...
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=4170, out=50)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Polynomial.natDegree_divByMonic
apply Polynomial.monic_X_sub_C
```

**lean_error:** tail step 1/2 ('apply Polynomial.natDegree_divByMonic'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.9s, verify 0.2s, in=4208, out=45)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [removeFactor, natDegree_divByMonic (monic_X_sub_C (AdjoinRoot.root f.factor))]
rw [natDegree_map (AdjoinRoot.of f.factor), natDegree_X_sub_C]
simp
```

**lean_error:** tail step 1/3 ('rw [removeFactor, natDegree_divByMonic (monic_X_sub_C (AdjoinRoot.root f.factor))]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 1.8s, verify 0.6s, in=4474, out=48)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [removeFactor, natDegree_divByMonic]
simp only [natDegree_map, AdjoinRoot.of, RingHom.coe_comp, Function.comp_apply, RingHom.coe_mk, natDegree_X_sub_C]
ring
```

**final state (truncated):**
```
case hg
F : Type u
K : Type v
L : Type w
inst✝² : Field K
inst✝¹ : Field L
...
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=4197, out=49)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Polynomial.natDegree_divByMonic
apply Polynomial.monic_X_sub_C
rw [Polynomial.natDegree_map]
apply AdjoinRoot.of
rw [Polynomial.natDegree_X_sub_C]
```

**lean_error:** tail step 1/5 ('apply Polynomial.natDegree_divByMonic'): tactic 'apply' failed, failed to unify
