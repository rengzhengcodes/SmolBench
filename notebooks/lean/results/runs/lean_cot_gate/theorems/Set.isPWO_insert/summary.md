# Set.isPWO_insert   (k=0, 1 tactics total)

file: `Mathlib/Order/WellFoundedSet.lean`  

**Ground-truth tail (from k):**
```lean
simp only [← singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**True premises at k:** `Set.singleton_union`, `Set.isPWO_union`, `Set.isPWO_singleton`, `true_and_iff`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · · ✘ ✘ | ✘ ✘ · ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✓ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 130.4s, verify 0.1s, in=259, out=5786)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
apply IsPWO.mono
exact subset_insert a s
apply IsPWO.insert
```

**lean_error:** tail step 1/4 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 167.9s, verify 0.1s, in=259, out=7363)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
apply IsPWO_subset (subset_insert a s)
intro h
apply IsPWO_insert h
```

**lean_error:** tail step 1/4 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 186.9s, verify 0.1s, in=259, out=8133)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· exact fun h => h.mono (subset_insert a s)
· exact fun h => h.insert a
```

**lean_error:** tail step 1/3 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 222.3s, verify 0.1s, in=259, out=9663)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
. apply IsPWO_of_subset; apply subset_insert
. apply IsPWO_insert
```

**lean_error:** tail step 1/3 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.1s, verify 0.1s, in=259, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [insert_eq, isPWO_union, isPWO_singleton]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
inst✝¹ : Preorder α
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 1.1s, verify 0.1s, in=259, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [insert_eq, isPWO_union, isPWO_singleton]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
inst✝¹ : Preorder α
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.2s, verify 0.1s, in=259, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [insert_eq, isPWO_union, isPWO_singleton, iff_true_iff]
```

**lean_error:** tail step 1/1 ('simp_rw [insert_eq, isPWO_union, isPWO_singleton, iff_true_iff]'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 70.5s, verify 0.4s, in=259, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [insert_eq, isPWO_union]
```

**lean_error:** tail step 1/1 ('simp [insert_eq, isPWO_union]'): tactic 'simp' failed, nested error:

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 5.0s, verify 0.1s, in=259, out=151)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [insert_eq, isPWO_union_left]
```

**lean_error:** tail step 1/1 ('rw [insert_eq, isPWO_union_left]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 5.8s, verify 0.1s, in=259, out=165)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [IsPWO, isWf_insert]
```

**lean_error:** tail step 1/1 ('simp_rw [IsPWO, isWf_insert]'): unknown identifier 'isWf_insert'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 10.5s, verify 0.1s, in=259, out=317)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [insert_eq, isPWO_union, isPWO_singleton]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
inst✝¹ : Preorder α
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 16.7s, verify 0.1s, in=259, out=491)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa only [insert_eq] using isPWO_union_iff_of_left (isPWO_singleton : IsPWO {a})
```

**lean_error:** tail step 1/1 ('simpa only [insert_eq] using isPWO_union_iff_of_left (isPWO_singleton : IsPWO {a})'): unknown identifier 'isPWO_union_iff_of_left'

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 14.7s, verify 0.1s, in=722, out=598)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp only [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 30.9s, verify 0.1s, in=722, out=1298)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [singleton_union]
rw [isPWO_union]
rw [isPWO_singleton]
rw [true_and_iff]
```

**lean_error:** tail step 1/4 ('rw [singleton_union]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 33.0s, verify 0.3s, in=722, out=1387)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [←singleton_union]
rw [isPWO_union]
rw [isPWO_singleton]
rw [true_and_iff]
```

**lean_error:** tail step 3/4 ('rw [isPWO_singleton]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 93.1s, verify 0.1s, in=722, out=4210)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp_rw [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.9s, verify 0.1s, in=722, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, true_and_iff]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=722, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, true_and_iff]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 70.9s, verify 0.1s, in=722, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 70.9s, verify 1.2s, in=722, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 5.6s, verify 0.1s, in=722, out=160)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [← singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 6.5s, verify 0.1s, in=722, out=187)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp only [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 6.6s, verify 0.1s, in=722, out=189)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp only [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 6.7s, verify 0.1s, in=722, out=196)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp_rw [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 27.0s, verify 0.1s, in=1126, out=532)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 55.9s, verify 0.1s, in=1126, out=1650)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Set.singleton_union, Set.isPWO_union, Set.isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp only [Set.singleton_union, Set.isPWO_union, Set.isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 71.2s, verify 0.1s, in=1126, out=2703)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [singleton_union, isPWO_union]
apply and_iff_left
exact isPWO_singleton a
```

**lean_error:** tail step 1/3 ('rw [singleton_union, isPWO_union]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 153.4s, verify 0.1s, in=1126, out=6122)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [singleton_union, isPWO_union]
simp [isPWO_singleton]
rw [true_and_iff]
```

**lean_error:** tail step 1/3 ('rw [singleton_union, isPWO_union]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1126, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.5s, verify 0.1s, in=1126, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.6s, verify 0.1s, in=1126, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.7s, verify 0.1s, in=1126, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 11.6s, verify 0.1s, in=1126, out=180)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp only [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 12.2s, verify 0.1s, in=1126, out=190)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp only [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 12.7s, verify 0.1s, in=1126, out=171)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('rw [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 13.9s, verify 0.1s, in=1126, out=210)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp only [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 13.1s, verify 0.3s, in=1151, out=526)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [←singleton_union]
rw [isPWO_union]
rw [isPWO_singleton]
rw [true_and_iff]
```

**lean_error:** tail step 3/4 ('rw [isPWO_singleton]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 15.5s, verify 0.1s, in=1151, out=628)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [singleton_union]
rw [isPWO_union]
rw [isPWO_singleton]
rw [true_and_iff]
```

**lean_error:** tail step 1/4 ('rw [singleton_union]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 20.8s, verify 0.1s, in=1151, out=863)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Set.singleton_union, Set.isPWO_union, Set.isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [Set.singleton_union, Set.isPWO_union, Set.isPWO_singleton, true_and_iff]'): simp made no progress

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 74.9s, verify 0.1s, in=1151, out=3400)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [singleton_union],
rw [isPWO_union],
rw [isPWO_singleton],
rw [true_and_iff],
refl
```

**lean_error:** tail step 1/5 ('rw [singleton_union],'): <stdin>:1:20: expected end of input

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=1151, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, true_and_iff]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.3s, verify 0.1s, in=1151, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.4s, verify 0.1s, in=1151, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 5.8s, verify 0.1s, in=1151, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 6.4s, verify 0.1s, in=1151, out=181)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('rw [← singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 6.7s, verify 0.1s, in=1151, out=193)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp_rw [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 6.8s, verify 0.1s, in=1151, out=198)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('rw [← singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 9.7s, verify 0.1s, in=1151, out=292)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp only [singleton_union, isPWO_union, isPWO_singleton, true_and_iff]'): simp made no progress
