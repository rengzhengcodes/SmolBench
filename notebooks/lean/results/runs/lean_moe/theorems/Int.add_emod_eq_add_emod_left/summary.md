# Int.add_emod_eq_add_emod_left   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/Int/DivMod.lean`  

**Ground-truth tail (from k):**
```lean
rw [Int.add_comm, add_emod_eq_add_emod_right _ H, Int.add_comm]
```

**True premises at k:** `Int.add_comm`, `Int.add_emod_eq_add_emod_right`, `Int.add_comm`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✓ |
| `noise:3` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=279, out=517)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [Int.add_mod, H]
```

**lean_error:** tail step 1/1 ('simpa [Int.add_mod, H]'): unknown constant 'Int.add_mod'

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.5s, verify 0.1s, in=893, out=306)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Int.add_comm] using Int.add_emod_eq_add_emod_right i H
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.9s, verify 0.1s, in=1439, out=401)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Int.add_comm] using (Int.add_emod_eq_add_emod_right i H)
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 1.5s, verify 0.1s, in=1411, out=305)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Int.add_comm] using Int.add_emod_eq_add_emod_right i H
```
