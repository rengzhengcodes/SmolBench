# Rat.divInt_mul_right   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/Rat/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simp [← divInt_mul_left (d := d) a0, Int.mul_comm]
```

**True premises at k:** `Rat.divInt_mul_left`, `Int.mul_comm`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.0s, verify 0.1s, in=273, out=2166)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply (Rat.eq_iff_mul_eq_mul).2
simp [Int.mul_comm, Int.mul_left_comm, Int.mul_assoc]
```

**lean_error:** tail step 1/2 ('apply (Rat.eq_iff_mul_eq_mul).2'): unknown constant 'Rat.eq_iff_mul_eq_mul'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.1s, verify 0.2s, in=644, out=614)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Int.mul_comm] using (Rat.divInt_mul_left (a:=a) a0)
```

**lean_error:** tail step 1/1 ('simpa [Int.mul_comm] using (Rat.divInt_mul_left (a:=a) a0)'): type mismatch

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.3s, verify 0.2s, in=1595, out=670)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Int.mul_comm] using (Rat.divInt_mul_left (a:=a) a0)
```

**lean_error:** tail step 1/1 ('simpa [Int.mul_comm] using (Rat.divInt_mul_left (a:=a) a0)'): type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.8s, verify 0.3s, in=1496, out=557)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Int.mul_comm] using (Rat.divInt_mul_left (a:=a) (n:=n) (d:=d) a0)
```
