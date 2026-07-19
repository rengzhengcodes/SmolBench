# antitone_dual_iff   (k=0, 1 tactics total)

file: `Mathlib/Order/Monotone/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

**True premises at k:** `antitone_toDual_comp_iff`, `monotone_comp_ofDual_iff`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✓ ✘ · ✘ |
| `hint:2` | ✓ ✓ ✘ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✘ |
| `hint:3` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ · ✓ |
| `noise:3` | ✓ ✘ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 299.4s, verify 0.3s, in=283, out=11492)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Antitone, Antitone]
apply forall_congr
intro x
apply forall_congr
intro y
rw [← ofDual_le_ofDual_iff]
rw [ge_iff_le]
```

**lean_error:** tail step 2/7 ('apply forall_congr'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 300.9s, verify 0.1s, in=283, out=11555)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Antitone, Antitone, comp_app, Dual.le_iff_ge, toDual_apply, ofDual_apply]
```

**lean_error:** tail step 1/1 ('rw [Antitone, Antitone, comp_app, Dual.le_iff_ge, toDual_apply, ofDual_apply]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 302.5s, verify 0.1s, in=283, out=11623)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· intro H x y h; exact H h
· intro H x y h; exact H h
```

**lean_error:** tail step 1/3 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 333.1s, verify 0.1s, in=283, out=12953)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
intros hf
apply Antitone.intro
intros x y h
apply hf (Dual.le_iff_le.mp h)
intros hg
apply Antitone.intro
intros a b h
apply hg (Dual.le_iff_le.mpr h)
```

**lean_error:** tail step 1/8 ('intros hf'): tactic 'introN' failed, insufficient number of binders

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.5s, verify 0.1s, in=283, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Antitone, Monotone.comp]
```

**lean_error:** tail step 1/1 ('simp [Antitone, Monotone.comp]'): invalid 'simp', proposition expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=283, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [antitone_iff_monotone_dual, Function.comp, toDual_comp_ofDual]
```

**lean_error:** tail step 1/1 ('simp only [antitone_iff_monotone_dual, Function.comp, toDual_comp_ofDual]'): unknown identifier 'antitone_iff_monotone_dual'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 71.1s, verify 0.1s, in=283, out=28)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Antitone, Dual.ofDual_lt_ofDual, toDual_lt_toDual, Function.comp_apply]
```

**lean_error:** tail step 1/1 ('simp only [Antitone, Dual.ofDual_lt_ofDual, toDual_lt_toDual, Function.comp_apply]'): unknown identifier 'Dual.ofDual_lt_ofDual'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 72.4s, verify 0.1s, in=283, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Antitone, monotone_comp_iff]
```

**lean_error:** tail step 1/1 ('simp [Antitone, monotone_comp_iff]'): unknown identifier 'monotone_comp_iff'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 8.1s, verify 0.1s, in=283, out=233)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 9.7s, verify 0.1s, in=283, out=286)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [antitone_comp_ofDual_iff, monotone_toDual_iff]
```

**lean_error:** tail step 1/1 ('rw [antitone_comp_ofDual_iff, monotone_toDual_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 10.5s, verify 0.2s, in=283, out=303)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Antitone]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u
β : Type v
γ : Type w
δ : Type u_2
π : ι → Type u_3
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 13.2s, verify 0.1s, in=283, out=390)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [antitone_comp_iff, antitone_toDual_iff]
```

**lean_error:** tail step 1/1 ('simp only [antitone_comp_iff, antitone_toDual_iff]'): unknown identifier 'antitone_comp_iff'

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 35.1s, verify 0.1s, in=600, out=1261)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 55.8s, verify 0.1s, in=600, out=2066)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 151.8s, verify 0.1s, in=600, out=5579)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw antitone_toDual_comp_iff
rw monotone_comp_ofDual_iff
rfl
```

**lean_error:** tail step 1/3 ('rw antitone_toDual_comp_iff'): <stdin>:1:3: expected '['

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 153.9s, verify 1.0s, in=600, out=5663)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact antitone_toDual_comp_iff.trans monotone_comp_ofDual_iff
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.3s, verify 0.1s, in=600, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 0.7s, verify 0.1s, in=600, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.8s, verify 0.1s, in=600, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.9s, verify 0.1s, in=600, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 7.5s, verify 0.1s, in=600, out=217)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 9.0s, verify 0.1s, in=600, out=262)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 9.8s, verify 0.1s, in=600, out=286)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using (antitone_toDual_comp_iff.trans monotone_comp_ofDual_iff)
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 22.5s, verify 0.6s, in=600, out=762)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Function.comp_assoc, antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

**lean_error:** tail step 1/1 ('simp only [Function.comp_assoc, antitone_toDual_comp_iff, monotone_comp_ofDual_iff]'): unknown identifier 'Function.comp_assoc'

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 89.3s, verify 0.1s, in=933, out=1290)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 158.9s, verify 0.1s, in=933, out=2969)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 232.7s, verify 0.1s, in=933, out=7356)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Iff.trans antitone_toDual_comp_iff monotone_comp_ofDual_iff
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 245.4s, verify 0.1s, in=933, out=8186)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=933, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.1s, verify 0.1s, in=933, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.2s, verify 0.1s, in=933, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.2s, verify 0.1s, in=933, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 15.5s, verify 0.1s, in=933, out=245)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 15.9s, verify 0.1s, in=933, out=243)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **incomplete**  (gen 16.4s, verify 0.1s, in=933, out=234)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Function.comp, antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u
β : Type v
γ : Type w
δ : Type u_2
π : ι → Type u_3
...
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 20.0s, verify 0.1s, in=933, out=427)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 25.6s, verify 0.1s, in=958, out=930)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 76.5s, verify 0.1s, in=958, out=2870)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw antitone_toDual_comp_iff
rw monotone_comp_ofDual_iff
```

**lean_error:** tail step 1/2 ('rw antitone_toDual_comp_iff'): <stdin>:1:3: expected '['

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 86.0s, verify 0.1s, in=958, out=3232)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 188.4s, verify 0.1s, in=958, out=6986)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.8s, verify 0.1s, in=958, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.0s, verify 0.1s, in=958, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.6s, verify 0.1s, in=958, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 70.5s, verify 0.1s, in=958, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 7.5s, verify 0.1s, in=958, out=218)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 9.3s, verify 0.1s, in=958, out=273)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Function.comp_assoc, antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

**lean_error:** tail step 1/1 ('rw [Function.comp_assoc, antitone_toDual_comp_iff, monotone_comp_ofDual_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 12.5s, verify 0.1s, in=958, out=365)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Function.comp_assoc, antitone_toDual_comp_iff, monotone_comp_ofDual_iff]
```

**lean_error:** tail step 1/1 ('rw [Function.comp_assoc, antitone_toDual_comp_iff, monotone_comp_ofDual_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 13.1s, verify 0.1s, in=958, out=385)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [← antitone_toDual_comp_iff, ← monotone_comp_ofDual_iff]
```

**lean_error:** tail step 1/1 ('simp_rw [← antitone_toDual_comp_iff, ← monotone_comp_ofDual_iff]'): simp made no progress
