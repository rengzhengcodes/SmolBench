# Filter.frequently_sSup   (k=0, 1 tactics total)

file: `Mathlib/Order/Filter/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp only [Filter.Frequently, not_forall, eventually_sSup, exists_prop]
```

**True premises at k:** `Filter.Frequently`, `Classical.not_forall`, `Filter.eventually_sSup`, `exists_prop`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ · ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✓ ✘ ✓ ✓ | ✓ ✘ ✓ ✘ |
| `hint:3` | ✘ ✘ · · | ✘ ✓ ✘ ✓ | ✓ ✘ ✘ ✘ |
| `noise:3` | ✘ · ✘ ✘ | ✘ ✘ ✓ ✓ | ✓ ✓ ✓ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 48.0s, verify 0.1s, in=282, out=2093)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply sSup_mem
```

**lean_error:** tail step 1/1 ('apply sSup_mem'): unknown identifier 'sSup_mem'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 272.6s, verify 0.1s, in=282, out=11343)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw eventually_sSup
split
· rintro ⟨T, hT, hTp⟩
  rcases T with ⟨⟩ | T
  · rcases Classical.em (∃ f ∈ fs, True) with ⟨⟨f, hf⟩ | hn⟩
    · exact ⟨f, hf, eventually_of_forall _ _⟩
    · exfalso; apply hn; intro; apply False.elim
  · rcases T with ⟨f, ht⟩
    exact ⟨f, hT ht, eventually_mem_inf.mp hTp f ht⟩
· rintro ⟨f, hfs, hf⟩
  exact ⟨{f}, ⟨hfs⟩, hf⟩
```

**lean_error:** tail step 1/11 ('rw eventually_sSup'): <stdin>:1:3: expected '['

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 302.6s, verify 0.1s, in=282, out=12635)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Filter.frequently_iff_not_eventually, not_forall, Filter.eventually_sSup, exists_prop, Filter.frequently_iff_not_eventually]
```

**lean_error:** tail step 1/1 ('rw [Filter.frequently_iff_not_eventually, not_forall, Filter.eventually_sSup, exists_prop, Filter.frequently_iff_not_eventually]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 350.7s, verify 0.1s, in=282, out=14979)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· rintro ⟨⟩
  obtain ⟨S, S_in_sSup, x, x_in_S, p_x⟩ := frequently_eq_true_iff.1 h
  rw mem_sSup at S_in_sSup
  obtain ⟨T, Tfin, Tin, hT⟩ := S_in_sSup
  have inter_T : x ∈ ⋂ t ∈ T, t := by simpa using hT x_in_S
  obtain ⟨t, t_in_T, x_t⟩ := mem_Inter.1 inter_T (ne_empty_iff_exists_mem.1 Tfin)
  obtain ⟨f, f_in, t_in_f⟩ := mem_Union.1 (Tin t_in_T)
  use f
  use f_in
  apply frequently_eq_true_iff.mpr
  use t
  exact t_in_f
  use x
  exact ⟨x_t, p_x⟩
· rintro ⟨f, f_in, ⟨S, S_in_f, x, x_in_S, p_x⟩⟩
  use S
  apply mem_sSup_of_mem f_in S_in_f
  use x
  exact ⟨x_in_S, p_x⟩
```

**lean_error:** tail step 1/20 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=282, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [eventually, mem_iUnion]
```

**lean_error:** tail step 1/1 ('simp [eventually, mem_iUnion]'): unknown identifier 'eventually'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=282, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [mem_sSup_sets]
```

**lean_error:** tail step 1/1 ('simp [mem_sSup_sets]'): unknown identifier 'mem_sSup_sets'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 2.3s, verify 0.1s, in=282, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [frequently_iff, eventually_sSup, not_forall, exists_prop]
```

**final state (truncated):**
```
α : Type u
β : Type v
γ : Type w
δ : Type u_1
ι : Sort x
p : α → Prop
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.4s, verify 0.1s, in=282, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [mem_iInf, exists_prop, eventually_iff, eventually_sSup]
```

**lean_error:** tail step 1/1 ('simp only [mem_iInf, exists_prop, eventually_iff, eventually_sSup]'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 7.3s, verify 0.1s, in=282, out=245)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Set.iSup, eventually_iSup]
```

**lean_error:** tail step 1/1 ('rw [Set.iSup, eventually_iSup]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 10.3s, verify 0.1s, in=282, out=325)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [eventually_not, not_exists, forall₂_congr, eventually_sSup]
```

**lean_error:** tail step 1/1 ('simp only [eventually_not, not_exists, forall₂_congr, eventually_sSup]'): unknown identifier 'eventually_not'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 10.6s, verify 0.1s, in=282, out=331)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [exists_filter_iff, mem_sSup]
```

**lean_error:** tail step 1/1 ('simp only [exists_filter_iff, mem_sSup]'): unknown identifier 'exists_filter_iff'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 13.5s, verify 0.1s, in=282, out=430)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [eventually_iSup, Set.sSup_eq_iSup]
```

**lean_error:** tail step 1/1 ('simp [eventually_iSup, Set.sSup_eq_iSup]'): unknown constant 'Set.sSup_eq_iSup'

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 201.0s, verify 0.1s, in=932, out=8536)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Filter.Frequently, eventually_sSup]
rw [classical.not_forall]
rw [not_imp]
```

**lean_error:** tail step 1/3 ('simp [Filter.Frequently, eventually_sSup]'): tactic 'simp' failed, nested error:

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 212.2s, verify 0.1s, in=932, out=8951)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Filter.Frequently, eventually_sSup, ← Classical.not_forall]
```

**lean_error:** tail step 1/1 ('rw [Filter.Frequently, eventually_sSup, ← Classical.not_forall]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 213.1s, verify 0.3s, in=932, out=8985)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Filter.Frequently]
rw [eventually_sSup]
rw [← Classical.not_forall]
```

**lean_error:** tail step 3/3 ('rw [← Classical.not_forall]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 243.4s, verify 0.1s, in=932, out=10117)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Filter.Frequently, Filter.eventually_sSup, ← Classical.not_forall, exists_prop]
```

**lean_error:** tail step 1/1 ('rw [Filter.Frequently, Filter.eventually_sSup, ← Classical.not_forall, exists_prop]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.0s, verify 0.1s, in=932, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Filter.Frequently, eventually_sSup, Classical.not_forall, exists_prop, and_comm]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.0s, verify 0.1s, in=932, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Filter.Frequently, not_forall, eventually_sSup, exists_prop]
```

**lean_error:** tail step 1/1 ('simp [Filter.Frequently, not_forall, eventually_sSup, exists_prop]'): tactic 'simp' failed, nested error:

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.7s, verify 0.1s, in=932, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Filter.Frequently, not_and, eventually_sSup, not_forall, exists_prop, exists_and_left]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.7s, verify 0.1s, in=932, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Filter.Frequently, not_forall, eventually_sSup, not_not, exists_prop, exists_and_left]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 8.0s, verify 0.1s, in=932, out=268)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Filter.Frequently, Classical.not_forall, Filter.eventually_sSup, exists_prop]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 11.0s, verify 0.1s, in=932, out=346)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Filter.Frequently, Classical.not_forall, Filter.eventually_sSup, exists_prop]
```

**lean_error:** tail step 1/1 ('simp [Filter.Frequently, Classical.not_forall, Filter.eventually_sSup, exists_prop]'): tactic 'simp' failed, nested error:

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 11.2s, verify 0.1s, in=932, out=353)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Filter.Frequently, Classical.not_forall, Filter.eventually_sSup, exists_prop]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 12.9s, verify 0.1s, in=932, out=405)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [Filter.Frequently, Classical.not_forall, Filter.eventually_sSup, exists_prop]
```

**lean_error:** tail step 1/1 ('simp_rw [Filter.Frequently, Classical.not_forall, Filter.eventually_sSup, exists_prop]'): simp made no progress

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 248.5s, verify 0.1s, in=1514, out=3887)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.Frequently, eventually_sSup, classical.not_forall]
```

**lean_error:** tail step 1/1 ('rw [Filter.Frequently, eventually_sSup, classical.not_forall]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 260.7s, verify 0.3s, in=1514, out=8681)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Filter.Frequently]
rw [eventually_sSup]
rw [classical.not_forall]
rw [exists_prop]
```

**lean_error:** tail step 3/4 ('rw [classical.not_forall]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **incomplete**  (gen 273.3s, verify 0.1s, in=1514, out=6881)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.Frequently, eventually_sSup, Classical.not_forall]
```

**final state (truncated):**
```
α : Type u
β : Type v
γ : Type w
δ : Type u_1
ι : Sort x
p : α → Prop
...
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **incomplete**  (gen 344.9s, verify 0.1s, in=1514, out=6126)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.Frequently, eventually_sSup, Classical.not_forall]
```

**final state (truncated):**
```
α : Type u
β : Type v
γ : Type w
δ : Type u_1
ι : Sort x
p : α → Prop
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.8s, verify 0.1s, in=1514, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Filter.Frequently, not_forall, eventually_sSup, exists_prop]
```

**lean_error:** tail step 1/1 ('simp [Filter.Frequently, not_forall, eventually_sSup, exists_prop]'): tactic 'simp' failed, nested error:

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.9s, verify 0.1s, in=1514, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Filter.Frequently, eventually_sSup, Classical.not_forall, exists_prop, and_comm]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 3.0s, verify 0.1s, in=1514, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Filter.Frequently, not_forall, eventually_sSup, exists_prop]
```

**lean_error:** tail step 1/1 ('simp [Filter.Frequently, not_forall, eventually_sSup, exists_prop]'): tactic 'simp' failed, nested error:

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 3.1s, verify 0.1s, in=1514, out=26)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Filter.Frequently, not_and, not_forall, eventually_sSup, exists_prop]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 20.2s, verify 0.1s, in=1514, out=315)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Filter.Frequently, Classical.not_forall, Filter.eventually_sSup, exists_prop]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 23.4s, verify 0.1s, in=1514, out=516)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [Filter.Frequently, Classical.not_forall, Filter.eventually_sSup, exists_prop]
```

**lean_error:** tail step 1/1 ('simp_rw [Filter.Frequently, Classical.not_forall, Filter.eventually_sSup, exists_prop]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 25.7s, verify 0.1s, in=1514, out=612)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.Frequently, Filter.Frequently, eventually_sSup, exists_prop, Classical.not_forall]
```

**lean_error:** tail step 1/1 ('rw [Filter.Frequently, Filter.Frequently, eventually_sSup, exists_prop, Classical.not_forall]'): failed to rewrite using equation theorems for 'Filter.Frequently'

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 28.4s, verify 0.1s, in=1514, out=693)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.Frequently, Classical.not_forall, exists_prop, Classical.not_forall]
```

**lean_error:** tail step 1/1 ('rw [Filter.Frequently, Classical.not_forall, exists_prop, Classical.not_forall]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 102.3s, verify 0.1s, in=1539, out=4481)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.Frequently, Filter.eventually_sSup, Classical.not_forall, exists_prop]
```

**lean_error:** tail step 1/1 ('rw [Filter.Frequently, Filter.eventually_sSup, Classical.not_forall, exists_prop]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **incomplete**  (gen 146.7s, verify 0.1s, in=1539, out=6433)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.Frequently, eventually_sSup, Classical.not_forall]
```

**final state (truncated):**
```
α : Type u
β : Type v
γ : Type w
δ : Type u_1
ι : Sort x
p : α → Prop
...
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 235.8s, verify 0.1s, in=1539, out=9808)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.Frequently, eventually_sSup, Classical.not_forall, not_imp]
```

**lean_error:** tail step 1/1 ('rw [Filter.Frequently, eventually_sSup, Classical.not_forall, not_imp]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 272.2s, verify 0.1s, in=1539, out=11327)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.Frequently, eventually_sSup, ← Classical.not_forall]
```

**lean_error:** tail step 1/1 ('rw [Filter.Frequently, eventually_sSup, ← Classical.not_forall]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.1s, verify 0.1s, in=1539, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Filter.Frequently, not_forall, eventually_sSup, exists_prop]
```

**lean_error:** tail step 1/1 ('simp [Filter.Frequently, not_forall, eventually_sSup, exists_prop]'): tactic 'simp' failed, nested error:

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.4s, verify 0.1s, in=1539, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Filter.Frequently, eventually_sSup, not_forall, exists_prop]
```

**lean_error:** tail step 1/1 ('simp [Filter.Frequently, eventually_sSup, not_forall, exists_prop]'): tactic 'simp' failed, nested error:

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.5s, verify 0.1s, in=1539, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Filter.Frequently, not_and, not_forall, eventually_sSup, exists_prop]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.6s, verify 0.1s, in=1539, out=28)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Filter.Frequently, eventually_sSup, Classical.not_forall, exists_prop, exists_and_left]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 10.5s, verify 0.1s, in=1539, out=330)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Filter.Frequently, Classical.not_forall, Filter.eventually_sSup, exists_prop]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 13.1s, verify 0.1s, in=1539, out=417)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Filter.Frequently, Classical.not_forall, Filter.eventually_sSup, exists_prop]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 14.6s, verify 0.1s, in=1539, out=456)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Filter.Frequently, Classical.not_forall, Filter.eventually_sSup, exists_prop]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 16.1s, verify 0.1s, in=1539, out=503)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Filter.Frequently, Classical.not_forall, eventually_sSup, exists_prop]
```

**lean_error:** tail step 1/1 ('simp [Filter.Frequently, Classical.not_forall, eventually_sSup, exists_prop]'): tactic 'simp' failed, nested error:
