# symmDiff_eq_iff_sdiff_eq   (k=1, 2 tactics total)

file: `Mathlib/Order/SymmDiff.lean`  

**Ground-truth tail (from k):**
```lean
exact ((symmDiff_right_involutive a).toPerm _).apply_eq_iff_eq_symm_apply.trans eq_comm
```

**True premises at k:** `symmDiff_right_involutive`, `Function.Involutive.toPerm`, `eq_comm`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ · ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✓ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✓ ✓ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 107.2s, verify 0.1s, in=250, out=4614)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
intro h
rw [h]
rw [← symm_diff_assoc]
rw [symm_diff_self]
rw [zero_symm_diff]
intro h
rw [h]
rw [← symm_diff_assoc]
rw [symm_diff_self]
rw [zero_symm_diff]
```

**lean_error:** tail step 1/11 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 140.2s, verify 0.3s, in=250, out=6076)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Iff.intro
intro h
rw [h]
rw [symmDiff_assoc]
rw [symmDiff_self]
rw [bot_symmDiff]
intro h
rw [h]
rw [symmDiff_assoc]
rw [symmDiff_self]
rw [bot_symmDiff]
```

**lean_error:** tail step 3/11 ('rw [h]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 147.2s, verify 0.1s, in=250, out=6383)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split;
intro h;
rw [h, ← symm_diff_assoc, symm_diff_self_left, symm_diff_zero_left]
```

**lean_error:** tail step 1/3 ('split;'): <stdin>:1:5: expected end of input

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 273.7s, verify 0.1s, in=250, out=12621)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
intro h
rw symm_diff_eq_sdiff_sup_sdiff at h
rw h
rw sdiff_sdiff_cancel ha
rw sup_sdiff_cancel ha
intro h
rw symm_diff_eq_sdiff_sup_sdiff at h
rw h
rw sdiff_sdiff_cancel ha
rw sup_sdiff_cancel ha
```

**lean_error:** tail step 1/11 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=250, out=40)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [symmDiff_eq_sup_sdiff_inf, sup_eq_right.2 ha, inf_eq_left.2 ha, ← symmDiff_sdiff_eq_sdiff]
```

**lean_error:** tail step 1/1 ('rw [symmDiff_eq_sup_sdiff_inf, sup_eq_right.2 ha, inf_eq_left.2 ha, ← symmDiff_sdiff_eq_sdiff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.8s, verify 0.1s, in=250, out=43)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [symmDiff_eq_sup_sdiff_inf, sup_eq_right.mpr ha, inf_eq_left.mpr ha, sdiff_self,
  sup_zero_eq, eq_comm]
```

**lean_error:** tail step 1/2 ('simp_rw [symmDiff_eq_sup_sdiff_inf, sup_eq_right.mpr ha, inf_eq_left.mpr ha, sdiff_self,'): <stdin>:1:88: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.3s, verify 0.1s, in=250, out=74)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [symmDiff_eq_sup_sdiff_inf, sup_eq_right.mpr ha, inf_eq_left.mpr ha, sdiff_eq_self_iff_disjoint,
  symmDiff_eq_sup_sdiff_inf, sup_eq_right.mpr ha, inf_eq_left.mpr ha, sdiff_eq_self_iff_disjoint,
  disjoint.comm]
```

**lean_error:** tail step 1/3 ('rw [symmDiff_eq_sup_sdiff_inf, sup_eq_right.mpr ha, inf_eq_left.mpr ha, sdiff_eq_self_iff_disjoint,'): <stdin>:1:99: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.4s, verify 0.1s, in=250, out=76)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [symmDiff_comm, symmDiff_eq_sup_sdiff_inf, sup_eq_right.2 ha, inf_eq_left.2 ha,
  sdiff_self, sup_bot_eq, symmDiff_eq_sup_sdiff_inf, sup_eq_right.2 ha, inf_eq_left.2 ha,
  sdiff_self, sup_bot_eq]
```

**lean_error:** tail step 1/3 ('rw [symmDiff_comm, symmDiff_eq_sup_sdiff_inf, sup_eq_right.2 ha, inf_eq_left.2 ha,'): <stdin>:1:82: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 11.7s, verify 0.1s, in=250, out=359)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [sdiff_eq_sup_sdiff, sdiff_eq_bot_iff.mpr ha, sup_bot_eq, sdiff_eq_comm' ha]
```

**lean_error:** tail step 1/1 ("simp only [sdiff_eq_sup_sdiff, sdiff_eq_bot_iff.mpr ha, sup_bot_eq, sdiff_eq_comm' ha]"): unknown identifier 'sdiff_eq_sup_sdiff'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 12.4s, verify 0.1s, in=250, out=384)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [symmDiff_eq_sup_sdiff_inf, le_sup_inf_of_inf_le_sup ha,
  sdiff_eq_self_iff_disjoint_sup inf_le_sup (le_sup_inf_of_inf_le_sup ha)]
```

**lean_error:** tail step 1/2 ('simp only [symmDiff_eq_sup_sdiff_inf, le_sup_inf_of_inf_le_sup ha,'): <stdin>:1:66: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 13.3s, verify 0.1s, in=250, out=410)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [symmDiff_eq_right, and_comm, sup_eq_right, inf_eq_left]
```

**lean_error:** tail step 1/1 ('rw [symmDiff_eq_right, and_comm, sup_eq_right, inf_eq_left]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 54.7s, verify 0.1s, in=250, out=2045)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Δ_eq_right_iff ha, Δ_eq_right_iff, sup_eq_right_iff ha]
```

**lean_error:** tail step 1/1 ('rw [Δ_eq_right_iff ha, Δ_eq_right_iff, sup_eq_right_iff ha]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 129.0s, verify 0.1s, in=673, out=5580)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Equiv.eq_symm_apply_iff (Function.Involutive.toPerm (a ∆ ·) (symmDiff_right_involutive a))]
rw [eq_comm]
```

**lean_error:** tail step 1/2 ('rw [Equiv.eq_symm_apply_iff (Function.Involutive.toPerm (a ∆ ·) (symmDiff_right_involutive a))]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 165.1s, verify 0.1s, in=673, out=7196)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
split
intro h
rw h
apply symmDiff_right_involutive
intro h
rw h
apply symmDiff_right_involutive
```

**lean_error:** tail step 1/7 ('split'): tactic 'split' failed

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 180.7s, verify 0.2s, in=673, out=7999)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Iff.intro
  (fun h => by rw [h, symmDiff_right_involutive a])
  (fun h => by rw [h, symmDiff_right_involutive a])
```

**lean_error:** tail step 2/3 ('(fun h => by rw [h, symmDiff_right_involutive a])'): <stdin>:1:1: expected '{' or tactic

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 228.3s, verify 0.1s, in=673, out=10335)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
split
· intro h; rw h; apply symmDiff_right_involutive a
· intro h; rw h; apply symmDiff_right_involutive a
```

**lean_error:** tail step 1/3 ('split'): tactic 'split' failed

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=673, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 1.1s, verify 0.1s, in=673, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Function.Involutive.leftInverse (symmDiff_right_involutive a), eq_comm]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
π : ι → Type u_4
inst✝ : GeneralizedBooleanAlgebra α
a b c d : α
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.8s, verify 0.1s, in=673, out=45)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [← Equiv.toPerm_apply_eq_iff_eq_inv, Equiv.toPerm_eq_right, ←
  symmDiff_right_involutive.toEquiv_eq_cast, eq_comm]
```

**lean_error:** tail step 1/2 ('simp_rw [← Equiv.toPerm_apply_eq_iff_eq_inv, Equiv.toPerm_eq_right, ←'): <stdin>:1:69: unexpected end of input

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.2s, verify 0.1s, in=673, out=61)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Equiv.toFun_eq_coe, Equiv.Perm.coe_involutive_toPerm, Function.Involutive.leftInverse,
  symmDiff_right_involutive, Equiv.Perm.coe_involutive_toPerm_left_inv, eq_comm]
```

**lean_error:** tail step 1/2 ('simp only [Equiv.toFun_eq_coe, Equiv.Perm.coe_involutive_toPerm, Function.Involutive.leftInverse,'): <stdin>:1:97: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 10.5s, verify 0.1s, in=673, out=319)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact (Function.Involutive.toPerm _ (symmDiff_right_involutive _)).eq_iff
```

**lean_error:** tail step 1/1 ('exact (Function.Involutive.toPerm _ (symmDiff_right_involutive _)).eq_iff'): invalid field 'eq_iff', the environment does not contain 'Equiv.Perm.eq_iff'

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 11.0s, verify 0.1s, in=673, out=333)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← eq_comm, Function.Involutive.toPerm _ (symmDiff_right_involutive a), eq_comm]
```

**lean_error:** tail step 1/1 ('rw [← eq_comm, Function.Involutive.toPerm _ (symmDiff_right_involutive a), eq_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 12.3s, verify 0.1s, in=673, out=382)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Function.Involutive.toPerm (a ∆ ·) (symmDiff_right_involutive a).injective.eq_iff, eq_comm]
```

**lean_error:** tail step 1/1 ('rw [Function.Involutive.toPerm (a ∆ ·) (symmDiff_right_involutive a).injective.eq_iff, eq_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 13.6s, verify 0.1s, in=673, out=427)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [symmDiff_right_involutive a.toPerm.toFun_eq_iff, eq_comm]
```

**lean_error:** tail step 1/1 ('rw [symmDiff_right_involutive a.toPerm.toFun_eq_iff, eq_comm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 225.2s, verify 0.1s, in=1041, out=5417)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply (Function.Involutive.toPerm (a ∆ ·) (symmDiff_right_involutive a)).apply_eq_iff_eq_symm_apply.trans eq_comm
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 236.0s, verify 0.2s, in=1041, out=5144)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have f := Function.Involutive.toPerm (a ∆ ·) (symmDiff_right_involutive a)
rw [Equiv.perm.apply_eq_iff_eq_symm_apply, Equiv.perm.self_symm, eq_comm]
```

**lean_error:** tail step 2/2 ('rw [Equiv.perm.apply_eq_iff_eq_symm_apply, Equiv.perm.self_symm, eq_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 236.7s, verify 0.1s, in=1041, out=6019)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
split;
intro h;
rw [h, symmDiff_right_involutive]
```

**lean_error:** tail step 1/3 ('split;'): <stdin>:1:5: expected end of input

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 272.3s, verify 0.2s, in=1041, out=7931)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Iff.intro
· intro h
  rw [h, symmDiff_right_involutive a b]
· intro h
  rw [h, symmDiff_right_involutive a c]
```

**lean_error:** tail step 2/5 ('· intro h'): unsolved goals

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=1041, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.0s, verify 0.1s, in=1041, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Equiv.eq_iff_inv_eq, Function.Involutive.toPerm]
```

**lean_error:** tail step 1/1 ('simp [Equiv.eq_iff_inv_eq, Function.Involutive.toPerm]'): unknown constant 'Equiv.eq_iff_inv_eq'

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.0s, verify 0.1s, in=1041, out=24)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact (Equiv.toPerm _ (symmDiff_right_involutive a)).eq_iff
```

**lean_error:** tail step 1/1 ('exact (Equiv.toPerm _ (symmDiff_right_involutive a)).eq_iff'): unknown constant 'Equiv.toPerm'

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.2s, verify 0.1s, in=1041, out=32)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Function.Involutive.toPerm (a ∆ ·) (symmDiff_right_involutive a), eq_comm]
```

**lean_error:** tail step 1/1 ('simp [Function.Involutive.toPerm (a ∆ ·) (symmDiff_right_involutive a), eq_comm]'): invalid 'simp', proposition expected

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 17.7s, verify 0.1s, in=1041, out=249)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using (Function.Involutive.toPerm _ (symmDiff_right_involutive a)).eq_iff
```

**lean_error:** tail step 1/1 ('simpa using (Function.Involutive.toPerm _ (symmDiff_right_involutive a)).eq_iff'): invalid field 'eq_iff', the environment does not contain 'Equiv.Perm.eq_iff'

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 18.0s, verify 0.1s, in=1041, out=284)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [symmDiff_right_involutive a, Function.Involutive.toPerm, eq_comm]
```

**lean_error:** tail step 1/1 ('simpa [symmDiff_right_involutive a, Function.Involutive.toPerm, eq_comm]'): tactic 'assumption' failed

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 18.1s, verify 0.1s, in=1041, out=326)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using (Function.Involutive.toPerm _ <| symmDiff_right_involutive a).eq_inv_iff.trans eq_comm
```

**lean_error:** tail step 1/1 ('simpa using (Function.Involutive.toPerm _ <| symmDiff_right_involutive a).eq_inv_iff.trans eq_comm'): invalid field 'eq_inv_iff', the environment does not contain 'Equiv.Perm.eq_inv_iff'

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 25.9s, verify 0.1s, in=1041, out=544)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [eq_comm, ← Function.Involutive.toPerm (a ∆ ·) (symmDiff_right_involutive a), eq_comm]
```

**lean_error:** tail step 1/1 ('rw [eq_comm, ← Function.Involutive.toPerm (a ∆ ·) (symmDiff_right_involutive a), eq_comm]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 110.3s, verify 0.1s, in=1065, out=4747)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [(symmDiff_right_involutive a).eq_iff, eq_comm]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 110.7s, verify 0.1s, in=1065, out=4768)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [(symmDiff_right_involutive a).eq_iff]
rw [eq_comm]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 136.7s, verify 0.1s, in=1065, out=5926)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply (symmDiff_right_involutive a).eq_iff
```

**lean_error:** tail step 1/1 ('apply (symmDiff_right_involutive a).eq_iff'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 188.8s, verify 0.1s, in=1065, out=8403)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
split
intro h; rw [h, symmDiff_right_involutive a]
intro h; rw [h, symmDiff_right_involutive a]
```

**lean_error:** tail step 1/3 ('split'): tactic 'split' failed

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=1065, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Function.toPerm_apply, symmDiff_right_involutive]
```

**lean_error:** tail step 1/1 ('simp [Function.toPerm_apply, symmDiff_right_involutive]'): unknown identifier 'Function.toPerm_apply'

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.6s, verify 0.1s, in=1065, out=39)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [← Equiv.Perm.apply_eq_iff_eq (Function.Involutive.toPerm _ (symmDiff_right_involutive a)),
  eq_comm]
```

**lean_error:** tail step 1/2 ('simp_rw [← Equiv.Perm.apply_eq_iff_eq (Function.Involutive.toPerm _ (symmDiff_right_involutive a)),'): <stdin>:1:99: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=1065, out=43)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Equiv.Perm.apply_toPerm, Function.Involutive.toPerm_apply, symmDiff_right_involutive,
  Equiv.Perm.inv_apply, eq_comm]
```

**lean_error:** tail step 1/2 ('simp only [Equiv.Perm.apply_toPerm, Function.Involutive.toPerm_apply, symmDiff_right_involutive,'): <stdin>:1:96: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.1s, verify 0.1s, in=1065, out=54)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Equiv.Perm.toFun_eq_coe, Equiv.Perm.apply_eq_iff_eq_inv, Function.Involutive.inv_eq_iff,
  symmDiff_right_involutive, Equiv.toPerm_inv, eq_comm]
```

**lean_error:** tail step 1/2 ('simp only [Equiv.Perm.toFun_eq_coe, Equiv.Perm.apply_eq_iff_eq_inv, Function.Involutive.inv_eq_iff,'): <stdin>:1:99: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 8.1s, verify 0.1s, in=1065, out=233)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact (symmDiff_right_involutive a).toPerm.eq_comm
```

**lean_error:** tail step 1/1 ('exact (symmDiff_right_involutive a).toPerm.eq_comm'): application type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 12.0s, verify 0.1s, in=1065, out=371)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← symmDiff_of_le ha, (symmDiff_right_involutive a).toPerm.injective.eq_iff, eq_comm, eq_iff_iff]
```

**lean_error:** tail step 1/1 ('rw [← symmDiff_of_le ha, (symmDiff_right_involutive a).toPerm.injective.eq_iff, eq_comm, eq_iff_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 13.4s, verify 0.1s, in=1065, out=409)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_right_involutive a, Function.Involutive.toPerm, eq_comm]
```

**lean_error:** tail step 1/1 ('rw [symmDiff_right_involutive a, Function.Involutive.toPerm, eq_comm]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 13.5s, verify 0.1s, in=1065, out=427)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [symmDiff_eq_iff_sdiff_eq, symmDiff_of_le ha, eq_comm,
  Function.Involutive.toPerm (a ∆ ·) (symmDiff_right_involutive a)]
```

**lean_error:** tail step 1/2 ('rw [symmDiff_eq_iff_sdiff_eq, symmDiff_of_le ha, eq_comm,'): <stdin>:1:57: unexpected end of input; expected ']'
