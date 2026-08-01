# CategoryTheory.unitCompPartialBijective_natural   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Adjunction/Reflective.lean`  

**Ground-truth tail (from k):**
```lean
rw [← Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural A h, Equiv.symm_apply_apply]
```

**True premises at k:** `Equiv.eq_symm_apply`, `CategoryTheory.unitCompPartialBijective_symm_natural`, `Equiv.symm_apply_apply`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | · | ✘ |
| `hint:3` | ✘ | · | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.2s, in=379, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [unitCompPartialBijective_naturality_left]
simp
```

**lean_error:** tail step 1/2 ('rw [unitCompPartialBijective_naturality_left]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 3.9s, verify 0.3s, in=356, out=68)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [unitCompPartialBijective, unitCompPartialBijective, ←category.assoc, ←category.assoc, unitCompPartialBijective_id]
simp only [category.assoc, ←Functor.map_comp, IsIso.hom_inv_id_assoc]
rw [←NatTrans.naturality]
simp only [category.id_comp]
```

**lean_error:** tail step 1/4 ('rw [unitCompPartialBijective, unitCompPartialBijective, ←category.assoc, ←category.assoc, unitCompPartialBijective_id]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 4.4s, verify 0.1s, in=368, out=229)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply unitCompPartialBijective_naturality
```

**lean_error:** tail step 1/1 ('apply unitCompPartialBijective_naturality'): unknown identifier 'unitCompPartialBijective_naturality'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.2s, in=1034, out=57)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Equiv.eq_symm_apply (unitCompPartialBijective A hB')]
rw [CategoryTheory.unitCompPartialBijective_symm_natural A h hB hB']
rw [Equiv.symm_apply_apply (unitCompPartialBijective A hB)]
```

**lean_error:** tail step 1/3 ("rw [Equiv.eq_symm_apply (unitCompPartialBijective A hB')]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 0.8s, verify 2.7s, in=1012, out=46)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Equiv.eq_symm_apply (unitCompPartialBijective A hB')]
rw [unitCompPartialBijective_symm_natural]
simp only [Equiv.symm_apply_apply, Category.assoc]
```

**final state (truncated):**
```
case hB
C : Type u₁
D : Type u₂
E : Type u₃
inst✝³ : Category.{v₁, u₁} C
inst✝² : Category.{v₂, u₂} D
...
```

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 137.5s, verify 0.3s, in=1023, out=8501)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Eq.symm
apply unitCompPartialBijective_symm_natural
exact hB
exact hB'
exact (unitCompPartialBijective A hB).symm f
```

**lean_error:** tail step 2/5 ('apply unitCompPartialBijective_symm_natural'): tactic 'apply' failed, failed to unify

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.4s, verify 0.2s, in=1831, out=57)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Equiv.eq_symm_apply (unitCompPartialBijective A hB')]
rw [CategoryTheory.unitCompPartialBijective_symm_natural A h hB hB']
rw [Equiv.symm_apply_apply (unitCompPartialBijective A hB)]
```

**lean_error:** tail step 1/3 ("rw [Equiv.eq_symm_apply (unitCompPartialBijective A hB')]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **incomplete**  (gen 3.5s, verify 0.4s, in=1804, out=44)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← Equiv.eq_symm_apply (unitCompPartialBijective A hB')]
rw [CategoryTheory.unitCompPartialBijective_symm_natural]
simp only [Equiv.symm_apply_apply]
```

**final state (truncated):**
```
case hB
C : Type u₁
D : Type u₂
E : Type u₃
inst✝³ : Category.{v₁, u₁} C
inst✝² : Category.{v₂, u₂} D
...
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.6s, in=1820, out=40)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Eq.trans
apply Eq.symm
apply unitCompPartialBijective_symm_natural
apply Eq.trans
apply Eq.symm
apply symm_apply_apply
```

**lean_error:** tail step 3/6 ('apply unitCompPartialBijective_symm_natural'): tactic 'apply' failed, failed to unify

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.2s, in=1859, out=57)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Equiv.eq_symm_apply (unitCompPartialBijective A hB')]
rw [CategoryTheory.unitCompPartialBijective_symm_natural A h hB hB']
rw [Equiv.symm_apply_apply (unitCompPartialBijective A hB)]
```

**lean_error:** tail step 1/3 ("rw [Equiv.eq_symm_apply (unitCompPartialBijective A hB')]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 4.3s, verify 0.1s, in=1929, out=63)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Equiv.symm_apply_apply (unitCompPartialBijective A hB'), ←
  Equiv.symm_apply_apply (unitCompPartialBijective A hB)]
symm
rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural]
rfl
```

**lean_error:** tail step 1/5 ("rw [← Equiv.symm_apply_apply (unitCompPartialBijective A hB'), ←"): <stdin>:1:64: unexpected end of input

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.7s, in=1848, out=40)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Eq.trans
apply Eq.symm
apply unitCompPartialBijective_symm_natural
apply Eq.trans
apply Eq.symm
apply symm_apply_apply
```

**lean_error:** tail step 3/6 ('apply unitCompPartialBijective_symm_natural'): tactic 'apply' failed, failed to unify
