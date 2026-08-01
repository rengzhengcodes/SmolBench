# Matrix.rank_vecMulVec   (k=4, 5 tactics total)

file: `Mathlib/LinearAlgebra/FreeModule/Finite/Matrix.lean`  

**Ground-truth tail (from k):**
```lean
rw [rank_fun', Fintype.card_unit, Nat.cast_one]
```

**True premises at k:** `rank_fun'`, `Fintype.card_unit`, `Nat.cast_one`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.7s, verify 0.1s, in=292, out=37)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : (Unit → K) ≅[K] K := Module.isoK K Unit,
rw [h.rank_eq, rank_free, Fintype.card_unit]
```

**lean_error:** tail step 1/2 ('have h : (Unit → K) ≅[K] K := Module.isoK K Unit,'): <stdin>:1:20: expected token

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=265, out=58)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← Cardinal.lift_inj, Cardinal.lift_rank, Module.rank_fun]
simp only [Fintype.card_unit, Cardinal.mk_one, Cardinal.lift_one]
rw [← Cardinal.lift_one, Cardinal.lift_inj]
simp only [Cardinal.mk_one]
```

**lean_error:** tail step 1/4 ('rw [← Cardinal.lift_inj, Cardinal.lift_rank, Module.rank_fun]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=281, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Module.rank_prod
simp [Module.rank_unit]
```

**lean_error:** tail step 1/2 ('apply Module.rank_prod'): unknown constant 'Module.rank_prod'

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 2.1s, verify 0.6s, in=733, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [rank_fun']
rw [Fintype.card_unit]
rw [Nat.cast_one]
```

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=700, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← rank_fun']
simp [Fintype.card_unit]
```

**lean_error:** tail step 1/2 ("rw [← rank_fun']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.6s, verify 0.1s, in=722, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit, Nat.cast_one]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.7s, verify 0.3s, in=1811, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [rank_fun']
rw [Fintype.card_unit]
rw [Nat.cast_one]
```

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=1776, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← rank_fun']
simp only [Fintype.card_unit, Nat.cast_one]
```

**lean_error:** tail step 1/2 ("rw [← rank_fun']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.7s, verify 0.4s, in=1800, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [rank_fun']
rw [Fintype.card_unit]
rw [Nat.cast_one]
```

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.4s, verify 0.3s, in=1838, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [rank_fun']
rw [Fintype.card_unit]
rw [Nat.cast_one]
```

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=1928, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← rank_fun']
simp only [Fintype.card_unit, Nat.cast_one]
```

**lean_error:** tail step 1/2 ("rw [← rank_fun']"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.6s, verify 0.2s, in=1827, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit, Nat.cast_one]
```
