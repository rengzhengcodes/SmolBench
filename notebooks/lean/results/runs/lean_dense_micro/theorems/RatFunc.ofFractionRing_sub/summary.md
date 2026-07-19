# RatFunc.ofFractionRing_sub   (k=0, 1 tactics total)

file: `Mathlib/FieldTheory/RatFunc.lean`  

**Ground-truth tail (from k):**
```lean
simp only [Sub.sub, HSub.hSub, RatFunc.sub]
```

**True premises at k:** `Sub.sub`, `HSub.hSub`, `RatFunc.sub`

## Verdict matrix

| rung | llama-31-405b-base | llama-lean-bare-micro-r128 |
| --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✓ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 1.0s, verify 0.1s, in=263, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Subtype.mk_eq_mk]
congr
rfl
```

**lean_error:** tail step 1/3 ('rw [Subtype.mk_eq_mk]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=263, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Subtype.mk_eq_mk]
congr
rfl
```

**lean_error:** tail step 1/3 ('rw [Subtype.mk_eq_mk]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=263, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
congr
rw [Subtype.coe_mk]
rfl
```

**lean_error:** tail step 2/3 ('rw [Subtype.coe_mk]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 1.5s, verify 0.1s, in=263, out=50)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Subtype.ext_iff]
rw [Subtype.coe_mk, Subtype.coe_mk, Subtype.coe_mk]
rw [Sub.sub_eq_iff_eq_add]
rw [add_comm]
rw [Subtype.coe_eta]
```

**lean_error:** tail step 1/5 ('rw [Subtype.ext_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 0.5s, verify 0.1s, in=263, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 0.7s, verify 0.1s, in=263, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 0.8s, verify 0.1s, in=263, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=263, out=3)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 2 → **lean_error**  (gen 0.5s, verify 0.1s, in=542, out=8)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact congrArg RatFunc.mk rfl
```

**lean_error:** tail step 1/1 ('exact congrArg RatFunc.mk rfl'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · llama-31-405b-base · rollout 0 → **success**  (gen 0.6s, verify 0.2s, in=542, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
congr
rw [RatFunc.sub]
refl
```

### `hint:2` · llama-31-405b-base · rollout 1 → **lean_error**  (gen 0.7s, verify 0.1s, in=542, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact congrArg RatFunc.mk (Sub.sub p q)
```

**lean_error:** tail step 1/1 ('exact congrArg RatFunc.mk (Sub.sub p q)'): type mismatch

### `hint:2` · llama-31-405b-base · rollout 3 → **lean_error**  (gen 0.9s, verify 0.1s, in=542, out=13)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact congr_arg RatFunc.mk (Sub.sub p q)
```

**lean_error:** tail step 1/1 ('exact congr_arg RatFunc.mk (Sub.sub p q)'): type mismatch

### `hint:2` · llama-lean-bare-micro-r128 · rollout 1 → **lean_error**  (gen 0.6s, verify 0.1s, in=542, out=3)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · llama-lean-bare-micro-r128 · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=542, out=3)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · llama-lean-bare-micro-r128 · rollout 2 → **lean_error**  (gen 1.0s, verify 0.1s, in=542, out=3)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · llama-lean-bare-micro-r128 · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=542, out=3)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch
