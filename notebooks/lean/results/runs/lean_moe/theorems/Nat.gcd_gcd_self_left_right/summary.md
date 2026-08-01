# Nat.gcd_gcd_self_left_right   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/Nat/Gcd.lean`  

**Ground-truth tail (from k):**
```lean
rw [gcd_comm, gcd_gcd_self_right_right]
```

**True premises at k:** `Nat.gcd_comm`, `Nat.gcd_gcd_self_right_right`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.0s, verify 0.1s, in=261, out=675)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [Nat.gcd_self] using (Nat.gcd_assoc n m m).symm
```

**lean_error:** tail step 1/1 ('simpa [Nat.gcd_self] using (Nat.gcd_assoc n m m).symm'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.4s, verify 0.1s, in=627, out=585)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Nat.gcd_comm] using Nat.gcd_gcd_self_right_right m n
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.1s, verify 0.1s, in=1499, out=664)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Nat.gcd_comm] using Nat.gcd_gcd_self_right_right m n
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 4.9s, verify 0.1s, in=1424, out=985)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [gcd_comm] using Nat.gcd_gcd_self_right_right m n
```
