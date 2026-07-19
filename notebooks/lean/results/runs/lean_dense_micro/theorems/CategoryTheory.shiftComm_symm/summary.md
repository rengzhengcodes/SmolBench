# CategoryTheory.shiftComm_symm   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Shift/Basic.lean`  

**Ground-truth tail (from k):**
```lean
exact NatTrans.congr_app (congr_arg Iso.hom (shiftFunctorComm_symm C i j)) X
```

**True premises at k:** `CategoryTheory.NatTrans.congr_app`, `congr_arg`, `CategoryTheory.Iso.hom`, `CategoryTheory.shiftFunctorComm_symm`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · · ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.6s, verify 0.1s, in=297, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [shiftComm_symm, shiftComm_hom]
```

**lean_error:** tail step 1/1 ('rw [shiftComm_symm, shiftComm_hom]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=297, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [shiftComm_symm],
rw [shiftComm_hom]
```

**lean_error:** tail step 1/2 ('rw [shiftComm_symm],'): <stdin>:1:19: expected end of input

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 0.7s, verify 0.1s, in=297, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [shiftComm_symm]
rw [shiftComm_hom]
```

**lean_error:** tail step 1/2 ('rw [shiftComm_symm]'): kernel type check failed: (kernel) declaration has free variables '[anonymous]'

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.1s, verify 0.1s, in=297, out=21)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [shiftComm_symm_hom]
rw [shiftComm_hom] 
exact add_comm i j
```

**lean_error:** tail step 1/3 ('rw [shiftComm_symm_hom]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **incomplete**  (gen 1.9s, verify 0.1s, in=297, out=2)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
case w
C : Type u
A : Type u_1
inst✝² : Category.{v, u} C
inst✝¹ : AddCommMonoid A
inst✝ : HasShift C A
...
```

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **incomplete**  (gen 2.0s, verify 0.1s, in=297, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [shiftComm]
```

**final state (truncated):**
```
case w
C : Type u
A : Type u_1
inst✝² : Category.{v, u} C
inst✝¹ : AddCommMonoid A
inst✝ : HasShift C A
...
```

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 2.6s, verify 0.1s, in=297, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [shift_comm_hom, shift_comm_symm_hom]
```

**lean_error:** tail step 1/1 ('simp [shift_comm_hom, shift_comm_symm_hom]'): unknown identifier 'shift_comm_hom'

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 2.6s, verify 0.1s, in=297, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [shiftComm, Iso.symm, Iso.mk_hom]
```

**lean_error:** tail step 1/1 ('simp only [shiftComm, Iso.symm, Iso.mk_hom]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.8s, verify 0.2s, in=818, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
dsimp
rw [CategoryTheory.shiftFunctorComm_symm]
```

**lean_error:** tail step 2/2 ('rw [CategoryTheory.shiftFunctorComm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=818, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
congr_arg Iso.hom
rw [shiftFunctorComm_symm]
```

**lean_error:** tail step 1/2 ('congr_arg Iso.hom'): <stdin>:1:1: unknown tactic

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.5s, verify 0.2s, in=818, out=50)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
dsimp
rw [CategoryTheory.Iso.symm_hom, CategoryTheory.Iso.hom, CategoryTheory.shiftFunctorComm_symm]
congr_arg
ext1
dsimp
rw [CategoryTheory.NatTrans.congr_app]
```

**lean_error:** tail step 2/6 ('rw [CategoryTheory.Iso.symm_hom, CategoryTheory.Iso.hom, CategoryTheory.shiftFunctorComm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.7s, verify 0.1s, in=818, out=48)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.Iso.symm_hom, CategoryTheory.shiftComm_hom]
rw [CategoryTheory.shiftFunctorComm_symm]
apply CategoryTheory.NatTrans.congr_app
rw [CategoryTheory.shiftComm_hom]
rfl
```

**lean_error:** tail step 1/5 ('rw [CategoryTheory.Iso.symm_hom, CategoryTheory.shiftComm_hom]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 2.9s, verify 0.1s, in=818, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact congr_app (congr_arg Iso.hom (shiftFunctorComm_symm _ _)) X
```

**lean_error:** tail step 1/1 ('exact congr_app (congr_arg Iso.hom (shiftFunctorComm_symm _ _)) X'): application type mismatch

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **success**  (gen 3.0s, verify 0.1s, in=818, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact congr_app (congr_arg Iso.hom (shiftFunctorComm_symm C i j)) X
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **success**  (gen 3.1s, verify 0.1s, in=818, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact congr_app (congr_arg Iso.hom (shiftFunctorComm_symm C i j)) X
```

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **success**  (gen 3.3s, verify 0.1s, in=818, out=33)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact CategoryTheory.NatTrans.congr_app (congr_arg CategoryTheory.Iso.hom (CategoryTheory.shiftFunctorComm_symm C i j)) X
```
