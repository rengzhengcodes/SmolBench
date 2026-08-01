# Int.add_emod_eq_add_emod_left   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/Int/DivMod.lean`  

**Ground-truth tail (from k):**
```lean
rw [Int.add_comm, add_emod_eq_add_emod_right _ H, Int.add_comm]
```

**True premises at k:** `Int.add_comm`, `Int.add_emod_eq_add_emod_right`, `Int.add_comm`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✓ | ✘ |
| `hint:3` | ✓ | ✓ | ✘ |
| `noise:3` | ✓ | ✓ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=241, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Int.add_mod, H] 
rfl
```

**lean_error:** tail step 1/2 ('rw [Int.add_mod, H]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=215, out=36)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
conv =>
  lhs
  rw [Int.add_comm, Int.add_mod]
  rhs
  rw [Int.add_comm, Int.add_mod]
  rw [H]
```

**lean_error:** tail step 1/6 ('conv =>'): <stdin>:1:7: unexpected end of input; expected '{'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=230, out=8)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [H]
```

**lean_error:** tail step 1/1 ('rw [H]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.4s, verify 0.3s, in=839, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Int.add_comm i m]
rw [Int.add_comm i k]
apply Int.add_emod_eq_add_emod_right
exact H
```

### `hint:2` · llama4-maverick-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=815, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Int.add_comm i m, Int.add_emod_eq_add_emod_right i H, Int.add_comm i k]
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=828, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [add_comm i m, add_emod_eq_add_emod_right i H, add_comm i k]
```

**lean_error:** tail step 1/1 ('rw [add_comm i m, add_emod_eq_add_emod_right i H, add_comm i k]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=1380, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Int.add_comm i m, Int.add_emod_eq_add_emod_right i H, Int.add_comm i k]
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=1349, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Int.add_comm i m, Int.add_emod_eq_add_emod_right i H, Int.add_comm i k]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1369, out=28)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [add_comm i m, add_emod_eq_add_emod_right i H, add_comm i k]
```

**lean_error:** tail step 1/1 ('rw [add_comm i m, add_emod_eq_add_emod_right i H, add_comm i k]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.3s, verify 0.1s, in=1404, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Int.add_comm i m, Int.add_emod_eq_add_emod_right i H, Int.add_comm i k]
```

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.2s, in=1444, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Int.add_comm i m, Int.add_emod_eq_add_emod_right i H, Int.add_comm i k]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=1393, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [add_comm i m, add_emod_eq_add_emod_right i H, add_comm i k]
```

**lean_error:** tail step 1/1 ('rw [add_comm i m, add_emod_eq_add_emod_right i H, add_comm i k]'): tactic 'rewrite' failed, equality or iff proof expected
