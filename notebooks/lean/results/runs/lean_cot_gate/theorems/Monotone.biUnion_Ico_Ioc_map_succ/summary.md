# Monotone.biUnion_Ico_Ioc_map_succ   (k=8, 9 tactics total)

file: `Mathlib/Order/SuccPred/IntervalSucc.lean`  

**Ground-truth tail (from k):**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

**True premises at k:** `Order.Ico_succ_right_eq_insert_of_not_isMax`, `Set.biUnion_insert`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✘ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✘ |
| `hint:3` | ✓ ✓ ✘ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `noise:3` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 107.9s, verify 0.1s, in=421, out=4754)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [h_interval], rw [Set.bUnion_union], rw [Set.bUnion_singleton], rw [Set.union_comm]
```

**lean_error:** tail step 1/1 ('rw [h_interval], rw [Set.bUnion_union], rw [Set.bUnion_singleton], rw [Set.union_comm]'): <stdin>:1:15: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 124.6s, verify 0.1s, in=421, out=5652)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Ico_succ_right m k hmk]
rw [Set.iUnion_union]
simp only [Set.iUnion_singleton]
apply Set.union_comm
```

**lean_error:** tail step 1/4 ('rw [Ico_succ_right m k hmk]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 143.0s, verify 0.1s, in=421, out=6707)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have key_eq : Ico m (succ k) = Ico m k ∪ {k} := by
  ext i
  simp only [Set.mem_union, Set.mem_Ico, Set.mem_singleton_iff]
  constructor
  · rintro ⟨hmi, hisk⟩
    have hik : i ≤ k := le_of_lt_succ hisk
    cases le_or_eq_of_le hik
    · exact Or.inl ⟨hmi, h⟩
    · exact Or.inr (h.symm)
  · rintro (⟨hmi, hik⟩ | hk)
    · exact ⟨hmi, lt_succ_of_le hik⟩
    · rw [hk]
      exact ⟨hmk, lt_succ_self k⟩
rw [key_eq, Set.union_Union, Set.Union_singleton]
rw [Set.union_comm]
```

**lean_error:** tail step 1/15 ('have key_eq : Ico m (succ k) = Ico m k ∪ {k} := by'): <stdin>:1:50: unexpected end of input; expected '{'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 146.4s, verify 0.1s, in=421, out=6958)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h1 : Ico m (succ k) = Icc m k := by ext i; rw [Ico.mem, Icc.mem, lt_succ_iff]; constructor; · rintro ⟨h1, h2⟩; exact ⟨h1, lt_succ_iff.mp h2⟩; · rintro ⟨h1, h2⟩; exact ⟨h1, lt_succ_of_le h2⟩
have h_union : Ico m (succ k) = Ico m k ∪ {k} := by rw [h1, Icc_eq_Ico_union_right hmk]
rw [h_union]
rw [Union_union]
rw [Union_singleton]
apply union_comm
```

**lean_error:** tail step 1/6 ('have h1 : Ico m (succ k) = Icc m k := by ext i; rw [Ico.mem, Icc.mem, lt_succ_iff]; constructor; · rintro ⟨h1, h2⟩; exact ⟨h1, lt_succ_iff.mp h2⟩; · rintro ⟨h1, h2⟩; exact ⟨h1, lt_succ_of_le h2⟩'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.2s, verify 0.1s, in=421, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Ico_succ_right_eq_insert_Ico (hmk.trans_lt <| succ_gt k).ne']
```

**lean_error:** tail step 1/1 ("simp [Ico_succ_right_eq_insert_Ico (hmk.trans_lt <| succ_gt k).ne']"): unknown identifier 'Ico_succ_right_eq_insert_Ico'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.5s, verify 0.1s, in=421, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [Ico_insert_right_of_not_isMax _ hk, iUnion_union]
```

**lean_error:** tail step 1/1 ('simp_rw [Ico_insert_right_of_not_isMax _ hk, iUnion_union]'): unknown identifier 'Ico_insert_right_of_not_isMax'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.6s, verify 0.1s, in=421, out=27)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Ico_insert_right_of_succ (not_isMax_iff.1 hk).2 hmk]
```

**lean_error:** tail step 1/1 ('simp only [Ico_insert_right_of_succ (not_isMax_iff.1 hk).2 hmk]'): unknown identifier 'Ico_insert_right_of_succ'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.8s, verify 0.1s, in=421, out=44)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [mem_Ico, lt_succ_iff, lt_or_eq_of_le, sup_eq_union, exists_or_distrib, exists_eq_right,
  iUnion_or, iUnion_pos]
```

**lean_error:** tail step 1/2 ('simp only [mem_Ico, lt_succ_iff, lt_or_eq_of_le, sup_eq_union, exists_or_distrib, exists_eq_right,'): <stdin>:1:98: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 9.1s, verify 0.2s, in=421, out=248)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Union_Ico_Ioc hmk hk.lt_succ, Union_singleton, union_comm]
```

**lean_error:** tail step 1/1 ('rw [Union_Ico_Ioc hmk hk.lt_succ, Union_singleton, union_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 9.2s, verify 0.1s, in=421, out=259)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Ico_insert_right hk, Set.iUnion_union, Set.iUnion_singleton, Set.union_comm]
```

**lean_error:** tail step 1/1 ('simp only [Ico_insert_right hk, Set.iUnion_union, Set.iUnion_singleton, Set.union_comm]'): application type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 9.7s, verify 0.1s, in=421, out=276)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [Ico_insert_right (le_succ _) hk, bUnion_insert, bUnion_singleton]
```

**lean_error:** tail step 1/1 ('simp_rw [Ico_insert_right (le_succ _) hk, bUnion_insert, bUnion_singleton]'): function expected at

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 9.8s, verify 0.1s, in=421, out=280)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Ico_insert_right (lt_succ_of_not_isMax hk), bUnion_insert]
```

**lean_error:** tail step 1/1 ('simp only [Ico_insert_right (lt_succ_of_not_isMax hk), bUnion_insert]'): application type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 14.7s, verify 0.2s, in=973, out=615)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Order.Ico_succ_right_eq_insert_of_not_isMax hmk hk]
rw [Set.biUnion_insert]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 19.2s, verify 0.1s, in=973, out=808)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Order.Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert], refl
```

**lean_error:** tail step 1/1 ('rw [Order.Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert], refl'): <stdin>:1:75: expected end of input

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 20.6s, verify 0.1s, in=973, out=862)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 31.7s, verify 0.1s, in=973, out=1320)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Order.Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.2s, verify 0.1s, in=973, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.3s, verify 0.6s, in=973, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.2s, verify 0.1s, in=973, out=25)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.6s, verify 0.1s, in=973, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Order.Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 7.5s, verify 0.1s, in=973, out=208)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 9.0s, verify 0.1s, in=973, out=252)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Order.Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 9.4s, verify 0.1s, in=973, out=266)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 9.5s, verify 0.1s, in=973, out=268)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert, Ioc (f k) (f (succ k))]
```

**lean_error:** tail step 1/1 ('simp_rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert, Ioc (f k) (f (succ k))]'): no goals to be solved

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 39.6s, verify 0.1s, in=1251, out=757)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Order.Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 47.8s, verify 0.1s, in=1251, out=1380)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Order.Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 56.1s, verify 0.1s, in=1251, out=1558)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk], rw [biUnion_insert]
```

**lean_error:** tail step 1/1 ('rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk], rw [biUnion_insert]'): <stdin>:1:49: expected end of input

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 78.7s, verify 0.1s, in=1251, out=2661)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Order.Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.9s, verify 0.1s, in=1251, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.9s, verify 0.1s, in=1251, out=25)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 3.0s, verify 0.1s, in=1251, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Order.Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 3.1s, verify 0.1s, in=1251, out=26)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 14.0s, verify 0.1s, in=1251, out=216)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert, union_comm]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 15.5s, verify 0.1s, in=1251, out=265)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Order.Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 16.2s, verify 0.1s, in=1251, out=277)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 16.8s, verify 0.1s, in=1251, out=284)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Order.Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 16.5s, verify 0.1s, in=1277, out=686)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Order.Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 24.0s, verify 0.2s, in=1277, out=1004)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Order.Ico_succ_right_eq_insert_of_not_isMax hmk hk]
rw [Set.biUnion_insert]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 33.0s, verify 0.1s, in=1277, out=1371)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 76.6s, verify 0.1s, in=1277, out=3266)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.9s, verify 0.3s, in=1277, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.3s, verify 0.1s, in=1277, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.4s, verify 0.1s, in=1277, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Order.Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.7s, verify 0.1s, in=1277, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 7.9s, verify 0.1s, in=1277, out=219)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Order.Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 8.5s, verify 0.1s, in=1277, out=238)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa only [Order.Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 9.9s, verify 0.1s, in=1277, out=281)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 10.2s, verify 0.1s, in=1277, out=290)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```
