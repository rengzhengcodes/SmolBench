# ExteriorAlgebra.liftAlternating_ι_mul   (k=2, 3 tactics total)

file: `Mathlib/LinearAlgebra/ExteriorAlgebra/OfAlternating.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **success**  (gen 0.4s, verify 0.2s, in=733, out=87)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 22.7s, verify 0.1s, in=732, out=3542)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
theorem your_theorem_name : (((CliffordAlgebra.foldl 0 (LinearMap.mk₂ R (fun m f i => (AlternatingMap.curryLeft (f (Nat.succ i))) m) ⋯ ⋯ ⋯ ⋯) ⋯)
          (((LinearMap.mk₂ R (fun m f i => (AlternatingMap.curryLeft (f (Nat.succ i))) m) ⋯ ⋯ ⋯ ⋯) m) f))
        x 0)
      0 =
    (((CliffordAlgebra.foldl 0 (LinearMap.mk₂ R (fun m f i => (AlternatingMap.curryLeft (f (Nat.succ i))) m) ⋯ ⋯ ⋯ ⋯) ⋯)
          fun i => (AlternatingMap.curryLeft (f (Nat.succ i))) m)
        x 0)
      0 := by
  have h_main : (((LinearMap.mk₂ R (fun m f i => (AlternatingMap.curryLeft (f (Nat.succ i))) m) ⋯ ⋯ ⋯ ⋯) m) f) = (fun i => (AlternatingMap.curryLeft (f (Nat.succ i))) m) := by
    ext i
    -- Simplify the application of the bilinear map to m and then to f
    simp [LinearMap.mk₂_apply_right, LinearMap.mk₂_apply_left]
    <;>
    aesop
  
  have h_final : (((CliffordAlgebra.foldl 0 (LinearMap.mk₂ R (fun m f i => (AlternatingMap.curryLeft (f (Nat.succ i))) m) ⋯ ⋯ ⋯ ⋯) ⋯)
          (((LinearMap.mk₂ R (fun m f i => (AlternatingMap.curryLeft (f (Nat.succ i))) m) ⋯ ⋯ ⋯ ⋯) m) f))
        x 0)
      0 =
    (((CliffordAlgebra.foldl 0 (LinearMap.mk₂ R (fun m f i => (AlternatingMap.curryLeft (f (Nat.succ i))) m) ⋯ ⋯ ⋯ ⋯) ⋯)
          fun i => (AlternatingMap.curryLeft (f (Nat.succ i))) m)
        x 0)
      0 := by
    rw [h_main]
    <;>
    rfl
  
  exact h_final
```

**lean_error:** tail step 1/26 ('theorem your_theorem_name : (((CliffordAlgebra.foldl 0 (LinearMap.mk₂ R (fun m f i => (AlternatingMap.curryLeft (f (Nat.succ i))) m) ⋯ ⋯ ⋯ ⋯) ⋯)'): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.4s, verify 0.1s, in=722, out=560)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [Function.comp_apply]
<;> rfl
```

**lean_error:** tail step 1/2 ('simp only [Function.comp_apply]'): simp made no progress
