# String.offsetOfPos_of_valid   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/String/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
simpa using offsetOfPosAux_of_valid [] l r 0
```

**True premises at k:** `String.offsetOfPosAux_of_valid`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.7s, verify 0.1s, in=284, out=1303)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
induction l with
| nil =>
    simp [utf8Len, offsetOfPos]
| cons a t ih =>
    simp [utf8Len, offsetOfPos, List.length, ih, Nat.add_comm, Nat.add_left_comm, Nat.add_assoc]
```

**lean_error:** tail step 1/5 ('induction l with'): <stdin>:1:16: unexpected end of input; expected '|'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 12.3s, verify 0.2s, in=718, out=1996)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold offsetOfPos
  simpa using (offsetOfPosAux_of_valid [] l r 0)
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.9s, verify 0.2s, in=2216, out=908)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold offsetOfPos
simpa using offsetOfPosAux_of_valid [] l r 0
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 13.0s, verify 0.1s, in=2052, out=2115)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [offsetOfPos] using
  offsetOfPosAux_of_valid [] l r 0
```

**lean_error:** tail step 1/2 ('simpa [offsetOfPos] using'): <stdin>:1:25: unexpected end of input
