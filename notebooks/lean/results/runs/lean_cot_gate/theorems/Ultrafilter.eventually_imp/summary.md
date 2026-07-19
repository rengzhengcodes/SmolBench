# Ultrafilter.eventually_imp   (k=0, 1 tactics total)

file: `Mathlib/Order/Filter/Ultrafilter.lean`  

**Ground-truth tail (from k):**
```lean
simp only [imp_iff_not_or, eventually_or, eventually_not]
```

**True premises at k:** `imp_iff_not_or`, `Ultrafilter.eventually_or`, `Ultrafilter.eventually_not`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✓ ✓ | ✘ ✘ ✓ ✓ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✓ ✘ ✘ ✓ | ✓ ✘ ✓ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 110.2s, verify 0.1s, in=303, out=4196)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· intro h hp
  apply mem_of_superset (inter_mem h hp) <|
    rintro x ⟨himp, hpx⟩
    exact himp hpx
· intro h_rh
  by_contra h_contra
  rw [eventually_not, not_mem] at h_contra
  have hp := mem_of_superset h_contra fun x h => h.1
  have hq := h_rh hp
  have h_nq := mem_of_superset h_contra fun x h => h.2
  have : {x | q x} ∩ {x | ¬q x} = ∅ := by ext; simp [and_self, not_true]
  rw [this] at h_nq
  exact not_mem_empty _ (inter_mem hq h_nq)
```

**lean_error:** tail step 1/14 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 132.9s, verify 0.1s, in=303, out=5098)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· intro h hp
  exact f.superset_mem (f.inter_mem hp h) (λ x ⟨hx, _⟩, h hx)
· intro h
  by_contra' H
  have : {x | p x ∧ ¬q x} ∈ f := f.compl_mem_iff_not_mem.mpr H
  have hp : {x | p x} ∈ f := f.superset_mem this (λ x h, h.1)
  have hq : {x | q x} ∈ f := h hp
  have hnq : {x | ¬q x} ∈ f := f.superset_mem this (λ x h, h.2)
  exact f.ne_bot.not_mem_empty (f.inter_mem hq hnq)
```

**lean_error:** tail step 1/10 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 202.5s, verify 0.1s, in=303, out=8089)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split;
[ intros h_imp h_p,
  apply mem_sets_of_superset (inter_mem h_imp h_p) (λ x ⟨hp, h⟩, h hp)
| intro H,
  by_contra h_contra,
  push_neg at h_contra,
  have s_mem : {x | p x ∧ ¬q x} ∈ f := h_contra,
  have p_mem : {x | p x} ∈ f := mem_sets_of_superset s_mem (λ x h, h.1),
  have q_mem := H p_mem,
  have not_q_mem : {x | ¬q x} ∈ f := mem_sets_of_superset s_mem (λ x h, h.2),
  exact absurd (inter_mem q_mem not_q_mem) (empty_not_mem f) ]
```

**lean_error:** tail step 1/11 ('split;'): <stdin>:1:5: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 215.9s, verify 0.1s, in=303, out=8627)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split,
{ intros h hp,
  apply eventually.mono (eventually_and h hp),
  intros x h_pq h_p,
  exact h_pq h_p },
{ intro h_imp,
  by_contra h_contra,
  rw not_eventually_iff at h_contra,
  have s_mem : {x | p x ∧ ¬ q x} ∈ f := h_contra,
  have hp := eventually_of_superset s_mem (λ x h, h.left),
  have hq := h_imp hp,
  have : {x | p x ∧ ¬ q x} ∩ {x | q x} = ∅ := by ext; simp; tauto,
  have empty_mem := filter.inter_sets s_mem hq,
  rwa this at empty_mem,
  exact filter.empty_not_mem empty_mem }
```

**lean_error:** tail step 1/15 ('split,'): <stdin>:1:5: expected end of input

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=303, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.1s, verify 0.1s, in=303, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [eventually_imp_distrib_left]
```

**lean_error:** tail step 1/1 ('simp [eventually_imp_distrib_left]'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.2s, verify 0.1s, in=303, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [mem_pure, Filter.eventually, mem_principal]
```

**lean_error:** tail step 1/1 ('simp only [mem_pure, Filter.eventually, mem_principal]'): unknown constant 'Filter.eventually'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 4.9s, verify 0.8s, in=303, out=33)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [mem_pure, not_mem_empty, ultrafilter_nmem_iff, imp_iff_not_or, eventually_or, not_imp]
```

**lean_error:** tail step 1/1 ('simp only [mem_pure, not_mem_empty, ultrafilter_nmem_iff, imp_iff_not_or, eventually_or, not_imp]'): unknown identifier 'ultrafilter_nmem_iff'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 4.9s, verify 0.1s, in=303, out=149)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact eventually.imp_iff
```

**lean_error:** tail step 1/1 ('exact eventually.imp_iff'): unknown identifier 'eventually.imp_iff'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 6.0s, verify 0.1s, in=303, out=182)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact eventually.mono
```

**lean_error:** tail step 1/1 ('exact eventually.mono'): unknown identifier 'eventually.mono'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 11.1s, verify 0.1s, in=303, out=359)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [eventually.mono, not_eventually]
```

**lean_error:** tail step 1/1 ('simp [eventually.mono, not_eventually]'): unknown identifier 'eventually.mono'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 16.2s, verify 0.1s, in=303, out=551)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact eventually.mp
```

**lean_error:** tail step 1/1 ('exact eventually.mp'): unknown identifier 'eventually.mp'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 103.0s, verify 0.1s, in=716, out=3909)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw imp_iff_not_or
rw eventually_or
rw eventually_not
rw [← imp_iff_not_or]
```

**lean_error:** tail step 1/4 ('rw imp_iff_not_or'): <stdin>:1:3: expected '['

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 108.5s, verify 0.1s, in=716, out=4123)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [imp_iff_not_or, eventually_or, eventually_not, ←imp_iff_not_or]
```

**lean_error:** tail step 1/1 ('rw [imp_iff_not_or, eventually_or, eventually_not, ←imp_iff_not_or]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 208.6s, verify 0.1s, in=716, out=8344)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw imp_iff_not_or
rw eventually_or
rw eventually_not
rw imp_iff_not_or
```

**lean_error:** tail step 1/4 ('rw imp_iff_not_or'): <stdin>:1:3: expected '['

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 216.3s, verify 0.1s, in=716, out=8644)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [imp_iff_not_or, eventually_or, eventually_not, ← imp_iff_not_or]
```

**lean_error:** tail step 1/1 ('rw [imp_iff_not_or, eventually_or, eventually_not, ← imp_iff_not_or]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.3s, in=716, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [imp_iff_not_or, eventually_or, eventually_not]
```

**lean_error:** tail step 1/1 ('simp [imp_iff_not_or, eventually_or, eventually_not]'): tactic 'simp' failed, nested error:

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.9s, verify 0.3s, in=716, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [imp_iff_not_or, eventually_or, eventually_not]
```

**lean_error:** tail step 1/1 ('simp [imp_iff_not_or, eventually_or, eventually_not]'): tactic 'simp' failed, nested error:

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.3s, verify 0.1s, in=716, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [imp_iff_not_or, eventually_or, eventually_not]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.5s, verify 0.9s, in=716, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [imp_iff_not_or, eventually_or, eventually_not]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 8.4s, verify 0.1s, in=716, out=264)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [imp_iff_not_or, eventually_or, eventually_not, imp_iff_not_or, or_comm]
```

**lean_error:** tail step 1/1 ('simp_rw [imp_iff_not_or, eventually_or, eventually_not, imp_iff_not_or, or_comm]'): no goals to be solved

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 10.2s, verify 0.1s, in=716, out=323)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not, imp_iff_not_or]
```

**lean_error:** tail step 1/1 ('rw [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not, imp_iff_not_or]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 10.9s, verify 0.1s, in=716, out=352)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 11.4s, verify 0.1s, in=716, out=368)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 153.1s, verify 0.1s, in=959, out=1987)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [imp_iff_not_or, eventually_or, eventually_not]
```

**lean_error:** tail step 1/1 ('rw [imp_iff_not_or, eventually_or, eventually_not]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 206.9s, verify 0.1s, in=959, out=3665)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]
```

**lean_error:** tail step 1/1 ('rw [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 291.0s, verify 0.1s, in=959, out=7873)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw imp_iff_not_or
rw eventually_or
rw eventually_not
rw imp_iff_not_or
```

**lean_error:** tail step 1/4 ('rw imp_iff_not_or'): <stdin>:1:3: expected '['

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 347.0s, verify 0.1s, in=959, out=10235)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw imp_iff_not_or
rw eventually_or
rw eventually_not
exact imp_iff_not_or (∀ᶠ x in f, p x) (∀ᶠ x in f, q x)
```

**lean_error:** tail step 1/4 ('rw imp_iff_not_or'): <stdin>:1:3: expected '['

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 4.4s, verify 0.5s, in=959, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [imp_iff_not_or, eventually_or, eventually_not]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 5.7s, verify 0.8s, in=959, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [imp_iff_not_or, eventually_or, eventually_not]
```

**lean_error:** tail step 1/1 ('simp [imp_iff_not_or, eventually_or, eventually_not]'): tactic 'simp' failed, nested error:

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 6.5s, verify 0.3s, in=959, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [imp_iff_not_or, eventually_or, eventually_not]
```

**lean_error:** tail step 1/1 ('simp [imp_iff_not_or, eventually_or, eventually_not]'): tactic 'simp' failed, nested error:

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 6.8s, verify 0.1s, in=959, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [imp_iff_not_or, eventually_or, eventually_not]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 15.2s, verify 0.1s, in=959, out=247)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [imp_iff_not_or, eventually_or, eventually_not]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 15.3s, verify 0.1s, in=959, out=367)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [imp_iff_not_or, eventually_or, eventually_not, ← imp_iff_not_or]
```

**lean_error:** tail step 1/1 ('rw [imp_iff_not_or, eventually_or, eventually_not, ← imp_iff_not_or]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 16.9s, verify 0.1s, in=959, out=387)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 18.2s, verify 0.1s, in=959, out=315)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]
```

**lean_error:** tail step 1/1 ('rw [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 120.4s, verify 0.1s, in=985, out=4271)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw imp_iff_not_or
rw eventually_or
rw eventually_not
rw ← imp_iff_not_or
```

**lean_error:** tail step 1/4 ('rw imp_iff_not_or'): <stdin>:1:3: expected '['

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 161.3s, verify 0.1s, in=985, out=6260)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw eventually_congr (λ x, imp_iff_not_or)
rw eventually_or
rw eventually_not
rw imp_iff_not_or
```

**lean_error:** tail step 1/4 ('rw eventually_congr (λ x, imp_iff_not_or)'): <stdin>:1:3: expected '['

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 208.2s, verify 0.1s, in=985, out=8328)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw imp_iff_not_or
rw eventually_or
rw eventually_not
```

**lean_error:** tail step 1/3 ('rw imp_iff_not_or'): <stdin>:1:3: expected '['

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 209.0s, verify 0.1s, in=985, out=8357)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw imp_iff_not_or
rw eventually_or
rw eventually_not
refl
```

**lean_error:** tail step 1/4 ('rw imp_iff_not_or'): <stdin>:1:3: expected '['

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.5s, verify 0.3s, in=985, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [imp_iff_not_or, eventually_or, eventually_not]
```

**lean_error:** tail step 1/1 ('simp [imp_iff_not_or, eventually_or, eventually_not]'): tactic 'simp' failed, nested error:

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.8s, verify 0.1s, in=985, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [imp_iff_not_or, eventually_or, eventually_not]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.8s, verify 0.1s, in=985, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [imp_iff_not_or, eventually_or, eventually_not]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 3.5s, verify 0.9s, in=985, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [imp_iff_not_or, eventually_or, eventually_not]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 9.7s, verify 0.1s, in=985, out=308)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 10.8s, verify 0.1s, in=985, out=348)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 11.5s, verify 0.1s, in=985, out=370)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 12.3s, verify 0.1s, in=985, out=405)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [imp_iff_not_or, Ultrafilter.eventually_or, Ultrafilter.eventually_not]
```
