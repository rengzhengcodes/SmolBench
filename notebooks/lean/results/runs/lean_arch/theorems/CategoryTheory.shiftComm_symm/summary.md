# CategoryTheory.shiftComm_symm   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Shift/Basic.lean`  

**Ground-truth tail (from k):**
```lean
exact NatTrans.congr_app (congr_arg Iso.hom (shiftFunctorComm_symm C i j)) X
```

**True premises at k:** `CategoryTheory.NatTrans.congr_app`, `congr_arg`, `CategoryTheory.Iso.hom`, `CategoryTheory.shiftFunctorComm_symm`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.1s, verify 0.1s, in=297, out=12)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [shiftComm_symm, shiftComm_hom]
```

**lean_error:** tail step 1/1 ('rw [shiftComm_symm, shiftComm_hom]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.2s, verify 0.1s, in=273, out=42)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Iso.symm_hom, ← comp_hom]
simp only [shiftComm_hom, Category.comp_id]
rw [Category.assoc, Iso.hom_inv_id, Category.comp_id]
```

**lean_error:** tail step 1/3 ('rw [Iso.symm_hom, ← comp_hom]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=286, out=11)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [symm_hom]
```

**lean_error:** tail step 1/1 ('rw [symm_hom]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.7s, verify 0.1s, in=818, out=50)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Iso.hom_congr, NatTrans.congr_app (congr_arg Iso.symm (shiftFunctorComm_symm C i j)) X]
rw [shiftFunctorComm_eq C j i X (add_comm j i)]
```

**lean_error:** tail step 1/2 ('rw [Iso.hom_congr, NatTrans.congr_app (congr_arg Iso.symm (shiftFunctorComm_symm C i j)) X]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.2s, in=784, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
dsimp
rw [shiftFunctorComm_symm C i j]
rfl
```

**lean_error:** tail step 2/3 ('rw [shiftFunctorComm_symm C i j]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 7.0s, verify 0.2s, in=807, out=320)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.Iso.hom, CategoryTheory.shiftFunctorComm_symm]
```

**lean_error:** tail step 1/1 ('rw [CategoryTheory.Iso.hom, CategoryTheory.shiftFunctorComm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 4.0s, verify 0.1s, in=2663, out=41)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Iso.symm_hom, shiftComm_eq X i j (i + j) rfl, shiftComm_eq X j i (i + j) (add_comm j i)] 
rfl
```

**lean_error:** tail step 1/2 ('rw [Iso.symm_hom, shiftComm_eq X i j (i + j) rfl, shiftComm_eq X j i (i + j) (add_comm j i)]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.7s, verify 0.2s, in=2600, out=14)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
dsimp
rw [shiftFunctorComm_symm]
rfl
```

**lean_error:** tail step 2/3 ('rw [shiftFunctorComm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 6.6s, verify 0.1s, in=2652, out=303)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [CategoryTheory.Iso.hom, CategoryTheory.shiftFunctorComm_symm]
```

**lean_error:** tail step 1/1 ('rw [CategoryTheory.Iso.hom, CategoryTheory.shiftFunctorComm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.5s, verify 0.1s, in=2690, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Iso.hom_congr (shiftFunctorComm_symm C i j)]
rw [Iso.symm_hom]
```

**lean_error:** tail step 1/2 ('rw [Iso.hom_congr (shiftFunctorComm_symm C i j)]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.4s, verify 0.3s, in=2867, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
dsimp
rw [shiftFunctorComm_symm]
rfl
```

**lean_error:** tail step 2/3 ('rw [shiftFunctorComm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 7.8s, verify 0.1s, in=2679, out=328)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [CategoryTheory.Iso.hom, CategoryTheory.shiftFunctorComm_symm]
```

**lean_error:** tail step 1/1 ('rw [CategoryTheory.Iso.hom, CategoryTheory.shiftFunctorComm_symm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
