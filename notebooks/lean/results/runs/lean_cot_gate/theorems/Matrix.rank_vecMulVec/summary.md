# Matrix.rank_vecMulVec   (k=4, 5 tactics total)

file: `Mathlib/LinearAlgebra/FreeModule/Finite/Matrix.lean`  

**Ground-truth tail (from k):**
```lean
rw [rank_fun', Fintype.card_unit, Nat.cast_one]
```

**True premises at k:** `rank_fun'`, `Fintype.card_unit`, `Nat.cast_one`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | · · · ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `hint:3` | · · · · | ✓ ✓ ✘ ✘ | ✓ ✓ · ✘ |
| `noise:3` | · · · · | ✓ ✓ ✘ ✓ | · ✓ ✓ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 38.0s, verify 0.1s, in=264, out=1697)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Module.rank_eq_of_linearEquiv (linearEquiv.funUnique K Unit), Module.rank_self]
```

**lean_error:** tail step 1/1 ('rw [Module.rank_eq_of_linearEquiv (linearEquiv.funUnique K Unit), Module.rank_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 51.9s, verify 0.1s, in=264, out=2375)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Module.rank_eq_of_linearEquiv (LinearEquiv.funUnique K Unit)
apply Module.rank_self K
```

**lean_error:** tail step 1/2 ('apply Module.rank_eq_of_linearEquiv (LinearEquiv.funUnique K Unit)'): unknown constant 'Module.rank_eq_of_linearEquiv'

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 56.3s, verify 0.1s, in=264, out=2609)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Module.rank_eq_of_linearEquiv (LinearEquiv.funUnique K Unit), Module.rank_self]
```

**lean_error:** tail step 1/1 ('rw [Module.rank_eq_of_linearEquiv (LinearEquiv.funUnique K Unit), Module.rank_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 101.0s, verify 0.1s, in=264, out=4667)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [(Basis.fun K Unit).rank_eq, Fintype.card_unit]
```

**lean_error:** tail step 1/1 ('rw [(Basis.fun K Unit).rank_eq, Fintype.card_unit]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.7s, verify 0.4s, in=264, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.1s, verify 0.1s, in=264, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.2s, verify 0.1s, in=264, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.4s, verify 0.1s, in=264, out=30)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← FiniteDimensional.finrank_eq_card_basis Unit.basisFun, FiniteDimensional.finrank_eq_card_basis]
```

**lean_error:** tail step 1/1 ('rw [← FiniteDimensional.finrank_eq_card_basis Unit.basisFun, FiniteDimensional.finrank_eq_card_basis]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 5.7s, verify 0.1s, in=264, out=166)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa only [rank_eq_card_basis (Unit.basisFun K)] using (Unit.basisFun K).card_eq_one
```

**lean_error:** tail step 1/1 ('simpa only [rank_eq_card_basis (Unit.basisFun K)] using (Unit.basisFun K).card_eq_one'): unknown constant 'Unit.basisFun'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 7.4s, verify 0.1s, in=264, out=186)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Equiv.PiUnit, rank_self]
```

**lean_error:** tail step 1/1 ('rw [Equiv.PiUnit, rank_self]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 7.5s, verify 0.1s, in=264, out=212)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [fintypeEquivRep]
```

**lean_error:** tail step 1/1 ('rw [fintypeEquivRep]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 8.4s, verify 0.1s, in=264, out=245)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Module.rank_eq_card_basis, pi.basisFun K Unit]
```

**lean_error:** tail step 1/1 ('simp [Module.rank_eq_card_basis, pi.basisFun K Unit]'): unknown constant 'Module.rank_eq_card_basis'

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **incomplete**  (gen 21.6s, verify 0.1s, in=707, out=978)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit]
```

**final state (truncated):**
```
R : Type u
S : Type u'
M : Type v
N : Type w
K m n : Type u
inst✝² : CommRing K
...
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **incomplete**  (gen 65.9s, verify 0.1s, in=707, out=3075)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit]
```

**final state (truncated):**
```
R : Type u
S : Type u'
M : Type v
N : Type w
K m n : Type u
inst✝² : CommRing K
...
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 68.8s, verify 0.1s, in=707, out=3208)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit]
```

**final state (truncated):**
```
R : Type u
S : Type u'
M : Type v
N : Type w
K m n : Type u
inst✝² : CommRing K
...
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 132.6s, verify 0.2s, in=707, out=6094)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit]
trivial
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.3s, verify 0.1s, in=707, out=10)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [rank_fun']
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.7s, verify 0.1s, in=707, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [rank_fun', Fintype.card_unit]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.9s, verify 0.1s, in=707, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit, Nat.cast_one]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.2s, verify 0.1s, in=707, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit, Nat.cast_one]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 7.0s, verify 0.1s, in=707, out=206)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [rank_fun', Fintype.card_unit, Nat.cast_one]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 7.3s, verify 0.1s, in=707, out=213)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit, Nat.cast_one]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 9.6s, verify 0.1s, in=707, out=284)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [rank_fun', Fintype.card_unit, Nat.cast_one]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 10.0s, verify 0.1s, in=707, out=296)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit, Nat.cast_one]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **incomplete**  (gen 72.6s, verify 0.1s, in=1787, out=2398)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit]
```

**final state (truncated):**
```
R : Type u
S : Type u'
M : Type v
N : Type w
K m n : Type u
inst✝² : CommRing K
...
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **incomplete**  (gen 79.1s, verify 0.1s, in=1787, out=2113)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit]
```

**final state (truncated):**
```
R : Type u
S : Type u'
M : Type v
N : Type w
K m n : Type u
inst✝² : CommRing K
...
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **incomplete**  (gen 90.4s, verify 0.1s, in=1787, out=2464)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit]
```

**final state (truncated):**
```
R : Type u
S : Type u'
M : Type v
N : Type w
K m n : Type u
inst✝² : CommRing K
...
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 115.8s, verify 0.3s, in=1787, out=4757)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit]
```

**final state (truncated):**
```
R : Type u
S : Type u'
M : Type v
N : Type w
K m n : Type u
inst✝² : CommRing K
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.3s, verify 0.1s, in=1787, out=10)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [rank_fun']
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.5s, verify 0.1s, in=1787, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [rank_fun', Fintype.card_unit]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.6s, verify 0.1s, in=1787, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (rank_fun' K Unit).trans Fintype.card_unit.trans Nat.cast_one
```

**lean_error:** tail step 1/1 ("exact (rank_fun' K Unit).trans Fintype.card_unit.trans Nat.cast_one"): function expected at

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.7s, verify 0.1s, in=1787, out=34)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (rank_fun' : Module.rank K (Unit → K) = _).trans (Fintype.card_unit.trans Nat.cast_one)
```

**lean_error:** tail step 1/1 ("exact (rank_fun' : Module.rank K (Unit → K) = _).trans (Fintype.card_unit.trans Nat.cast_one)"): application type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 14.4s, verify 0.1s, in=1787, out=226)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit, Nat.cast_one]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 15.5s, verify 0.1s, in=1787, out=258)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit, Nat.cast_one]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 15.7s, verify 0.1s, in=1787, out=257)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit]
```

**final state (truncated):**
```
R : Type u
S : Type u'
M : Type v
N : Type w
K m n : Type u
inst✝² : CommRing K
...
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 22.8s, verify 0.3s, in=1787, out=605)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
refine' (Matrix.rank_vecMulVec w v).trans_le (LinearMap.rank_eq _).le
```

**lean_error:** tail step 1/1 ("refine' (Matrix.rank_vecMulVec w v).trans_le (LinearMap.rank_eq _).le"): invalid field 'trans_le', the environment does not contain 'LE.le.trans_le'

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **incomplete**  (gen 13.1s, verify 0.1s, in=1815, out=563)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit]
```

**final state (truncated):**
```
R : Type u
S : Type u'
M : Type v
N : Type w
K m n : Type u
inst✝² : CommRing K
...
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **incomplete**  (gen 34.6s, verify 0.1s, in=1815, out=1549)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit]
```

**final state (truncated):**
```
R : Type u
S : Type u'
M : Type v
N : Type w
K m n : Type u
inst✝² : CommRing K
...
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 37.4s, verify 0.1s, in=1815, out=1672)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit]
```

**final state (truncated):**
```
R : Type u
S : Type u'
M : Type v
N : Type w
K m n : Type u
inst✝² : CommRing K
...
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **incomplete**  (gen 52.5s, verify 0.1s, in=1815, out=2418)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit]
```

**final state (truncated):**
```
R : Type u
S : Type u'
M : Type v
N : Type w
K m n : Type u
inst✝² : CommRing K
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.5s, verify 0.1s, in=1815, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [rank_fun', Fintype.card_unit]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.6s, verify 0.1s, in=1815, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [rank_fun', Fintype.card_unit]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.8s, verify 0.1s, in=1815, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (rank_fun' K Unit).trans Fintype.card_unit
```

**lean_error:** tail step 1/1 ("exact (rank_fun' K Unit).trans Fintype.card_unit"): function expected at

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.0s, verify 0.1s, in=1815, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (rank_fun' : Module.rank K (Unit → K) = _)
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 6.7s, verify 0.1s, in=1815, out=196)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit]
```

**final state (truncated):**
```
R : Type u
S : Type u'
M : Type v
N : Type w
K m n : Type u
inst✝² : CommRing K
...
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 9.5s, verify 0.1s, in=1815, out=280)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit, Nat.cast_one]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 10.8s, verify 0.1s, in=1815, out=323)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [rank_fun', Fintype.card_unit, Nat.cast_one]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 11.8s, verify 0.1s, in=1815, out=346)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa only [rank_fun', Fintype.card_unit, Nat.cast_one] using ⟨one_le_rank_iff.2 a✝, LinearMap.rank_le_domain _⟩
```

**lean_error:** tail step 1/1 ("simpa only [rank_fun', Fintype.card_unit, Nat.cast_one] using ⟨one_le_rank_iff.2 a✝, LinearMap.rank_le_domain _⟩"): <stdin>:1:82: expected token
