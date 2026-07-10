# CategoryTheory.shiftComm_symm   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Shift/Basic.lean`  

**Ground-truth tail (from k):**
```lean
exact NatTrans.congr_app (congr_arg Iso.hom (shiftFunctorComm_symm C i j)) X
```

**True premises at k:** `CategoryTheory.NatTrans.congr_app`, `congr_arg`, `CategoryTheory.Iso.hom`, `CategoryTheory.shiftFunctorComm_symm`

## Verdict matrix

| rung | llama-31-405b-base | llama-31-405b-lean-lora | nemotron-ultra-253b-base | nemotron-ultra-253b-lean-lora | qwen3-235b-a22b-base | qwen3-235b-a22b-lean-lora |
| --- | --- | --- | --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ | · | ✘ | · |
| `hint:2` | ✘ | ✘ | ✘ | ✘ | ✘ | · |
| `hint:3` | ✘ | ✘ | ✘ | ✘ | ✘ | · |
| `noise:3` | ✘ | ✘ | ✘ | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=297, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [shiftComm_symm, shiftComm_hom]
```

**lean_error:** tail step 1/1 ('rw [shiftComm_symm, shiftComm_hom]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 7.6s, verify 0.1s, in=297, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Iso.symm_hom, shiftComm_hom, add_comm]
```

**lean_error:** tail step 1/1 ('rw [Iso.symm_hom, shiftComm_hom, add_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=286, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [symm_hom]
```

**lean_error:** tail step 1/1 ('rw [symm_hom]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-lean-lora · rollout 0 → **incomplete**  (gen 0.9s, verify 0.1s, in=277, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Iso.symm_hom]
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

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 16.9s, verify 0.1s, in=270, out=488)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 10.4s, verify 0.1s, in=270, out=6)

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

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.3s, verify 0.1s, in=818, out=50)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Iso.hom_congr, NatTrans.congr_app (congr_arg Iso.symm (shiftFunctorComm_symm C i j)) X]
rw [shiftFunctorComm_eq C j i X (add_comm j i)]
```

**lean_error:** tail step 1/2 ('rw [Iso.hom_congr, NatTrans.congr_app (congr_arg Iso.symm (shiftFunctorComm_symm C i j)) X]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 8.6s, verify 0.1s, in=818, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
congr 1 <;> exact shiftFunctorComm_symm _ _ _
```

**lean_error:** tail step 1/1 ('congr 1 <;> exact shiftFunctorComm_symm _ _ _'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 11.2s, verify 0.1s, in=807, out=690)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.Iso.hom, CategoryTheory.shiftFunctorComm_symm]
```

**lean_error:** tail step 1/1 ('rw [CategoryTheory.Iso.hom, CategoryTheory.shiftFunctorComm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 2.7s, verify 0.3s, in=798, out=82)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.shiftFunctorComm_symm]
```

**lean_error:** tail step 1/1 ('rw [CategoryTheory.shiftFunctorComm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 108.7s, verify 0.1s, in=793, out=5148)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
NatTrans.congr_app (shiftFunctorComm_symm i j) X
```

**lean_error:** tail step 1/1 ('NatTrans.congr_app (shiftFunctorComm_symm i j) X'): <stdin>:1:1: unknown tactic

### `hint:2` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 10.6s, verify 0.1s, in=793, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [shiftFunctorComm_symm]
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

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.1s, in=2663, out=41)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Iso.symm_hom, shiftComm_eq X i j (i + j) rfl, shiftComm_eq X j i (i + j) (add_comm j i)] 
rfl
```

**lean_error:** tail step 1/2 ('rw [Iso.symm_hom, shiftComm_eq X i j (i + j) rfl, shiftComm_eq X j i (i + j) (add_comm j i)]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 7.7s, verify 0.1s, in=2663, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact congrArg Iso.hom (shiftFunctorComm_symm C i j)
```

**lean_error:** tail step 1/1 ('exact congrArg Iso.hom (shiftFunctorComm_symm C i j)'): application type mismatch

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 8.9s, verify 0.1s, in=2652, out=512)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [CategoryTheory.shiftFunctorComm_symm]
```

**lean_error:** tail step 1/1 ('rw [CategoryTheory.shiftFunctorComm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 4.7s, verify 0.1s, in=2643, out=132)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [CategoryTheory.Iso.hom, CategoryTheory.Iso.symm_hom, CategoryTheory.shiftFunctorComm_symm]
```

**lean_error:** tail step 1/1 ('rw [CategoryTheory.Iso.hom, CategoryTheory.Iso.symm_hom, CategoryTheory.shiftFunctorComm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 143.0s, verify 0.1s, in=2638, out=6892)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact congr_app (shiftFunctorComm_symm C i j) X
```

**lean_error:** tail step 1/1 ('exact congr_app (shiftFunctorComm_symm C i j) X'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 10.5s, verify 0.1s, in=2638, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [shiftFunctorComm_symm]
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

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=2690, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Iso.hom_congr (shiftFunctorComm_symm C i j)]
rw [Iso.symm_hom]
```

**lean_error:** tail step 1/2 ('rw [Iso.hom_congr (shiftFunctorComm_symm C i j)]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama-31-405b-lean-lora · rollout 0 → **lean_error**  (gen 7.8s, verify 0.8s, in=2690, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact congr_arg Iso.hom (shiftFunctorComm_symm C i j)
```

**lean_error:** tail step 1/1 ('exact congr_arg Iso.hom (shiftFunctorComm_symm C i j)'): application type mismatch

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 4.5s, verify 0.1s, in=2679, out=244)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [CategoryTheory.shiftFunctorComm_symm]
```

**lean_error:** tail step 1/1 ('rw [CategoryTheory.shiftFunctorComm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-lean-lora · rollout 0 → **lean_error**  (gen 7.2s, verify 0.1s, in=2670, out=258)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [CategoryTheory.shiftFunctorComm_symm]
```

**lean_error:** tail step 1/1 ('rw [CategoryTheory.shiftFunctorComm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 59.1s, verify 0.1s, in=2668, out=2617)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [shiftFunctorComm_symm]
rfl
```

**lean_error:** tail step 1/2 ('rw [shiftFunctorComm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-lean-lora · rollout 0 → **incomplete**  (gen 10.7s, verify 0.1s, in=2668, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [shiftFunctorComm_symm]
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
