# Matrix.rank_vecMulVec   (k=4, 5 tactics total)

file: `Mathlib/LinearAlgebra/FreeModule/Finite/Matrix.lean`  

**Ground-truth tail (from k):**
```lean
rw [rank_fun', Fintype.card_unit, Nat.cast_one]
```

**True premises at k:** `rank_fun'`, `Fintype.card_unit`, `Nat.cast_one`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | · |
| `hint:3` | ✓ | ✘ | · |
| `noise:3` | ✓ | ✓ | · |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.8s, verify 0.1s, in=330, out=777)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (rank_fun (ι:=Unit) (M:=K))
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 77.6s, verify 0.1s, in=280, out=9383)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : Module.rank K (Unit → K) = ∑ i : Unit, Module.rank K K := by
  apply Module.rank_pi
  <;> infer_instance
have h₂ : Module.rank K K = (1 : Cardinal) := by
  have h₃ : Module.rank K K = Fintype.card (PUnit : Type*) := by
    apply Module.rank_eq_fintype_card_basis
    apply Basis.singleton_one
  rw [h₃]
  <;> simp [Fintype.card_punit]
  <;> norm_cast
have h₅ : Module.rank K (Unit → K) = (1 : Cardinal) := by
  calc
    Module.rank K (Unit → K) = ∑ i : Unit, Module.rank K K := h₁
    _ = ∑ i : Unit, (1 : Cardinal) := by
      apply Finset.sum_congr rfl
      intro i _
      rw [h₂]
    _ = (1 : Cardinal) := by
      rw [Fintype.sum_const]
      <;> simp [Fintype.card_unit]
      <;> norm_cast
      <;> rfl
rw [h₅]
<;> norm_cast

<details>
<summary>Explanation of tactics</summary>
The proof proceeds in three main steps:

1. **Decompose the rank of the product**: Using `Module.rank_pi`, we show that the rank of `(Unit → K)` (which is a product over the fintype `Unit`) equals the sum of the ranks of `K` over each element of `Unit`. Since `Unit` has exactly one element, this sum will simplify to just the rank of `K`.

2. **Compute the rank of `K` over itself**: We use the fact that `K` is a free module of rank 1 over itself, with basis `{1}`. This is formalized using `Basis.singleton_one` to get a basis of `K` indexed by `PUnit` (a type with one element), and then `Module.rank_eq_fintype_card_basis` to conclude that the rank is `(1 : Cardinal)`.

3. **Simplify the sum**: The sum over `Unit` of the constant `(1 : Cardinal)` is just `(1 : Cardinal)` because `Unit` has exactly one element. This is done using `Fintype.sum_const` and simplifying the cardinality of `Unit`.

Finally, we use `norm_cast` to reconcile the cardinal `1` with the natural number `1` in the goal statement.
</details>
```

**lean_error:** tail step 1/32 ('have h₁ : Module.rank K (Unit → K) = ∑ i : Unit, Module.rank K K := by'): <stdin>:1:37: expected token

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.1s, verify 0.1s, in=276, out=574)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Module.rank_fun]
```

**lean_error:** tail step 1/1 ('simp [Module.rank_fun]'): unknown constant 'Module.rank_fun'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 10.7s, verify 0.1s, in=789, out=1663)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [rank_fun' (R:=K) (η:=Unit), Fintype.card_unit]
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 34.5s, verify 0.2s, in=760, out=3907)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [rank_fun']
<;> simp [Fintype.card_unit]
```

**lean_error:** tail step 2/2 ('<;> simp [Fintype.card_unit]'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 6.0s, verify 0.1s, in=737, out=551)

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

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.3s, verify 0.2s, in=1906, out=834)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Fintype.card_unit] using (rank_fun' (R:=K) (η:=Unit))
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 46.0s, verify 0.2s, in=1914, out=5213)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [rank_fun']
<;> infer_instance
rw [Fintype.card_unit]
```

**lean_error:** tail step 2/3 ('<;> infer_instance'): <stdin>:1:0: expected tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.0s, verify 0.1s, in=1863, out=447)

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

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 10.5s, verify 0.1s, in=1796, out=1657)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Fintype.card_unit] using (rank_fun' (R:=K) (η:=Unit))
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 28.0s, verify 0.1s, in=2070, out=3160)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply rank_fun'
rw [Fintype.card_unit]
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 5.1s, verify 0.2s, in=1856, out=462)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [rank_fun']
rw [Fintype.card_unit]
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
