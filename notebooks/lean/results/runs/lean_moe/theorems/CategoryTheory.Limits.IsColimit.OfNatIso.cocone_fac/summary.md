# CategoryTheory.Limits.IsColimit.OfNatIso.cocone_fac   (k=2, 3 tactics total)

file: `Mathlib/CategoryTheory/Limits/IsLimit.lean`  

**Ground-truth tail (from k):**
```lean
apply (coconeOfHom_fac _ _).symm
```

**True premises at k:** `CategoryTheory.Limits.IsColimit.OfNatIso.coconeOfHom_fac`, `Eq.symm`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✓ | ✘ | ✘ |
| `noise:3` | ✓ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.8s, verify 0.1s, in=425, out=640)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 209.6s, verify 0.1s, in=374, out=23375)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext <;> simp [Cocone.extend, coconeOfHom] <;> aesop
```

**lean_error:** tail step 1/1 ('ext <;> simp [Cocone.extend, coconeOfHom] <;> aesop'): no applicable extensionality theorem found for

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 23.0s, verify 0.1s, in=363, out=514)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [coconeOfHom]
```

**final state (truncated):**
```
J : Type u₁
inst✝² : Category.{v₁, u₁} J
K : Type u₂
inst✝¹ : Category.{v₂, u₂} K
C : Type u₃
inst✝ : Category.{v₃, u₃} C
...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.0s, verify 0.2s, in=1179, out=897)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [coconeOfHom_fac]
rfl
```

**lean_error:** tail step 1/2 ('rw [coconeOfHom_fac]'): tactic 'rewrite' failed, motive is not type correct

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 82.9s, verify 0.1s, in=1161, out=8065)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact Eq.symm (coconeOfHom_fac (homOfCocone h s))
```

**lean_error:** tail step 1/1 ('exact Eq.symm (coconeOfHom_fac (homOfCocone h s))'): application type mismatch

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 24.8s, verify 0.3s, in=1103, out=587)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← coconeOfHom_fac (homOfCocone h s)]
```

**lean_error:** tail step 1/1 ('rw [← coconeOfHom_fac (homOfCocone h s)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 10.8s, verify 0.5s, in=4767, out=1655)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← coconeOfHom_fac]
exact coconeOfHom_homOfCocone h s
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 118.1s, verify 0.2s, in=4807, out=12153)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Eq.symm
exact coconeOfHom_fac _
```

**lean_error:** tail step 2/2 ('exact coconeOfHom_fac _'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 23.5s, verify 0.1s, in=4719, out=562)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact Eq.symm (coconeOfHom_fac (homOfCocone h s))
```

**lean_error:** tail step 1/1 ('exact Eq.symm (coconeOfHom_fac (homOfCocone h s))'): application type mismatch

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.1s, verify 0.1s, in=4385, out=712)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using (coconeOfHom_fac (h:=h) (f:=homOfCocone h s)).symm
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 92.0s, verify 0.2s, in=5353, out=9051)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [coconeOfHom_fac]
<;> rfl
```

**lean_error:** tail step 1/2 ('rw [coconeOfHom_fac]'): tactic 'rewrite' failed, motive is not type correct

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 23.7s, verify 1.0s, in=4672, out=581)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← CategoryTheory.Limits.IsColimit.OfNatIso.coconeOfHom_fac (homOfCocone h s)]
```

**lean_error:** tail step 1/1 ('rw [← CategoryTheory.Limits.IsColimit.OfNatIso.coconeOfHom_fac (homOfCocone h s)]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
