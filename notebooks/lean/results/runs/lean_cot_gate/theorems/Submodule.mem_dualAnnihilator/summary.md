# Submodule.mem_dualAnnihilator   (k=2, 3 tactics total)

file: `Mathlib/LinearAlgebra/Dual.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨fun h w hw => h ⟨w, hw⟩, fun h w => h w.1 w.2⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✓ ✘ ✓ ✘ | ✓ ✓ ✘ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 51.6s, verify 0.1s, in=277, out=2258)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· intro h w hw
  exact h ⟨w, hw⟩
· intro h x
  exact h ↑x x.2
```

**lean_error:** tail step 1/5 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 64.3s, verify 0.1s, in=277, out=2773)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
  intro h w hw
  exact h ⟨w, hw⟩
  intro h x
  cases x with w hw
  exact h w hw
```

**lean_error:** tail step 1/6 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 97.5s, verify 0.1s, in=277, out=4072)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
  intro h w hw
  exact h ⟨w, hw⟩
  intro h x
  cases x with val mem
  exact h val mem
```

**lean_error:** tail step 1/6 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 153.5s, verify 0.1s, in=277, out=6507)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
intro h w hw
specialize h ⟨w, hw⟩
rw h
intro h x
specialize h ↑x x.property
rw h
```

**lean_error:** tail step 1/7 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.3s, verify 0.2s, in=277, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.5s, verify 0.8s, in=277, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.3s, verify 0.1s, in=277, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [LinearMap.ext_iff]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.4s, verify 0.1s, in=277, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [LinearMap.zero_apply, forall_subtype_iff]
```

**lean_error:** tail step 1/1 ('simp only [LinearMap.zero_apply, forall_subtype_iff]'): unknown identifier 'forall_subtype_iff'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 8.0s, verify 0.2s, in=277, out=296)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 9.1s, verify 0.1s, in=277, out=336)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [LinearMap.zero_apply, Subtype.forall]
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 9.2s, verify 0.1s, in=277, out=348)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Subtype.forall, forall_subtype, zero_apply]
```

**lean_error:** tail step 1/1 ('simp only [Subtype.forall, forall_subtype, zero_apply]'): unknown identifier 'forall_subtype'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 11.1s, verify 0.2s, in=277, out=428)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Subtype.forall, Subtype.coe_mk]
```
