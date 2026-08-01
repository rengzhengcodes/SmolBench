# LinearPMap.inverse_range   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/LinearPMap.lean`  

**Ground-truth tail (from k):**
```lean
rfl
```

**True premises at k:** _(none recorded)_

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.5s, in=439, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
rw [LinearEquiv.coe_coe]
```

**lean_error:** tail step 2/2 ('rw [LinearEquiv.coe_coe]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.3s, verify 1.8s, in=409, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
simp only [LinearEquiv.coe_coe]
```

**lean_error:** tail step 2/2 ('simp only [LinearEquiv.coe_coe]'): simp made no progress

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 2.4s, verify 1.2s, in=428, out=114)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
```

**final state (truncated):**
```
case e_p.e_σ₁₂
R : Type u_1
inst✝⁶ : Ring R
E : Type u_2
inst✝⁵ : AddCommGroup E
inst✝⁴ : Module R E
...
```
