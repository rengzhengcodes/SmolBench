# LinearMap.IsProj.isCompl   (k=1, 2 tactics total)

file: `Mathlib/LinearAlgebra/Projection.lean`  

**Ground-truth tail (from k):**
```lean
exact isCompl_of_proj h.codRestrict_apply_cod
```

**True premises at k:** `LinearMap.isCompl_of_proj`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ ✘ ✘ ✘ ✘ |
| `hint:2` | · · · ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ ✘ · ✘ ✘ |
| `hint:3` | · ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ · ✘ ✘ ✘ |
| `noise:3` | · · · ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 64.4s, verify 0.1s, in=1063, out=3194)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IsCompl.symm (h.isCompl)
```

**lean_error:** tail step 1/1 ('exact IsCompl.symm (h.isCompl)'): application type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 91.1s, verify 0.1s, in=1063, out=4632)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [LinearMap.ker_codRestrict]
apply is_proj.is_compl_ker_image h
exact h
trivial
```

**lean_error:** tail step 1/4 ('simp only [LinearMap.ker_codRestrict]'): simp made no progress

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 105.5s, verify 0.2s, in=1063, out=5383)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply IsProj.isCompl h
```

**lean_error:** tail step 1/1 ('apply IsProj.isCompl h'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 148.3s, verify 0.1s, in=1063, out=7564)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw ker_codRestrict
exact IsCompl_of_is_proj h
apply IsProj_of_ker h
apply Submodule.ker
```

**lean_error:** tail step 1/4 ('rw ker_codRestrict'): <stdin>:1:3: expected '['

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.9s, verify 0.1s, in=1063, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.isCompl
```

**lean_error:** tail step 1/1 ('exact h.isCompl'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=1063, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.isCompl_ker
```

**lean_error:** tail step 1/1 ('exact h.isCompl_ker'): invalid field 'isCompl_ker', the environment does not contain 'LinearMap.IsProj.isCompl_ker'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.2s, verify 0.1s, in=1063, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.isCompl_ker
```

**lean_error:** tail step 1/1 ('exact h.isCompl_ker'): invalid field 'isCompl_ker', the environment does not contain 'LinearMap.IsProj.isCompl_ker'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 3.4s, verify 0.1s, in=1063, out=10)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.isCompl
```

**lean_error:** tail step 1/1 ('exact h.isCompl'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 4.5s, verify 0.1s, in=1063, out=131)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.2
```

**lean_error:** tail step 1/1 ('exact h.2'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 7.0s, verify 0.1s, in=1063, out=208)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [LinearMap.isProj] using h
```

**lean_error:** tail step 1/1 ('simpa [LinearMap.isProj] using h'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 7.7s, verify 0.1s, in=1063, out=232)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.2
```

**lean_error:** tail step 1/1 ('exact h.2'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 8.7s, verify 0.1s, in=1063, out=257)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.isCompl_ker
```

**lean_error:** tail step 1/1 ('exact h.isCompl_ker'): invalid field 'isCompl_ker', the environment does not contain 'LinearMap.IsProj.isCompl_ker'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 10.3s, verify 0.1s, in=1063, out=314)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
convert h.isCompl_ker using 1 <;> simp [ker_codRestrict]
```

**lean_error:** tail step 1/1 ('convert h.isCompl_ker using 1 <;> simp [ker_codRestrict]'): invalid field 'isCompl_ker', the environment does not contain 'LinearMap.IsProj.isCompl_ker'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 10.9s, verify 0.1s, in=1063, out=273)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.compl
```

**lean_error:** tail step 1/1 ('exact h.compl'): invalid field 'compl', the environment does not contain 'LinearMap.IsProj.compl'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 13.0s, verify 0.1s, in=1063, out=397)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exacts [h.isCompl_ker, h, p]
```

**lean_error:** tail step 1/1 ('exacts [h.isCompl_ker, h, p]'): no goals to be solved

### `stepk:1` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 17.7s, verify 0.1s, in=1063, out=526)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact ⟨h.isCompl_ker, h.isCompl_ker.1, p⟩
```

**lean_error:** tail step 1/1 ('exact ⟨h.isCompl_ker, h.isCompl_ker.1, p⟩'): invalid field 'isCompl_ker', the environment does not contain 'LinearMap.IsProj.isCompl_ker'

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **incomplete**  (gen 11.1s, verify 0.4s, in=1407, out=532)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply isCompl_of_proj
simp [h]
```

**final state (truncated):**
```
R : Type u_1
inst✝⁹ : Ring R
E : Type u_2
inst✝⁸ : AddCommGroup E
inst✝⁷ : Module R E
F : Type u_3
...
```

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 20.3s, verify 0.2s, in=1407, out=953)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
```

**final state (truncated):**
```
case hf
R : Type u_1
inst✝⁹ : Ring R
E : Type u_2
inst✝⁸ : AddCommGroup E
inst✝⁷ : Module R E
...
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **incomplete**  (gen 66.0s, verify 0.2s, in=1407, out=3273)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply isCompl_of_proj
```

**final state (truncated):**
```
case hf
R : Type u_1
inst✝⁹ : Ring R
E : Type u_2
inst✝⁸ : AddCommGroup E
inst✝⁷ : Module R E
...
```

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 145.2s, verify 0.7s, in=1407, out=7386)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
intro x
ext
exact h x
```

**lean_error:** tail step 4/4 ('exact h x'): function expected at

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1407, out=12)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact h.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('exact h.isCompl_of_proj'): invalid field 'isCompl_of_proj', the environment does not contain 'LinearMap.IsProj.isCompl_of_proj'

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.6s, verify 0.1s, in=1407, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isCompl_of_proj fun x => h.idem_codRestrict x
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj fun x => h.idem_codRestrict x'): invalid field 'idem_codRestrict', the environment does not contain 'LinearMap.IsProj.idem_codRestrict'

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.7s, verify 0.1s, in=1407, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isCompl_of_proj fun x ↦ h.commute.submodule_coe x
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj fun x ↦ h.commute.submodule_coe x'): invalid field 'commute', the environment does not contain 'LinearMap.IsProj.commute'

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 3.9s, verify 0.1s, in=1407, out=35)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isCompl_of_proj fun x => congr_arg (fun y => ⟨y, _⟩) (h.left_codRestrict_apply x)
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj fun x => congr_arg (fun y => ⟨y, _⟩) (h.left_codRestrict_apply x)'): type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 6.5s, verify 0.2s, in=1407, out=190)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← codRestrict_ker, h.isCompl]
```

**lean_error:** tail step 1/1 ('rw [← codRestrict_ker, h.isCompl]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 6.6s, verify 0.1s, in=1407, out=191)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isCompl_of_proj h.2
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj h.2'): application type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 10.1s, verify 0.1s, in=1407, out=246)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact h.1.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('exact h.1.isCompl_of_proj'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 10.7s, verify 0.1s, in=1407, out=188)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact h.isCompl
```

**lean_error:** tail step 1/1 ('exact h.isCompl'): type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 13.2s, verify 0.1s, in=1407, out=411)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using h.surj.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('simpa using h.surj.isCompl_of_proj'): invalid field 'surj', the environment does not contain 'LinearMap.IsProj.surj'

### `hint:2` · qwen3-lean-cot-r128 · rollout 6 → **incomplete**  (gen 15.3s, verify 0.2s, in=1407, out=273)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
```

**final state (truncated):**
```
case hf
R : Type u_1
inst✝⁹ : Ring R
E : Type u_2
inst✝⁸ : AddCommGroup E
inst✝⁷ : Module R E
...
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 17.2s, verify 0.1s, in=1407, out=292)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isCompl_of_proj (f.codRestrict p h.range) h.idem
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj (f.codRestrict p h.range) h.idem'): invalid field 'range', the environment does not contain 'LinearMap.IsProj.range'

### `hint:2` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 20.0s, verify 0.1s, in=1407, out=427)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact isCompl_of_proj fun x => LinearMap.congr_arg Subtype.val (h.2.2 ⟨x, rfl⟩)
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj fun x => LinearMap.congr_arg Subtype.val (h.2.2 ⟨x, rfl⟩)'): application type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 20.7s, verify 0.2s, in=2028, out=414)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
```

**final state (truncated):**
```
case hf
R : Type u_1
inst✝⁹ : Ring R
E : Type u_2
inst✝⁸ : AddCommGroup E
inst✝⁷ : Module R E
...
```

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 29.4s, verify 0.3s, in=2028, out=440)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
exact h
```

**lean_error:** tail step 2/2 ('exact h'): type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 73.5s, verify 0.3s, in=2028, out=2709)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
exact h.idempotent
exact h.image_le
exact h.range_eq
exact h.ker_eq
exact h.le_ker
exact h.ker_le
```

**lean_error:** tail step 2/7 ('exact h.idempotent'): invalid field 'idempotent', the environment does not contain 'LinearMap.IsProj.idempotent'

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 141.4s, verify 0.1s, in=2028, out=6342)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply isCompl_of_proj (codRestrict f p)
intros x
ext
have h_mem : x ∈ p := x.2
obtain ⟨y, rfl⟩ := h.image ▸ h_mem
rw [← h.idem, LinearMap.comp_apply]
rfl
```

**lean_error:** tail step 1/7 ('apply isCompl_of_proj (codRestrict f p)'): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.9s, verify 0.1s, in=2028, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact isCompl_of_proj fun x ↦ h.idemp x.2
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj fun x ↦ h.idemp x.2'): invalid field 'idemp', the environment does not contain 'LinearMap.IsProj.idemp'

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.0s, verify 0.1s, in=2028, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact isCompl_of_proj fun x ↦ h.commute.submodule_coe x
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj fun x ↦ h.commute.submodule_coe x'): invalid field 'commute', the environment does not contain 'LinearMap.IsProj.commute'

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.1s, verify 0.1s, in=2028, out=32)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact isCompl_of_proj fun x => congr_arg (fun y => ⟨y, _⟩) (h.left_inv x)
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj fun x => congr_arg (fun y => ⟨y, _⟩) (h.left_inv x)'): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 8.4s, verify 0.1s, in=2028, out=12)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact h.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('exact h.isCompl_of_proj'): invalid field 'isCompl_of_proj', the environment does not contain 'LinearMap.IsProj.isCompl_of_proj'

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 22.6s, verify 0.1s, in=2028, out=241)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact h.isCompl
```

**lean_error:** tail step 1/1 ('exact h.isCompl'): type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 23.4s, verify 0.1s, in=2028, out=202)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact h.isCompl
```

**lean_error:** tail step 1/1 ('exact h.isCompl'): type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 23.5s, verify 0.1s, in=2028, out=273)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact LinearMap.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('exact LinearMap.isCompl_of_proj'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 25.1s, verify 0.1s, in=2028, out=247)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact isCompl_of_proj (f.codRestrict p h)
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj (f.codRestrict p h)'): application type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 27.2s, verify 0.2s, in=2028, out=450)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply isCompl_of_proj
```

**final state (truncated):**
```
case hf
R : Type u_1
inst✝⁹ : Ring R
E : Type u_2
inst✝⁸ : AddCommGroup E
inst✝⁷ : Module R E
...
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 27.4s, verify 0.1s, in=2028, out=332)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact h.isCompl
```

**lean_error:** tail step 1/1 ('exact h.isCompl'): type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 29.5s, verify 0.1s, in=2028, out=396)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply h.toLinearMap.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('apply h.toLinearMap.isCompl_of_proj'): invalid field 'toLinearMap', the environment does not contain 'LinearMap.IsProj.toLinearMap'

### `hint:3` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 33.9s, verify 0.1s, in=2028, out=466)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← codRestrict_ker] <;>
exact isCompl_of_proj fun x ↦ h.self_mem ⟨x, h.mem_ker.mp (mem_ker.mpr (h.self_mem x))⟩
```

**lean_error:** tail step 1/2 ('rw [← codRestrict_ker] <;>'): <stdin>:1:26: unexpected end of input; expected '['

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **incomplete**  (gen 18.3s, verify 0.2s, in=2056, out=857)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply isCompl_of_proj
```

**final state (truncated):**
```
case hf
R : Type u_1
inst✝⁹ : Ring R
E : Type u_2
inst✝⁸ : AddCommGroup E
inst✝⁷ : Module R E
...
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 27.4s, verify 0.2s, in=2056, out=1294)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply isCompl_of_proj
```

**final state (truncated):**
```
case hf
R : Type u_1
inst✝⁹ : Ring R
E : Type u_2
inst✝⁸ : AddCommGroup E
inst✝⁷ : Module R E
...
```

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **incomplete**  (gen 57.8s, verify 0.2s, in=2056, out=2864)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply LinearMap.isCompl_of_proj
```

**final state (truncated):**
```
case hf
R : Type u_1
inst✝⁹ : Ring R
E : Type u_2
inst✝⁸ : AddCommGroup E
inst✝⁷ : Module R E
...
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 67.0s, verify 0.4s, in=2056, out=3330)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply isCompl_of_proj
intro x hx
apply Subtype.eq
exact h.2 hx
```

**lean_error:** tail step 2/4 ('intro x hx'): tactic 'introN' failed, insufficient number of binders

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=2056, out=12)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact h.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('exact h.isCompl_of_proj'): invalid field 'isCompl_of_proj', the environment does not contain 'LinearMap.IsProj.isCompl_of_proj'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=2056, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact isCompl_of_proj fun x => h.idem ⟨x, x.prop⟩
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj fun x => h.idem ⟨x, x.prop⟩'): invalid field 'idem', the environment does not contain 'LinearMap.IsProj.idem'

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.8s, verify 0.1s, in=2056, out=32)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact isCompl_of_proj fun x => congr_arg (fun y => ⟨y, _⟩) (h.left_inv x)
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj fun x => congr_arg (fun y => ⟨y, _⟩) (h.left_inv x)'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 3.7s, verify 0.1s, in=2056, out=24)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact isCompl_of_proj fun x ↦ h.commutes ⟨x, x.prop⟩
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj fun x ↦ h.commutes ⟨x, x.prop⟩'): invalid field 'commutes', the environment does not contain 'LinearMap.IsProj.commutes'

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 13.8s, verify 0.1s, in=2056, out=188)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact h.isCompl
```

**lean_error:** tail step 1/1 ('exact h.isCompl'): type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 15.5s, verify 0.1s, in=2056, out=215)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact h.2.isCompl_of_proj
```

**lean_error:** tail step 1/1 ('exact h.2.isCompl_of_proj'): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 17.3s, verify 0.1s, in=2056, out=209)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact isCompl_of_proj h.1
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj h.1'): application type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 17.8s, verify 0.1s, in=2056, out=236)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact h.isCompl
```

**lean_error:** tail step 1/1 ('exact h.isCompl'): type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 18.9s, verify 0.1s, in=2056, out=257)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact isCompl_of_proj fun x ↦ rfl
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj fun x ↦ rfl'): type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 20.1s, verify 0.1s, in=2056, out=217)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact LinearMap.isCompl_of_proj h.2
```

**lean_error:** tail step 1/1 ('exact LinearMap.isCompl_of_proj h.2'): application type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 20.3s, verify 0.1s, in=2056, out=221)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact h.isCompl
```

**lean_error:** tail step 1/1 ('exact h.isCompl'): type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 97.8s, verify 0.1s, in=2056, out=221)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact isCompl_of_proj (h.surj.codRestrict f)
```

**lean_error:** tail step 1/1 ('exact isCompl_of_proj (h.surj.codRestrict f)'): invalid field 'surj', the environment does not contain 'LinearMap.IsProj.surj'
