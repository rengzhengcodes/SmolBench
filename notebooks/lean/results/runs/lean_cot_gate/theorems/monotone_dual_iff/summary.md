# monotone_dual_iff   (k=0, 1 tactics total)

file: `Mathlib/Order/Monotone/Basic.lean`  

**Ground-truth tail (from k):**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

**True premises at k:** `monotone_toDual_comp_iff`, `antitone_comp_ofDual_iff`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✓ ✘ ✘ ✘ | ✓ · ✘ ✘ | ✘ ✓ ✘ ✘ |
| `hint:2` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `hint:3` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |
| `noise:3` | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ | ✓ ✘ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 163.2s, verify 0.1s, in=287, out=7178)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 243.1s, verify 0.1s, in=287, out=11162)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· rintro H a b h
  exact H (toDual b) (toDual a) (by simp [h])
· rintro H x y h
  exact H (ofDual y) (ofDual x) h
```

**lean_error:** tail step 1/5 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 273.4s, verify 0.2s, in=287, out=12611)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Iff.intro
· intro h
  apply Monotone.intro
  intros a b hab
  exact h b a hab
· intro h
  apply Monotone.intro
  intros x y hxy
  exact h y x hxy
```

**lean_error:** tail step 2/9 ('· intro h'): unsolved goals

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 317.9s, verify 0.1s, in=287, out=14711)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Function.monotone_comp_iff (OrderIso.ofDual α).symm, Function.monotone_comp_iff (OrderIso.toDual β)]
```

**lean_error:** tail step 1/1 ('rw [Function.monotone_comp_iff (OrderIso.ofDual α).symm, Function.monotone_comp_iff (OrderIso.toDual β)]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=287, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 0.9s, verify 0.2s, in=287, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Monotone]
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

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.2s, verify 0.1s, in=287, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Monotone, Function.comp, le_ofDual_iff]
```

**lean_error:** tail step 1/1 ('simp [Monotone, Function.comp, le_ofDual_iff]'): unknown identifier 'le_ofDual_iff'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=287, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [monotone_comp_iff, dual_preorder, monotone_dual_iff]
```

**lean_error:** tail step 1/1 ('simp only [monotone_comp_iff, dual_preorder, monotone_dual_iff]'): unknown identifier 'monotone_comp_iff'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 6.8s, verify 0.1s, in=287, out=220)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [monotone_toDual, antitone_comp_ofDual]
```

**lean_error:** tail step 1/1 ('simp only [monotone_toDual, antitone_comp_ofDual]'): unknown identifier 'monotone_toDual'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 7.2s, verify 0.1s, in=287, out=236)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 8.1s, verify 0.1s, in=287, out=266)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [← Function.comp.assoc, monotone_toDual_comp, antitone_comp_ofDual]
```

**lean_error:** tail step 1/1 ('simp only [← Function.comp.assoc, monotone_toDual_comp, antitone_comp_ofDual]'): unknown identifier 'monotone_toDual_comp'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 9.5s, verify 0.1s, in=287, out=311)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [monotone_toDual_iff, monotone_comp_ofDual]
```

**lean_error:** tail step 1/1 ('simp only [monotone_toDual_iff, monotone_comp_ofDual]'): unknown identifier 'monotone_toDual_iff'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 22.4s, verify 0.1s, in=605, out=868)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 28.4s, verify 0.1s, in=605, out=1096)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 73.6s, verify 0.1s, in=605, out=2956)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 92.7s, verify 0.1s, in=605, out=3788)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=605, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.7s, verify 0.1s, in=605, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.4s, verify 0.1s, in=605, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.6s, verify 0.1s, in=605, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 8.6s, verify 0.1s, in=605, out=279)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 9.0s, verify 0.1s, in=605, out=290)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 11.9s, verify 0.1s, in=605, out=406)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [← Function.comp.assoc, monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 14.9s, verify 0.1s, in=605, out=517)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa only [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 70.2s, verify 0.1s, in=938, out=1483)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 79.8s, verify 0.1s, in=938, out=2123)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 89.2s, verify 0.1s, in=938, out=2758)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
rfl
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 91.2s, verify 0.2s, in=938, out=2040)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [monotone_toDual_comp_iff]
rw [antitone_comp_ofDual_iff]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.2s, verify 0.1s, in=938, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.7s, verify 0.1s, in=938, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.7s, verify 0.1s, in=938, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.3s, verify 0.1s, in=938, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 13.6s, verify 0.1s, in=938, out=268)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 15.4s, verify 0.1s, in=938, out=270)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 18.0s, verify 0.1s, in=938, out=425)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp_rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 21.4s, verify 0.1s, in=938, out=551)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa only [Function.comp.assoc, monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 33.4s, verify 0.1s, in=963, out=1315)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 41.8s, verify 0.1s, in=963, out=1665)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 56.5s, verify 0.1s, in=963, out=2246)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 91.5s, verify 0.1s, in=963, out=3726)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.6s, verify 0.1s, in=963, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.3s, verify 0.1s, in=963, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.5s, verify 0.1s, in=963, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.0s, verify 0.1s, in=963, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 6.0s, verify 0.1s, in=963, out=195)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 8.0s, verify 0.1s, in=963, out=262)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Function.comp_assoc, monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

**lean_error:** tail step 1/1 ('rw [Function.comp_assoc, monotone_toDual_comp_iff, antitone_comp_ofDual_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 8.6s, verify 0.1s, in=963, out=274)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 8.9s, verify 0.1s, in=963, out=292)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [monotone_toDual_comp_iff, antitone_comp_ofDual_iff]
```
