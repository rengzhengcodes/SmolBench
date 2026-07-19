# Basis.coe_toDual_self   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Dual.lean`  

**Ground-truth tail (from k):**
```lean
apply toDual_apply_right
```

**True premises at k:** `Basis.toDual_apply_right`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.2s, verify 0.1s, in=366, out=1149)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [Basis.toDual]
```

**lean_error:** tail step 1/1 ('simpa [Basis.toDual]'): tactic 'assumption' failed

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 249.3s, verify 0.1s, in=319, out=27776)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h₁ : ((toDual b) (b i)) x✝ = ∑ j : ι, (coord b j) (b i) * (coord b j) x✝ := by
  rw [toDual_apply]
  <;> simp [mul_assoc]

have h₂ : (∑ j : ι, (coord b j) (b i) * (coord b j) x✝) = (∑ j : ι, (if j = i then (1 : R) else 0) * (coord b j) x✝) := by
  apply Finset.sum_congr rfl
  intro j _
  have h₃ : (coord b j) (b i) = if j = i then (1 : R) else 0 := by
    rw [coord_apply_basis]
    <;> simp [if_pos, if_neg]
    <;> aesop
  rw [h₃]
  <;> simp [mul_comm]
  <;> ring_nf
  <;> simp_all

have h₃ : (∑ j : ι, (if j = i then (1 : R) else 0) * (coord b j) x✝) = (∑ j : ι, (if j = i then (coord b j) x✝ else (0 : R))) := by
  apply Finset.sum_congr rfl
  intro j _
  split_ifs <;> simp [mul_zero, zero_mul] <;> ring_nf <;> simp_all

have h₄ : (∑ j : ι, (if j = i then (coord b j) x✝ else (0 : R))) = (coord b i) x✝ := by
  have h₅ : (∑ j : ι, (if j = i then (coord b j) x✝ else (0 : R))) = (coord b i) x✝ := by
    calc
      (∑ j : ι, (if j = i then (coord b j) x✝ else (0 : R))) = ∑ j : ι, if j = i then (coord b j) x✝ else 0 := by rfl
      _ = (coord b i) x✝ := by
        rw [Finset.sum_ite_eq']
        <;> simp [Finset.mem_univ, true.and]
        <;> aesop
  exact h₅

calc
  ((toDual b) (b i)) x✝ = ∑ j : ι, (coord b j) (b i) * (coord b j) x✝ := by rw [h₁]
  _ = ∑ j : ι, (if j = i then (1 : R) else 0) * (coord b j) x✝ := by rw [h₂]
  _ = ∑ j : ι, (if j = i then (coord b j) x✝ else (0 : R)) := by rw [h₃]
  _ = (coord b i) x✝ := by rw [h₄]
```

**lean_error:** tail step 1/32 ('have h₁ : ((toDual b) (b i)) x✝ = ∑ j : ι, (coord b j) (b i) * (coord b j) x✝ := by'): <stdin>:1:30: expected token

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 43.4s, verify 0.1s, in=308, out=561)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Basis.toDual_apply]
```

**final state (truncated):**
```
case h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.3s, verify 0.1s, in=567, out=669)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Basis.coord] using b.toDual_apply_right i x✝
```

**lean_error:** tail step 1/1 ('simpa [Basis.coord] using b.toDual_apply_right i x✝'): <stdin>:1:50: expected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 118.1s, verify 0.1s, in=535, out=13596)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
theorem Basis.coeToDual_self {R : Type uR} {M : Type uM} {K : Type uK} {V : Type uV} {ι : Type uι} [CommSemiring R] [AddCommMonoid M] [Module R M] [DecidableEq ι] (b : Basis ι R M) (i : ι) (x✝ : M) :
    ((toDual b) (b i)) x✝ = (coord b i) x✝ := by
  ext
  have h_main : ((toDual b) (b i)) x✝ = (coord b i) x✝ := by
    have h1 : (toDual b) = (b : Basis ι R M).toDual := by
      rfl
    rw [h1]
    have h2 : b.toDual (b i) x✝ = b.repr x✝ i := Basis.toDual_apply_right i x✝
    have h3 : (coord b i) x✝ = b.repr x✝ i := by
      dsimp [coord]
      <;> rfl
    linarith
  exact h_main
```

**lean_error:** tail step 1/13 ('theorem Basis.coeToDual_self {R : Type uR} {M : Type uM} {K : Type uK} {V : Type uV} {ι : Type uι} [CommSemiring R] [AddCommMonoid M] [Module R M] [DecidableEq ι] (b : Basis ι R M) (i : ι) (x✝ : M) :'): <stdin>:1:0: expected tactic

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 44.0s, verify 0.1s, in=515, out=619)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Basis.toDual_apply_right]
```

**final state (truncated):**
```
case h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
...
```
