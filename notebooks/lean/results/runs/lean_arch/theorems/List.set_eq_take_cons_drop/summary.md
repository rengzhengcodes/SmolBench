# List.set_eq_take_cons_drop   (k=0, 1 tactics total)

file: `.lake/packages/std/Std/Data/List/Lemmas.lean`  

**Ground-truth tail (from k):**
```lean
rw [set_eq_modifyNth, modifyNth_eq_take_cons_drop _ h]
```

**True premises at k:** `List.set_eq_modifyNth`, `List.modifyNth_eq_take_cons_drop`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=259, out=46)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [set_eq]
rw [set_rec]
rw [set_pos]
simp only [Nat.succ_eq_add_one]
rw [drop_add]
rw [drop_one]
rw [take_append]
rw [drop_append]
```

**lean_error:** tail step 1/8 ('rw [set_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=233, out=48)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [set]
simp only [take_append_drop]
rw [Nat.add_comm] at h
rw [← drop_take_succ_eq_of_lt h]
simp only [drop, take]
rw [List.append_assoc]
rfl
```

**lean_error:** tail step 1/7 ('rw [set]'): failed to rewrite using equation theorems for 'List.set'

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=248, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [set, take_append_drop]
```

**lean_error:** tail step 1/1 ('rw [set, take_append_drop]'): failed to rewrite using equation theorems for 'List.set'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.2s, in=714, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [set_eq_modifyNth]
rw [modifyNth_eq_take_cons_drop h] 
rfl
```

**lean_error:** tail step 2/3 ('rw [modifyNth_eq_take_cons_drop h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=690, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [set_eq_modifyNth, modifyNth_eq_take_cons_drop h]
simp only [get, Function.const]
```

**lean_error:** tail step 1/2 ('rw [set_eq_modifyNth, modifyNth_eq_take_cons_drop h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=703, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [set_eq_modifyNth a, modifyNth_eq_take_cons_drop _ h]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.2s, in=1482, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [set_eq_modifyNth]
rw [modifyNth_eq_take_cons_drop h] 
rfl
```

**lean_error:** tail step 2/3 ('rw [modifyNth_eq_take_cons_drop h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1464, out=28)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [set_eq_modifyNth, modifyNth_eq_take_cons_drop h]
simp only [get, Function.const]
rfl
```

**lean_error:** tail step 1/3 ('rw [set_eq_modifyNth, modifyNth_eq_take_cons_drop h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 7.4s, verify 0.1s, in=1471, out=457)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [set_eq_modifyNth, modifyNth_eq_take_cons_drop h]
```

**lean_error:** tail step 1/1 ('rw [set_eq_modifyNth, modifyNth_eq_take_cons_drop h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **success**  (gen 1.6s, verify 0.1s, in=1506, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [set_eq_modifyNth a, modifyNth_eq_take_cons_drop (fun _ => a) h]
rfl
```

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.9s, verify 0.2s, in=1570, out=36)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [set_eq_modifyNth]
rw [modifyNth_eq_take_cons_drop (fun _ => a) h]
simp only [getElem_eq_get, get]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=1495, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [set_eq_modifyNth a, modifyNth_eq_take_cons_drop _ h]
```
