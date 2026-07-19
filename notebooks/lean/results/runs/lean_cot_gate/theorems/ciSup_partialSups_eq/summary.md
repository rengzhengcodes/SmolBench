# ciSup_partialSups_eq   (k=3, 4 tactics total)

file: `Mathlib/Order/PartialSups.lean`  

**Ground-truth tail (from k):**
```lean
rwa [bddAbove_range_partialSups]
```

**True premises at k:** `bddAbove_range_partialSups`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✓ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ · | ✘ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ ✓ | · · ✓ ✓ | ✓ ✓ ✓ ✘ |
| `noise:3` | ✓ ✓ ✓ ✓ | · ✓ ✓ ✓ | ✘ ✘ ✘ · |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 101.2s, verify 0.4s, in=240, out=4298)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
obtain ⟨ub, h_ub⟩ := h
use ub
intro n
apply csSup_le
· use f 0
  apply Set.mem_image_of_mem
  exact Nat.zero_le n
· rintro x ⟨k, hk, rfl⟩
  exact h_ub (f k) (Set.mem_range.2 ⟨k, rfl⟩)
```

**lean_error:** tail step 4/9 ('apply csSup_le'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 117.5s, verify 0.4s, in=240, out=5097)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
obtain ⟨M, hM⟩ := h
use M
intro y
rintro ⟨n, rfl⟩
apply cSup_le
· exact Set.nonempty_insert _ _
· exact Set.subset_bounded_of_bounded h
· intro x hx
  rcases hx with ⟨k, hk, rfl⟩
  exact hM (f k) (Set.mem_range_self k)
```

**lean_error:** tail step 5/10 ('apply cSup_le'): unknown identifier 'cSup_le'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 162.9s, verify 0.4s, in=240, out=7186)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
obtain ⟨M, hM⟩ := h
use M
intro n
induction n with n IH
exact hM 0 (Set.mem_range_self f 0)
rw [partialSups_succ]
exact sup_le IH (hM (n + 1) (Set.mem_range_self f (n + 1)))
```

**lean_error:** tail step 4/7 ('induction n with n IH'): <stdin>:1:18: unknown tactic

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 190.3s, verify 0.1s, in=240, out=8345)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
cases h with
| intro M hM => 
   apply BddAbove.intro M
   intro x hx
   obtain ⟨n, rfl⟩ := hx
   apply sup_le
   · intro y hy
     obtain ⟨k, hk, rfl⟩ := hy
     apply hM
     use k
     rfl
   · use f 0
     use 0
     exact ⟨Nat.zero_le n, rfl⟩
```

**lean_error:** tail step 1/14 ('cases h with'): <stdin>:1:12: unexpected end of input; expected '|'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=240, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.partialSups
```

**lean_error:** tail step 1/1 ('exact h.partialSups'): invalid field 'partialSups', the environment does not contain 'BddAbove.partialSups'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.2s, verify 0.1s, in=240, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact Bounded.partialSups_bddAbove h
```

**lean_error:** tail step 1/1 ('exact Bounded.partialSups_bddAbove h'): unknown identifier 'Bounded.partialSups_bddAbove'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.4s, verify 0.1s, in=240, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.8s, verify 0.1s, in=240, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact BddAbove.mono (partialSups_le_range h) (Set.subset_range_partialSups f)
```

**lean_error:** tail step 1/1 ('exact BddAbove.mono (partialSups_le_range h) (Set.subset_range_partialSups f)'): internal exception #7

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 4.4s, verify 0.1s, in=240, out=119)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact bddAbove_range_partialSups h
```

**lean_error:** tail step 1/1 ('exact bddAbove_range_partialSups h'): function expected at

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 5.9s, verify 0.1s, in=240, out=160)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply bddAbove_range_partialSups h
```

**lean_error:** tail step 1/1 ('apply bddAbove_range_partialSups h'): function expected at

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 6.2s, verify 0.1s, in=240, out=170)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact bddAbove_range_partialSups_iff.2 h
```

**lean_error:** tail step 1/1 ('exact bddAbove_range_partialSups_iff.2 h'): unknown identifier 'bddAbove_range_partialSups_iff'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 10.5s, verify 0.1s, in=240, out=313)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact bddAbove_iff.2 ⟨⨆ i, f i, fun x hx => partialSups_le_iSup f⟩
```

**lean_error:** tail step 1/1 ('exact bddAbove_iff.2 ⟨⨆ i, f i, fun x hx => partialSups_le_iSup f⟩'): unknown identifier 'bddAbove_iff'

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 30.1s, verify 0.1s, in=510, out=1192)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 35.2s, verify 0.1s, in=510, out=1431)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.mpr h
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 44.0s, verify 0.1s, in=510, out=1816)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 61.4s, verify 0.1s, in=510, out=2553)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.0s, verify 0.1s, in=510, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [h]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.4s, verify 0.1s, in=510, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.5s, verify 0.1s, in=510, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.6s, verify 0.1s, in=510, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case refine'_2
α : Type u_1
inst✝ : ConditionallyCompleteLattice α
f : ℕ → α
h : BddAbove (Set.range f)
⊢ BddAbove (Set.range f)
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 4.3s, verify 0.1s, in=510, out=119)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.1 h
```

**lean_error:** tail step 1/1 ('exact bddAbove_range_partialSups.1 h'): application type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 5.3s, verify 0.1s, in=510, out=128)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rwa [bddAbove_range_partialSups]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 5.8s, verify 0.1s, in=510, out=155)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using h
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 7.1s, verify 0.1s, in=510, out=202)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rwa [bddAbove_range_partialSups]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 79.0s, verify 0.1s, in=1171, out=2799)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 79.5s, verify 0.1s, in=1171, out=1832)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 83.4s, verify 0.1s, in=1171, out=2328)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 84.6s, verify 0.1s, in=1171, out=2142)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.2s, verify 0.1s, in=1171, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case refine'_2
α : Type u_1
inst✝ : ConditionallyCompleteLattice α
f : ℕ → α
h : BddAbove (Set.range f)
⊢ BddAbove (Set.range f)
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.7s, verify 0.1s, in=1171, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [bddAbove_range_partialSups]
```

**final state (truncated):**
```
case refine'_2
α : Type u_1
inst✝ : ConditionallyCompleteLattice α
f : ℕ → α
h : BddAbove (Set.range f)
⊢ BddAbove (Set.range f)
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.7s, verify 0.1s, in=1171, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 3.1s, verify 0.1s, in=1171, out=16)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 8.7s, verify 0.1s, in=1171, out=131)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 9.4s, verify 0.1s, in=1171, out=149)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 10.1s, verify 0.1s, in=1171, out=152)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using bddAbove_range_partialSups.2 h
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 10.6s, verify 0.1s, in=1171, out=146)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact h
```

**lean_error:** tail step 1/1 ('exact h'): type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 12.9s, verify 0.1s, in=1196, out=526)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.mpr h
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 37.0s, verify 0.1s, in=1196, out=1514)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.mpr h
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 38.2s, verify 0.1s, in=1196, out=1567)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 43.5s, verify 0.1s, in=1196, out=1800)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 0.6s, verify 0.1s, in=1196, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case refine'_2
α : Type u_1
inst✝ : ConditionallyCompleteLattice α
f : ℕ → α
h : BddAbove (Set.range f)
⊢ BddAbove (Set.range f)
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.0s, verify 0.1s, in=1196, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [h]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.1s, verify 0.1s, in=1196, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.3s, verify 0.1s, in=1196, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact bddAbove_range_partialSups.2 h
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 5.4s, verify 0.1s, in=1196, out=135)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using bddAbove_range_partialSups.1
```

**lean_error:** tail step 1/1 ('simpa using bddAbove_range_partialSups.1'): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 5.5s, verify 0.1s, in=1196, out=147)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using bddAbove_range_partialSups
```

**lean_error:** tail step 1/1 ('simpa using bddAbove_range_partialSups'): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 5.6s, verify 0.1s, in=1196, out=149)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using bddAbove_range_partialSups
```

**lean_error:** tail step 1/1 ('simpa using bddAbove_range_partialSups'): typeclass instance problem is stuck, it is often due to metavariables

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 5.7s, verify 0.1s, in=1196, out=152)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case refine'_2
α : Type u_1
inst✝ : ConditionallyCompleteLattice α
f : ℕ → α
h : BddAbove (Set.range f)
⊢ BddAbove (Set.range f)
```
