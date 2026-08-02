# Int.add_emod_eq_add_emod_left   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/Int/DivMod.lean`  

**Ground-truth tail (from k):**
```lean
rw [Int.add_comm, add_emod_eq_add_emod_right _ H, Int.add_comm]
```

**True premises at k:** `Int.add_comm`, `Int.add_emod_eq_add_emod_right`, `Int.add_comm`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✓ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.1s, in=279, out=517)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [Int.add_mod, H]
```

**lean_error:** tail step 1/1 ('simpa [Int.add_mod, H]'): unknown constant 'Int.add_mod'

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 37.3s, verify 0.1s, in=223, out=4711)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
calc
  (i + m) % n = ((i % n) + (m % n)) % n := by rw [Int.add_emod]
  _ = ((i % n) + (k % n)) % n := by rw [H]
  _ = (i + k) % n := by rw [← Int.add_emod i k n]
```

**lean_error:** tail step 1/4 ('calc'): <stdin>:1:4: unexpected end of input

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 4.5s, verify 0.1s, in=224, out=433)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Int.add_emod, Int.add_emod, H]
```

**final state (truncated):**
```
m n k i : Int
H : m % n = k % n
⊢ (i % n % n + k % n % n) % n = (i + k) % n
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 2.5s, verify 0.1s, in=893, out=306)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Int.add_comm] using Int.add_emod_eq_add_emod_right i H
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 13.7s, verify 0.1s, in=849, out=1434)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [add_comm i m]
rw [add_comm i k]
apply Int.add_emod_eq_add_emod_right i H
```

**lean_error:** tail step 1/3 ('rw [add_comm i m]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 3.3s, verify 0.1s, in=840, out=303)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Int.add_comm i m, Int.add_comm i k]
exact Int.add_emod_eq_add_emod_right i H
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 3.9s, verify 0.1s, in=1439, out=401)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Int.add_comm] using (Int.add_emod_eq_add_emod_right i H)
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 11.9s, verify 0.1s, in=1409, out=1244)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
calc
  (i + m) % n = (m + i) % n := by rw [add_comm]
  _ = (k + i) % n := by apply Int.add_emod_eq_add_emod_right i H
  _ = (i + k) % n := by rw [add_comm]
```

**lean_error:** tail step 1/4 ('calc'): <stdin>:1:4: unexpected end of input

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.0s, verify 0.2s, in=1401, out=486)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Int.add_comm, Int.add_comm]
apply Int.add_emod_eq_add_emod_right
exact H
```

**lean_error:** tail step 2/3 ('apply Int.add_emod_eq_add_emod_right'): tactic 'apply' failed, failed to unify

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 1.5s, verify 0.1s, in=1411, out=305)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Int.add_comm] using Int.add_emod_eq_add_emod_right i H
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 11.7s, verify 0.1s, in=1522, out=1163)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
calc
  (i + m) % n = (m + i) % n := by rw [Int.add_comm]
  _ = (k + i) % n := by apply Int.add_emod_eq_add_emod_right H
  _ = (i + k) % n := by rw [Int.add_comm]
```

**lean_error:** tail step 1/4 ('calc'): <stdin>:1:4: unexpected end of input

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 4.9s, verify 0.2s, in=1413, out=449)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Int.add_comm, Int.add_comm]
exact Int.add_emod_eq_add_emod_right i H
```

**lean_error:** tail step 2/2 ('exact Int.add_emod_eq_add_emod_right i H'): type mismatch
