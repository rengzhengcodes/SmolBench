# Rat.mk_eq_divInt   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/Rat/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [mk_eq_mkRat]
```

**True premises at k:** `Rat.mk_eq_mkRat`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | · | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.3s, verify 0.5s, in=311, out=1938)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (Rat.mk_eq (num:=num) (den:=den) nz c).symm
```

**lean_error:** tail step 1/1 ('simpa using (Rat.mk_eq (num:=num) (den:=den) nz c).symm'): unknown constant 'Rat.mk_eq'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 93.3s, verify 0.1s, in=258, out=11466)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Rat.ext_iff
·
  rw [Rat.num_div nz]
  have h₁ : Int.gcd (Int.natAbs num) den = Nat.gcd (Int.natAbs num) den := by
    rw [Int.gcd_eq_nat_gcd]
    <;> simp [Int.natAbs_cast]
  have h₂ : Nat.gcd (Int.natAbs num) den = 1 := c
  rw [h₁, h₂]
  <;> norm_num
  <;> rfl
·
  rw [Rat.den_div nz]
  have h : Nat.gcd (Int.natAbs num) den = 1 := c
  rw [h]
  <;> norm_num
  <;> rfl
```

**lean_error:** tail step 1/16 ('apply Rat.ext_iff'): unknown constant 'Rat.ext_iff'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.3s, verify 0.1s, in=255, out=425)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.7s, verify 0.1s, in=526, out=1612)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using Rat.mk_eq_mkRat num den nz c
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **incomplete**  (gen 6.5s, verify 0.1s, in=475, out=799)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Rat.mk_eq_mkRat]
```

**final state (truncated):**
```
num : Int
den : Nat
nz : den ≠ 0
c : Nat.Coprime (Int.natAbs num) den
⊢ mkRat num den = num /. ↑den
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.9s, verify 0.1s, in=469, out=579)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Rat.mk_eq_mkRat]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.2s, verify 0.1s, in=826, out=1245)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using Rat.mk_eq_mkRat num den nz c
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 111.4s, verify 0.2s, in=782, out=13901)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [mk_eq_mkRat]
rw [Rat.div_eq_mkRat num den nz]
```

**lean_error:** tail step 2/2 ('rw [Rat.div_eq_mkRat num den nz]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.9s, verify 0.1s, in=774, out=708)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Rat.mk_eq_mkRat
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 8.2s, verify 0.1s, in=818, out=1848)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using (Rat.mk_eq_mkRat num den nz c)
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 90.5s, verify 0.2s, in=851, out=11066)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Rat.mk_eq_mkRat]
rw [mkRat_eq_div nz]
norm_cast
<;> rfl
```

**lean_error:** tail step 2/4 ('rw [mkRat_eq_div nz]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.1s, verify 0.1s, in=793, out=465)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Rat.mk_eq_mkRat]
rfl
```
