# Rat.mk_eq_divInt   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/Rat/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [mk_eq_mkRat]
```

**True premises at k:** `Rat.mk_eq_mkRat`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=272, out=28)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Rat.eq_iff_num_and_den_eq.mpr
constructor
rfl
rw [Rat.den]
rfl
exact nz
```

**lean_error:** tail step 1/6 ('apply Rat.eq_iff_num_and_den_eq.mpr'): unknown constant 'Rat.eq_iff_num_and_den_eq.mpr'

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=246, out=30)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
simp [divInt_eq', ne_eq, nz, Int.ofNat_eq_coe, Int.natAbs_ofNat, c]
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 47.0s, verify 0.1s, in=261, out=3014)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Quotient.mk.inj
congr
simp [Rat.num, Rat.den, Rat.den_nz, Rat.reduced]
exact c
```

**lean_error:** tail step 1/4 ('apply Quotient.mk.inj'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=480, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Rat.mk_eq_mkRat num den nz c]
exact Rat.mkRat_eq_divInt num den nz
```

**lean_error:** tail step 2/2 ('exact Rat.mkRat_eq_divInt num den nz'): unknown constant 'Rat.mkRat_eq_divInt'

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=442, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Rat.mk_eq_mkRat, ← Rat.divInt_eq_mkRat]
rfl
```

**lean_error:** tail step 1/2 ('rw [Rat.mk_eq_mkRat, ← Rat.divInt_eq_mkRat]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=469, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply mk_eq_mkRat
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.2s, in=774, out=70)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Rat.mk_eq_mkRat num den nz c]
rw [Rat.mkRat, dif_neg nz]
rw [Rat.normalize_eq_mkRat nz]
rw [Rat.mkRat, dif_neg nz]
rw [Int.divInt_eq_of_coprime (Int.natAbs num) den c]
```

**lean_error:** tail step 2/5 ('rw [Rat.mkRat, dif_neg nz]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.2s, in=730, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Rat.mk_eq_mkRat, mkRat_eq_divInt]
```

**lean_error:** tail step 1/1 ('rw [Rat.mk_eq_mkRat, mkRat_eq_divInt]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.5s, verify 0.1s, in=763, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply mk_eq_mkRat
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=798, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Rat.mk_eq_mkRat num den nz c]
rw [Rat.mkRat_eq_divInt num den nz]
```

**lean_error:** tail step 2/2 ('rw [Rat.mkRat_eq_divInt num den nz]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=793, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Rat.mk_eq_mkRat, ←Rat.divInt_eq_mkRat]
simp only [Int.cast_natCast]
```

**lean_error:** tail step 1/2 ('rw [Rat.mk_eq_mkRat, ←Rat.divInt_eq_mkRat]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.4s, verify 0.1s, in=787, out=11)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply mk_eq_mkRat
```
