# RatFunc.ofFractionRing_algebraMap   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
rw [← mk_one, mk_one']
```

**True premises at k:** `RatFunc.mk_one`, `RatFunc.mk_one'`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.0s, verify 0.1s, in=327, out=312)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 107.0s, verify 0.1s, in=273, out=10845)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : RatFunc K = FractionRing K[X] := rfl
rw [h]
apply FractionRing.ext
<;> simp [algebraMap]
```

**lean_error:** tail step 1/4 ('have h : RatFunc K = FractionRing K[X] := rfl'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 24.5s, verify 0.1s, in=275, out=554)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 13.4s, verify 0.1s, in=697, out=1584)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h : (algebraMap K[X] (RatFunc K)) x = ofFractionRing (algebraMap K[X] (FractionRing K[X]) x) := by
    calc
      (algebraMap K[X] (RatFunc K)) x
          = RatFunc.mk x 1 := (RatFunc.mk_one x).symm
      _ = ofFractionRing (algebraMap K[X] (FractionRing K[X]) x) := (RatFunc.mk_one' x)
  simpa using h.symm
```

**lean_error:** tail step 1/6 ('have h : (algebraMap K[X] (RatFunc K)) x = ofFractionRing (algebraMap K[X] (FractionRing K[X]) x) := by'): <stdin>:1:103: unexpected end of input; expected '{'

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 63.8s, verify 0.1s, in=654, out=6081)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [RatFunc.mk_one]
rw [RatFunc.mk_one']
<;> rfl
```

**lean_error:** tail step 1/3 ('rw [RatFunc.mk_one]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 24.8s, verify 0.4s, in=657, out=578)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← RatFunc.mk_one' x, RatFunc.mk_one x]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 9.7s, verify 0.1s, in=1902, out=847)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 45.2s, verify 0.1s, in=1895, out=4188)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← RatFunc.mk_one]
<;> rfl
```

**lean_error:** tail step 2/2 ('<;> rfl'): <stdin>:1:0: expected tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 24.3s, verify 0.1s, in=1898, out=538)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← RatFunc.mk_one', RatFunc.mk_one]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 10.1s, verify 0.1s, in=1802, out=919)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 146.5s, verify 0.1s, in=2094, out=15684)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [RatFunc.mk_one]
rw [RatFunc.mk_one']
<;> rfl
```

**lean_error:** tail step 1/3 ('rw [RatFunc.mk_one]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 25.7s, verify 0.1s, in=1885, out=668)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← RatFunc.mk_one' x, RatFunc.mk_one x]
```
