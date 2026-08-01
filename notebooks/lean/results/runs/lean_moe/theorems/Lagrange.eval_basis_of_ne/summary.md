# Lagrange.eval_basis_of_ne   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Lagrange.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨j, ⟨mem_erase.mpr ⟨hij.symm, hj⟩, eval_basisDivisor_right⟩⟩
```

**True premises at k:** `Lagrange.eval_basisDivisor_right`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.7s, verify 0.3s, in=361, out=1531)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
refine ⟨j, ?_, ?_⟩
· simpa [Finset.mem_erase, hij, hj]
· simpa [basisDivisor]
```

**lean_error:** tail step 2/3 ('· simpa [Finset.mem_erase, hij, hj]'): tactic 'assumption' failed

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.5s, verify 0.4s, in=585, out=1250)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
refine ⟨j, ?_, ?_⟩
· simpa [Finset.mem_erase, hij.symm, hj]
· simp
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.1s, verify 0.2s, in=743, out=1163)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
refine ⟨j, ?_, ?_⟩
·
  have hji : j ≠ i := by
    intro h
    exact hij (h.symm)
  exact (Finset.mem_erase).2 ⟨hji, hj⟩
·
  simpa using (Lagrange.eval_basisDivisor_right (x := v i) (y := v j))
```

**lean_error:** tail step 2/8 ('·'): <stdin>:1:1: unexpected end of input; expected '{'

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.8s, verify 0.2s, in=751, out=1076)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
refine ⟨j, ?_, ?_⟩
·
  have hji : j ≠ i := (ne_comm).mp hij
  exact Finset.mem_erase.mpr ⟨hji, hj⟩
·
  simpa using (Lagrange.eval_basisDivisor_right (x:=v i) (y:=v j))
```

**lean_error:** tail step 2/6 ('·'): <stdin>:1:1: unexpected end of input; expected '{'
