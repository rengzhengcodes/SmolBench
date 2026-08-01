# Submodule.mem_dualAnnihilator   (k=2, 3 tactics total)

file: `Mathlib/LinearAlgebra/Dual.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨fun h w hw => h ⟨w, hw⟩, fun h w => h w.1 w.2⟩
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.5s, in=304, out=34)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  intro h w hw
  exact h ⟨w, hw⟩
constructor
  intro h ⟨w, hw⟩
  exact h w hw
```

**lean_error:** tail step 4/6 ('constructor'): tactic 'constructor' failed, target is not an inductive datatype

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.1s, in=278, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Submodule.forall]
simp only [coe_zero, map_zero, forall_true_left]
```

**lean_error:** tail step 1/2 ('rw [Submodule.forall]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=293, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply forall_congr'
intro w
refl
```

**lean_error:** tail step 1/3 ("apply forall_congr'"): tactic 'apply' failed, failed to unify
