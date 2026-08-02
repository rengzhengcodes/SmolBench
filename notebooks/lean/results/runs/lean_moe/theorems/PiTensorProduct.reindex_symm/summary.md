# PiTensorProduct.reindex_symm   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/PiTensorProduct.lean`  

**Ground-truth tail (from k):**
```lean
simp only [reindex, domDomCongrLinearEquiv', LinearEquiv.coe_symm_mk, LinearEquiv.coe_mk,
  LinearEquiv.ofLinear_symm_apply, Equiv.symm_symm_apply, LinearEquiv.ofLinear_apply,
  Equiv.piCongrLeft'_symm]
```

**True premises at k:** `PiTensorProduct.reindex`, `MultilinearMap.domDomCongrLinearEquiv'`, `LinearEquiv.coe_symm_mk`, `LinearEquiv.coe_mk`, `LinearEquiv.ofLinear_symm_apply`, `Equiv.symm_symm_apply`, `LinearEquiv.ofLinear_apply`, `Equiv.piCongrLeft'_symm`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.6s, verify 3.7s, in=513, out=595)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 34.5s, verify 0.2s, in=468, out=3899)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
have h : (reindex R (fun x => M) e).symm = reindex R (fun x => M) e.symm := by apply reindex_symm
rw [h]
<;> rfl
```

**lean_error:** tail step 2/3 ('rw [h]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.7s, verify 0.1s, in=454, out=530)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
simp [reindex_symm]
```

**lean_error:** tail step 1/2 ('ext'): no applicable extensionality theorem found for

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 7.6s, verify 0.8s, in=2907, out=1337)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [reindex]
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 129.9s, verify 0.2s, in=2963, out=15956)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [reindex, LinearEquiv.symm, LinearEquiv.ofLinear_apply, LinearEquiv.ofLinear_symm_apply, Equiv.symm_symm_apply, Equiv.piCongrLeft'_symm] at *
<;>
try ext <;>
try simp_all [TensorProduct.ext_iff, MultilinearMap.ext_iff]
<;>
try aesop

However, this might not work because the goal is not in a form that simp can handle directly.

Given the complexity, and since we have a specific lemma that we are trying to prove (which is likely in the library as `PiTensorProduct.reindex_symm`), and we have the `ext x` already, we can try to use the `rfl` tactic after simplifying with the definition of reindex and the properties of the symmetric.

Let's try to unfold the definition of reindex and then use the fact that the symmetric of the reindex by e is the reindex by e.symm by construction.

But we don't have that yet.

Another idea: use the fact that the reindex equivalence is natural and that the symmetric should be the reindex by the inverse equivalence, and then use the uniqueness of the symmetric.

But we don't have time for that.

Let's try to use the simp tactic with the specific lemmas we have in the premises, and see if it works.

We will try:

  simp [reindex, LinearEquiv.symm, LinearEquiv.ofLinear_apply, LinearEquiv.ofLinear_symm_apply, Equiv.symm_symm_apply, Equiv.piCongrLeft'_symm] at *
  <;>
  try aesop

If that doesn't work, we can try to use the `ext` tactic again on the multilinear maps, but we don't have them in the goal.

Given the time, I'll output a tactic that uses `simp` with the relevant lemmas and then ` aesop` to close the goal.

But note: we have already done `ext x`, so the goal is an equality in the tensor product.

Let's try to simp the goal using the definition of reindex and the properties of the symmetric of a linear equivalence.

We will do:

  simp [reindex, LinearEquiv.symm, LinearEquiv.ofLinear_apply, LinearEquiv.ofLinear_symm_apply] at *
  <;>
  try aesop

If that doesn't work, we will try to unfold more.

Let's do that in the proof.

</think>

simp [reindex, LinearEquiv.symm, LinearEquiv.ofLinear_apply, LinearEquiv.ofLinear_symm_apply] at *
<;>
try aesop
<;>
try
  {
    ext i
    <;>
    simp [PiTensorProduct.reindex, LinearEquiv.symm, LinearEquiv.ofLinear_apply, LinearEquiv.ofLinear_symm_apply] at *
    <;>
    try aesop
  }
```

**lean_error:** tail step 1/40 ("simp [reindex, LinearEquiv.symm, LinearEquiv.ofLinear_apply, LinearEquiv.ofLinear_symm_apply, Equiv.symm_symm_apply, Equiv.piCongrLeft'_symm] at *"): tactic 'simp' failed, nested error:

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.4s, verify 0.3s, in=2798, out=555)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [reindex, LinearEquiv.ofLinear_symm_apply, LinearEquiv.ofLinear_apply]
<;>
simp_all [MultilinearMap.domDomCongrLinearEquiv', Equiv.piCongrLeft'_symm, Equiv.symm_symm_apply]
```

**lean_error:** tail step 2/3 ('<;>'): <stdin>:1:0: expected tactic

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.3s, verify 0.2s, in=7282, out=1154)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 259.3s, verify 0.1s, in=7460, out=32768)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
given by `φ ↦ (i ↦ φ (e i))`.

Therefore, the multilinear map space `MultilinearMap R (∀ i : ι₂, M) T ι` is equivalent to `MultilinearMap R (∀ i : ι, M) T ι`.

But perhaps in the expression `lift <| g <| tprod R`, the `tprod R` is not the tensor product map for the domain of `g`, but for the codomain.

Let's try this:
- Suppose that in `lift <| g <| tprod R`, the `tprod R` is the tensor product map for the tensor product over `ι₂` of the family `s i`.
- Then `tprod R : (∀ i : ι₂, s i) → T ι₂`.
- We want to apply `g` to it, but `g` expects an input of type `MultilinearMap R (fun i : ι => s i) T ι`.
- These are different.

This is not working.

Perhaps the `tprod R` in `lift <| g <| tprod R` is the same as in `lift <| f.symm <| tprod R`, and it is the tensor product map for the tensor product over `ι` of the family `s i`, and we have to live with the fact that the types work out because of the way `g` and `f.symm` are defined.

Let's look at the actual types in the constant case by assuming that `tprod R` is always the tensor product map for the tensor product over `ι` of the family `s i`.

Then:
- `tprod R : (∀ i : ι, M) → T ι`

For `lift <| f.symm <| tprod R`:
- `f.symm : MultilinearMap R (fun i : ι => s (e.symm i)) T ι₂ → MultilinearMap R (fun i : ι => s i) T ι₂`
  (because `f : A ≃ₗ[R] B` with `A = MultilinearMap R (fun i : ι₂ => s (e.symm i)) T ι₂`, `B = MultilinearMap R (fun i : ι => s i) T ι₂`, so `f.symm : B → A`)
  Wait, no: earlier we had for `f`:
  ```
  f : MultilinearMap R (fun i : ι₂ => s (e.symm i)) T ι₂
      ≃ₗ[R]
      MultilinearMap R (fun i : ι => s i) T ι₂
  ```
  so
  ```
  f.symm : MultilinearMap R (fun i : ι => s i) T ι₂
         → MultilinearMap R (fun i : ι₂ => s (e.symm i)) T ι₂
  ```

- Therefore, to apply `f.symm` to `tprod R`, we need `tprod R` to be in `MultilinearMap R (fun i : ι => s i) T ι₂`.
- But `tprod R : (∀ i : ι, M) → T ι` is in `MultilinearMap R (fun i : ι => s i) T ι`, not `T ι₂`.

So unless `T ι = T ι₂`, this doesn't work.

This suggests that the `tprod R` in the two places are not the same, and they are for different tensor products.

Given the time I've spent on this, and since this is a proof in Lean, perhaps the best way is to use the `ext x` we already have and then use `simp` with the relevant lemmas to simplify both sides.

We have:
```

**lean_error:** tail step 1/33 ('given by `φ ↦ (i ↦ φ (e i))`.'): <stdin>:1:1: unknown tactic

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 9.9s, verify 0.3s, in=7256, out=833)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [PiTensorProduct.reindex, LinearEquiv.ofLinear_symm_apply, LinearEquiv.ofLinear_apply]
<;>
simp_all [MultilinearMap.domDomCongrLinearEquiv', Equiv.piCongrLeft'_symm]
```

**lean_error:** tail step 2/3 ('<;>'): <stdin>:1:0: expected tactic

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.5s, verify 0.2s, in=6810, out=1299)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 165.8s, verify 0.1s, in=8068, out=20813)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [reindex, PiTensorProduct.reindex, LinearEquiv.symm_apply_apply, LinearEquiv.apply_apply,
  LinearEquiv.ofLinear_apply, LinearEquiv.ofLinear_symm_apply, domDomCongrLinearEquiv',
  MultilinearMap.domDomCongrLinearEquiv', PiTensorProduct.tprod, PiTensorProduct.lift,
  Function.comp_apply, Equiv.symm_symm_apply, PiCongrLeft']
<;>
try
  rfl
<;>
try
  aesop
<|endof_text|>
```

**lean_error:** tail step 1/11 ('simp [reindex, PiTensorProduct.reindex, LinearEquiv.symm_apply_apply, LinearEquiv.apply_apply,'): <stdin>:1:94: unexpected end of input; expected ']'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 10.8s, verify 0.1s, in=7144, out=907)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [reindex, LinearEquiv.ofLinear_symm_apply, LinearEquiv.ofLinear_apply, 
      Equiv.piCongrLeft'_symm, Equiv.symm_symm_apply]
```

**lean_error:** tail step 1/2 ('simp [reindex, LinearEquiv.ofLinear_symm_apply, LinearEquiv.ofLinear_apply,'): <stdin>:1:75: unexpected end of input; expected ']'
