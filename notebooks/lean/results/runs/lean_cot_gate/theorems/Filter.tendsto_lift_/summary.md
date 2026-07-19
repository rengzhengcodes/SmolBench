# Filter.tendsto_lift'   (k=0, 1 tactics total)

file: `Mathlib/Order/Filter/Lift.lean`  

**Ground-truth tail (from k):**
```lean
simp only [Filter.lift', tendsto_lift, tendsto_principal, comp]
```

**True premises at k:** `Filter.lift'`, `Filter.tendsto_lift`, `Filter.tendsto_principal`, `Function.comp`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✓ · ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✘ ✓ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | · ✓ ✓ ✓ | ✓ ✓ ✓ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ · | ✘ ✘ ✘ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 91.6s, verify 0.1s, in=296, out=3960)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
tactic.apply (tendsto_lift'_iff : _)
```

**lean_error:** tail step 1/1 ("tactic.apply (tendsto_lift'_iff : _)"): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 148.1s, verify 0.1s, in=296, out=6267)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split,
  · intros h s hs,
    exact h (h s) (Filter.mem_lift'_of_mem hs),
  · intro H,
    apply Filter.tendsto_def.2,
    intros U HU,
    obtain ⟨s, hs, Hs⟩ := Filter.mem_lift'_iff.1 HU,
    apply l.mono (preimage_mono Hs) (H s hs)
```

**lean_error:** tail step 1/8 ('split,'): <stdin>:1:5: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 177.5s, verify 0.1s, in=296, out=7434)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split,
{ intros Ht s hs,
  exact Ht (Filter.lift'_sets.2 hs) },
{ intros Ht,
  apply tendsto_def.2,
  intros U HU,
  rcases Filter.lift'_sets.1 HU with ⟨s, hs, hsub⟩,
  exact l.upward (Ht s hs) (preimage_mono hsub) }
```

**lean_error:** tail step 1/8 ('split,'): <stdin>:1:5: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 205.1s, verify 0.1s, in=296, out=8519)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
intro H s hs
apply H
exact Filter.mem_lift'_sets.mpr ⟨s, hs, rfl.le⟩
intro H
apply Filter.tendsto_def.mpr
intros u hu
obtain ⟨s, hs, h_sub⟩ := Filter.mem_lift'_sets.mp hu
exact Filter.eventually_mono (H s hs) h_sub
```

**lean_error:** tail step 1/9 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=296, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [tendsto_lift'_gen]
```

**lean_error:** tail step 1/1 ("simp [tendsto_lift'_gen]"): unknown identifier 'tendsto_lift'_gen'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.3s, verify 1.4s, in=296, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [tendsto_def, mem_lift'_sets]
```

**lean_error:** tail step 1/1 ("simp [tendsto_def, mem_lift'_sets]"): unknown identifier 'mem_lift'_sets'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 3.7s, verify 0.1s, in=296, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [tendsto_def, mem_lift'_sets, eventually_map]
```

**lean_error:** tail step 1/1 ("simp only [tendsto_def, mem_lift'_sets, eventually_map]"): unknown identifier 'mem_lift'_sets'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 3.7s, verify 0.1s, in=296, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Filter.lift'_tendsto_iff, tendsto_iff_eventually]
```

**lean_error:** tail step 1/1 ("simp only [Filter.lift'_tendsto_iff, tendsto_iff_eventually]"): unknown constant 'Filter.lift'_tendsto_iff'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 8.4s, verify 0.1s, in=296, out=236)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [tendsto_lift'_iff]
```

**lean_error:** tail step 1/1 ("simp [tendsto_lift'_iff]"): unknown identifier 'tendsto_lift'_iff'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 12.4s, verify 0.1s, in=296, out=339)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Tendsto_def, mem_lift'_sets]
```

**lean_error:** tail step 1/1 ("simp only [Tendsto_def, mem_lift'_sets]"): unknown identifier 'Tendsto_def'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 12.8s, verify 0.1s, in=296, out=352)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Tendsto, Filter.lift'_le_iff, preimage_principal, principal_le_iff]
```

**lean_error:** tail step 1/1 ("rw [Tendsto, Filter.lift'_le_iff, preimage_principal, principal_le_iff]"): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 15.0s, verify 0.1s, in=296, out=423)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [tendsto_lift'_iff]
```

**lean_error:** tail step 1/1 ("simp [tendsto_lift'_iff]"): unknown identifier 'tendsto_lift'_iff'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 47.3s, verify 0.1s, in=1211, out=2082)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Filter.lift', tendsto_lift, tendsto_principal]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **incomplete**  (gen 53.9s, verify 0.1s, in=1211, out=2353)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Filter.lift', tendsto_lift, tendsto_principal]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
f f₁ f₂ : Filter α
h h₁ h₂ : Set α → Set β
...
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 100.8s, verify 0.1s, in=1211, out=4331)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Filter.lift', tendsto_lift, tendsto_principal]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 112.0s, verify 0.2s, in=1211, out=4770)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Filter.lift', tendsto_lift]
simp [tendsto_principal]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.1s, verify 0.1s, in=1211, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Filter.lift', tendsto_lift, tendsto_principal]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.7s, verify 0.7s, in=1211, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Filter.lift', tendsto_lift, tendsto_principal]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 3.8s, verify 0.1s, in=1211, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Filter.lift', tendsto_lift, Function.comp_apply, tendsto_principal]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 3.9s, verify 0.1s, in=1211, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Filter.lift', tendsto_lift, tendsto_principal, Function.comp_apply]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 10.0s, verify 0.1s, in=1211, out=268)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Filter.lift', Function.comp_apply, Filter.tendsto_lift, Filter.tendsto_principal]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 11.1s, verify 0.1s, in=1211, out=302)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [lift', tendsto_lift, tendsto_principal, Function.comp]
```

**lean_error:** tail step 1/1 ("simp only [lift', tendsto_lift, tendsto_principal, Function.comp]"): unknown identifier 'lift''

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 12.7s, verify 0.1s, in=1211, out=347)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Filter.lift', Filter.tendsto_lift, Filter.tendsto_principal, Function.comp]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 13.3s, verify 0.1s, in=1211, out=371)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [lift', tendsto_lift, tendsto_principal, Function.comp]
```

**lean_error:** tail step 1/1 ("simp only [lift', tendsto_lift, tendsto_principal, Function.comp]"): unknown identifier 'lift''

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 159.6s, verify 0.1s, in=3868, out=5463)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw tendsto_lift
apply forall_congr
intro s
apply tendsto_principal
```

**lean_error:** tail step 1/4 ('rw tendsto_lift'): <stdin>:1:3: expected '['

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 167.7s, verify 0.1s, in=3868, out=3470)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.tendsto_lift], simp
```

**lean_error:** tail step 1/1 ('rw [Filter.tendsto_lift], simp'): <stdin>:1:24: expected end of input

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 170.4s, verify 0.1s, in=3868, out=5066)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.tendsto_lift]
apply forall_congr
intro s
apply Filter.tendsto_principal
```

**lean_error:** tail step 1/4 ('rw [Filter.tendsto_lift]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 197.2s, verify 0.2s, in=3868, out=5849)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.lift', tendsto_lift]
simp only [tendsto_principal]
```

**lean_error:** tail step 2/2 ('simp only [tendsto_principal]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 3.9s, verify 0.1s, in=3868, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Filter.lift', tendsto_lift, tendsto_principal]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
f f₁ f₂ : Filter α
h h₁ h₂ : Set α → Set β
...
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 4.1s, verify 0.1s, in=3868, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Filter.lift', tendsto_lift, Function.comp_apply, tendsto_principal]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 4.2s, verify 0.1s, in=3868, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Filter.lift', tendsto_lift, tendsto_principal]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 4.4s, verify 0.1s, in=3868, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Filter.lift', tendsto_lift, tendsto_principal]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 18.1s, verify 0.1s, in=3868, out=251)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Filter.lift', Filter.tendsto_lift, Function.comp, Filter.tendsto_principal]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 19.0s, verify 0.1s, in=3868, out=320)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Filter.lift', Filter.tendsto_lift, Function.comp, Filter.tendsto_principal]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 20.3s, verify 0.1s, in=3868, out=336)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Filter.lift', Filter.tendsto_lift, Function.comp, Filter.tendsto_principal]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 21.5s, verify 0.1s, in=3868, out=365)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [lift', tendsto_lift, Function.comp_apply, tendsto_principal]
```

**lean_error:** tail step 1/1 ("simp_rw [lift', tendsto_lift, Function.comp_apply, tendsto_principal]"): unknown identifier 'lift''

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 27.3s, verify 0.1s, in=3895, out=1230)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.tendsto_lift, Filter.tendsto_principal]
```

**lean_error:** tail step 1/1 ('rw [Filter.tendsto_lift, Filter.tendsto_principal]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 82.0s, verify 0.1s, in=3895, out=3555)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw tendsto_lift
simp [tendsto_principal]
```

**lean_error:** tail step 1/2 ('rw tendsto_lift'): <stdin>:1:3: expected '['

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 88.7s, verify 0.1s, in=3895, out=3840)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw Filter.lift'
rw tendsto_lift
simp only [tendsto_principal]
```

**lean_error:** tail step 1/3 ("rw Filter.lift'"): <stdin>:1:3: expected '['

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 134.3s, verify 0.1s, in=3895, out=5628)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw tendesto_lift
simp only [tendesto_principal]
```

**lean_error:** tail step 1/2 ('rw tendesto_lift'): <stdin>:1:3: expected '['

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 3.4s, verify 0.1s, in=3895, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Filter.lift', tendsto_lift, tendsto_principal]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 3.5s, verify 0.1s, in=3895, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Filter.lift', tendsto_lift, tendsto_principal]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 3.6s, verify 0.1s, in=3895, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Filter.lift', tendsto_lift, Function.comp_apply, tendsto_principal]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 4.0s, verify 0.1s, in=3895, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Filter.lift', tendsto_lift, tendsto_principal]
```

**final state (truncated):**
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
f f₁ f₂ : Filter α
h h₁ h₂ : Set α → Set β
...
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 10.3s, verify 0.1s, in=3895, out=274)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Filter.lift', Filter.tendsto_lift, Function.comp_apply, Filter.tendsto_principal,
  forall_prop_of_true]
```

**lean_error:** tail step 1/2 ("simp only [Filter.lift', Filter.tendsto_lift, Function.comp_apply, Filter.tendsto_principal,"): <stdin>:1:92: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 10.5s, verify 0.1s, in=3895, out=281)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [lift', tendsto_lift, tendsto_principal, Function.comp]
```

**lean_error:** tail step 1/1 ("simp only [lift', tendsto_lift, tendsto_principal, Function.comp]"): unknown identifier 'lift''

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 11.3s, verify 0.1s, in=3895, out=306)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [lift', tendsto_lift, tendsto_principal, comp_apply, forall_mem_image_iff]
```

**lean_error:** tail step 1/1 ("simp only [lift', tendsto_lift, tendsto_principal, comp_apply, forall_mem_image_iff]"): unknown identifier 'lift''

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 12.7s, verify 0.1s, in=3895, out=349)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Filter.lift', Filter.tendsto_lift, Filter.tendsto_principal, Function.comp]
```
