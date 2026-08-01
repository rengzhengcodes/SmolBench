# CategoryTheory.Functor.preservesZeroMorphisms_of_map_exact   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Abelian/Exact.lean`  

**Ground-truth tail (from k):**
```lean
exact preservesZeroMorphisms_of_map_zero_object (idZeroEquivIsoZero _ h)
```

**True premises at k:** `CategoryTheory.Functor.preservesZeroMorphisms_of_map_zero_object`, `CategoryTheory.Limits.idZeroEquivIsoZero`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=322, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
intro X Y f hf
rw [hf, ←L.map_zero]
apply h
```

**lean_error:** tail step 2/4 ('intro X Y f hf'): tactic 'introN' failed, insufficient number of binders

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.6s, in=292, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
intro X Y f hf
dsimp
rw [Functor.map_zero, h]
rfl
```

**lean_error:** tail step 2/5 ('intro X Y f hf'): tactic 'introN' failed, insufficient number of binders

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.3s, in=311, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply PreservesZeroMorphisms.mk
apply h
```

**lean_error:** tail step 2/2 ('apply h'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=955, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact CategoryTheory.Functor.preservesZeroMorphisms_of_map_zero_object (CategoryTheory.Limits.idZeroEquivIsoZero _ h)
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=912, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object
apply (idZeroEquivIsoZero _).symm
exact h
```

**lean_error:** tail step 2/3 ('apply (idZeroEquivIsoZero _).symm'): tactic 'apply' failed, failed to unify

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.9s, verify 0.2s, in=944, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object
exact (idZeroEquivIsoZero _).toFun h
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.5s, verify 0.1s, in=1312, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact CategoryTheory.Functor.preservesZeroMorphisms_of_map_zero_object (CategoryTheory.Limits.idZeroEquivIsoZero _ h)
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.3s, in=1267, out=26)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object
apply (idZeroEquivIsoZero _).symm
exact h
```

**lean_error:** tail step 2/3 ('apply (idZeroEquivIsoZero _).symm'): tactic 'apply' failed, failed to unify

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.3s, verify 0.2s, in=1301, out=34)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object
exact (idZeroEquivIsoZero (L.obj 0)).toFun h
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=1337, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact CategoryTheory.Functor.preservesZeroMorphisms_of_map_zero_object (CategoryTheory.Limits.idZeroEquivIsoZero _ h)
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.2s, in=1337, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object
apply (idZeroEquivIsoZero _).symm.mp
exact h
```

**lean_error:** tail step 2/3 ('apply (idZeroEquivIsoZero _).symm.mp'): invalid field 'mp', the environment does not contain 'Equiv.mp'

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=1326, out=30)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply preservesZeroMorphisms_of_map_zero_object
exact (idZeroEquivIsoZero _).symm h
```

**lean_error:** tail step 2/2 ('exact (idZeroEquivIsoZero _).symm h'): type mismatch
