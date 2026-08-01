# Int.add_emod_eq_add_emod_left   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/Int/DivMod.lean`  

**Ground-truth tail (from k):**
```lean
rw [Int.add_comm, add_emod_eq_add_emod_right _ H, Int.add_comm]
```

**True premises at k:** `Int.add_comm`, `Int.add_emod_eq_add_emod_right`, `Int.add_comm`

## Verdict matrix

| rung | llama-31-405b-base |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=241, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Int.add_mod, H] 
rfl
```

**lean_error:** tail step 1/2 ('rw [Int.add_mod, H]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.9s, verify 0.1s, in=241, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Int.add_mod, Int.add_mod]
exact H
```

**lean_error:** tail step 1/2 ('rw [Int.add_mod, Int.add_mod]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.0s, verify 0.1s, in=241, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Int.add_mod, Int.add_mod]
rw H
rfl
```

**lean_error:** tail step 1/3 ('rw [Int.add_mod, Int.add_mod]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 2.0s, verify 0.1s, in=241, out=62)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← H]
rw [Int.add_comm i m]
rw [Int.add_assoc k i]
rw [Int.add_comm k i]
rw [Int.add_assoc i m]
rw [(Int.add_comm i m)]
rw [Int.mod_add i m]
rw [Int.mod_add i k]
```

**lean_error:** tail step 1/8 ('rw [← H]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.1s, verify 0.2s, in=839, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Int.add_comm]
exact Int.add_emod_eq_add_emod_right i H
```

**lean_error:** tail step 2/2 ('exact Int.add_emod_eq_add_emod_right i H'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.3s, verify 0.2s, in=839, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Int.add_comm]
apply Int.add_emod_eq_add_emod_right
exact H
```

**lean_error:** tail step 2/3 ('apply Int.add_emod_eq_add_emod_right'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.5s, verify 0.2s, in=839, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Int.add_comm]
apply Int.add_emod_eq_add_emod_right
exact H
rw [Int.add_comm]
```

**lean_error:** tail step 2/4 ('apply Int.add_emod_eq_add_emod_right'): tactic 'apply' failed, failed to unify

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 1.6s, verify 0.3s, in=839, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Int.add_comm i m]
rw [Int.add_comm i k]
apply Int.add_emod_eq_add_emod_right
exact H
```
