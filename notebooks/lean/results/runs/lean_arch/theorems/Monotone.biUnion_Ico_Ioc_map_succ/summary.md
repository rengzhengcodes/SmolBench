# Monotone.biUnion_Ico_Ioc_map_succ   (k=8, 9 tactics total)

file: `Mathlib/Order/SuccPred/IntervalSucc.lean`  

**Ground-truth tail (from k):**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

**True premises at k:** `Order.Ico_succ_right_eq_insert_of_not_isMax`, `Set.biUnion_insert`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✓ | ✓ | ✓ |
| `noise:3` | ✘ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.5s, verify 0.2s, in=449, out=44)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Ico_succ, Union.union_comm]
rw [ihk]
exact Ioc_union_Ioc (hf (hmk.trans lt_succ_self).lt_of_le) (hf (lt_succ_self k))
```

**lean_error:** tail step 1/3 ('rw [Ico_succ, Union.union_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.2s, verify 1.6s, in=415, out=136)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [succ_eq_of_not_isMax hk, Ico_succ_right, iUnion_union]
congr 1
rw [iUnion_congr]
intro i hi
rw [succ_eq_of_not_isMax]
exact not_isMax_of_lt (hi.2.trans hk)
simp only [iUnion_insert, mem_Ico, le_refl, true_and]
rw [ihk]
simp only [not_isMax_iff_lt, hmk, hk, and_self]
rw [← Ioc_union_Ioc_eq_Ioc hf.le (le_refl _), sup_eq_right.mpr (hf _ _ hmk)]
exact hmk.trans_lt hk
```

**lean_error:** tail step 1/11 ('rw [succ_eq_of_not_isMax hk, Ico_succ_right, iUnion_union]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 119.8s, verify 0.2s, in=438, out=7676)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [←ihk, union_comm]
```

**lean_error:** tail step 1/1 ('rw [←ihk, union_comm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.5s, in=1001, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk]
rw [biUnion_insert _ _ Ioc]
rw [Ihk]
```

**lean_error:** tail step 2/3 ('rw [biUnion_insert _ _ Ioc]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=966, out=51)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert, union_assoc, union_comm (Ioc (f k) (f (succ k)))]
congr 1
exact ihk.symm
```

**lean_error:** tail step 1/3 ('rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert, union_assoc, union_comm (Ioc (f k) (f (succ k)))]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 7.1s, verify 0.1s, in=990, out=441)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **success**  (gen 2.4s, verify 0.1s, in=1277, out=35)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
simp only [Ioc_self, union_comm, union_left_comm]
```

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=1243, out=30)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert, union_comm]
simp [ihk]
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.9s, verify 0.1s, in=1266, out=39)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert _ (Ico m k)]
congr
exact ihk
```

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.3s, in=1302, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk]
rw [biUnion_insert _ _ Ioc]
```

**lean_error:** tail step 2/2 ('rw [biUnion_insert _ _ Ioc]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=1300, out=30)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert, union_comm]
simp [ihk]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=1291, out=42)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert]
simp only [insert_Ioc_of_le (hf hmk), union_assoc]
```
