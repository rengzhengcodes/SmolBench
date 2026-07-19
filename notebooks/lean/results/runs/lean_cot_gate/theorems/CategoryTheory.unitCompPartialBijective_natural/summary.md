# CategoryTheory.unitCompPartialBijective_natural   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Adjunction/Reflective.lean`  

**Ground-truth tail (from k):**
```lean
rw [← Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural A h, Equiv.symm_apply_apply]
```

**True premises at k:** `Equiv.eq_symm_apply`, `CategoryTheory.unitCompPartialBijective_symm_natural`, `Equiv.symm_apply_apply`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ · ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | · ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✓ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✓ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 195.0s, verify 0.2s, in=355, out=8331)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [←comp_assoc, unitCompPartialBijective_property hB', comp_assoc, unitCompPartialBijective_property hB, comp_assoc]
refl
```

**lean_error:** tail step 1/2 ("rw [←comp_assoc, unitCompPartialBijective_property hB', comp_assoc, unitCompPartialBijective_property hB, comp_assoc]"): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 198.7s, verify 0.3s, in=355, out=8508)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [unitCompPartialBijective, unitCompPartialBijective, F.map_comp]
```

**lean_error:** tail step 1/1 ('rw [unitCompPartialBijective, unitCompPartialBijective, F.map_comp]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 264.9s, verify 0.1s, in=355, out=11513)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
naturality h
  |> congr_arg (fun t => (unitCompPartialBijective A hB f) ≫ t)
  |> forward
  |> rw [← category.assoc]
  |> rw [unitCompPartialBijective_spec]
  |> rw [unitCompPartialBijective_spec]
  |> rw [category.assoc]
```

**lean_error:** tail step 1/7 ('naturality h'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 286.8s, verify 0.2s, in=355, out=12493)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply i.map_injective
rw [functor.map_comp, unitCompPartialBijective_comm, unitCompPartialBijective_comm]
simp
```

**lean_error:** tail step 1/3 ('apply i.map_injective'): tactic 'apply' failed, failed to unify

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=355, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.1s, verify 0.1s, in=355, out=14)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [unitCompPartialBijective_apply]
```

**lean_error:** tail step 1/1 ('simp [unitCompPartialBijective_apply]'): unknown identifier 'unitCompPartialBijective_apply'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 1.2s, verify 0.2s, in=355, out=13)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [unitCompPartialBijective]
```

**final state (truncated):**
```
C : Type u₁
D : Type u₂
E : Type u₃
inst✝³ : Category.{v₁, u₁} C
inst✝² : Category.{v₂, u₂} D
inst✝¹ : Category.{v₃, u₃} E
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.1s, in=355, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [unitCompPartialBijective_apply, assoc]
```

**lean_error:** tail step 1/1 ('simp only [unitCompPartialBijective_apply, assoc]'): unknown identifier 'unitCompPartialBijective_apply'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 9.6s, verify 0.1s, in=355, out=299)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [η_naturality_assoc, Functor.map_comp, ← cancel_mono (η.app A)]
```

**lean_error:** tail step 1/1 ('simp only [η_naturality_assoc, Functor.map_comp, ← cancel_mono (η.app A)]'): unknown identifier 'η_naturality_assoc'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 10.6s, verify 0.1s, in=355, out=319)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [Functor.essImage.unitCompPartialBijective_apply]
```

**lean_error:** tail step 1/1 ('simp [Functor.essImage.unitCompPartialBijective_apply]'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 13.0s, verify 0.1s, in=355, out=394)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [← Functor.map_comp, unit.naturality, unit_comp_partialBijective_apply,
  unitCompPartialBijective]
```

**lean_error:** tail step 1/2 ('simp only [← Functor.map_comp, unit.naturality, unit_comp_partialBijective_apply,'): <stdin>:1:81: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 14.3s, verify 0.1s, in=355, out=435)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [unitCompPartialBijective_apply, unitCompPartialBijective_apply,
  PartialBijective.inv_comp_apply, unit_naturality]
```

**lean_error:** tail step 1/2 ('rw [unitCompPartialBijective_apply, unitCompPartialBijective_apply,'): <stdin>:1:67: unexpected end of input; expected ']'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **incomplete**  (gen 71.1s, verify 0.4s, in=1010, out=2838)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [←Equiv.eq_symm_apply (unitCompPartialBijective A hB')]
rw [unitCompPartialBijective_symm_natural]
simp [Equiv.symm_apply_apply]
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

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 153.0s, verify 0.6s, in=1010, out=6354)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have key := unitCompPartialBijective_symm_natural A h hB hB' (unitCompPartialBijective A hB f)
have h_eq := Equiv.apply_symm_apply (unitCompPartialBijective A hB') (unitCompPartialBijective A hB f ≫ h)
rwa [key] at h_eq
```

**lean_error:** tail step 3/3 ('rwa [key] at h_eq'): tactic 'assumption' failed

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 153.6s, verify 0.3s, in=1010, out=6369)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [←Equiv.eq_symm_apply]
apply unitCompPartialBijective_symm_natural
```

**lean_error:** tail step 2/2 ('apply unitCompPartialBijective_symm_natural'): tactic 'apply' failed, failed to unify

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 167.2s, verify 0.1s, in=1010, out=6978)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply Eq.symm_apply_iff.mp
rw [unitCompPartialBijective_symm_natural A h hB hB' (unitCompPartialBijective A hB f)]
rw [Equiv.symm_apply_apply]
rfl
```

**lean_error:** tail step 1/4 ('apply Eq.symm_apply_iff.mp'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1010, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.6s, verify 0.1s, in=1010, out=24)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural]
```

**lean_error:** tail step 1/1 ('simp [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural]'): simp made no progress

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.8s, verify 0.2s, in=1010, out=31)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.symm_apply_apply]
```

**lean_error:** tail step 1/1 ('rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.symm_apply_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.7s, verify 0.1s, in=1010, out=39)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.symm_apply_apply,
  Equiv.symm_apply_apply]
```

**lean_error:** tail step 1/2 ('rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.symm_apply_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 11.9s, verify 0.1s, in=1010, out=359)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Equiv.eq_symm_apply, CategoryTheory.unitCompPartialBijective_symm_natural,
  Equiv.symm_apply_apply]
```

**lean_error:** tail step 1/2 ('simp only [Equiv.eq_symm_apply, CategoryTheory.unitCompPartialBijective_symm_natural,'): <stdin>:1:85: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 12.7s, verify 0.1s, in=1010, out=380)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.symm_apply_apply]
```

**lean_error:** tail step 1/1 ('simp only [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.symm_apply_apply]'): simp made no progress

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 18.4s, verify 0.1s, in=1010, out=557)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Equiv.eq_symm_apply, CategoryTheory.unitCompPartialBijective_symm_natural,
  Equiv.symm_apply_apply]
```

**lean_error:** tail step 1/2 ('simp only [Equiv.eq_symm_apply, CategoryTheory.unitCompPartialBijective_symm_natural,'): <stdin>:1:85: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 23.9s, verify 0.1s, in=1010, out=762)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural A h hB' hB, Equiv.symm_apply_apply]
```

**lean_error:** tail step 1/1 ("rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural A h hB' hB, Equiv.symm_apply_apply]"): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 192.4s, verify 0.1s, in=1814, out=3278)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply eq_symm_apply.mp,
rw unitCompPartialBijective_symm_natural h,
rw Equiv.symm_apply_apply,
```

**lean_error:** tail step 1/3 ('apply eq_symm_apply.mp,'): <stdin>:1:22: expected end of input

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 234.2s, verify 0.1s, in=1814, out=5951)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Equiv.eq_symm_apply.mp,
rw [Equiv.symm_apply_apply (unitCompPartialBijective A hB') (f ≫ h)],
rw [unitCompPartialBijective_symm_natural A h hB hB' (unitCompPartialBijective A hB f)],
rw [Equiv.symm_apply_apply (unitCompPartialBijective A hB) (unitCompPartialBijective A hB f)],
rfl
```

**lean_error:** tail step 1/5 ('apply Equiv.eq_symm_apply.mp,'): <stdin>:1:28: expected end of input

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 236.1s, verify 0.4s, in=1814, out=5739)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply (Equiv.eq_symm_apply (unitCompPartialBijective A hB')).mp
rw [unitCompPartialBijective_symm_natural A h hB hB' (unitCompPartialBijective A hB f)]
rw [Equiv.symm_apply_apply (unitCompPartialBijective A hB) f]
rfl
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 241.1s, verify 0.3s, in=1814, out=7566)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h1 := unitCompPartialBijective_symm_natural A h hB hB' (unitCompPartialBijective A hB f)
exact Equiv.eq_symm_apply.mp (unitCompPartialBijective A hB') h1
```

**lean_error:** tail step 2/2 ("exact Equiv.eq_symm_apply.mp (unitCompPartialBijective A hB') h1"): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=1814, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.6s, verify 0.1s, in=1814, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [unitCompPartialBijective_symm_natural]
```

**lean_error:** tail step 1/1 ('simp [unitCompPartialBijective_symm_natural]'): simp made no progress

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.8s, verify 0.2s, in=1814, out=31)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.symm_apply_apply]
```

**lean_error:** tail step 1/1 ('rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.symm_apply_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.9s, verify 0.1s, in=1814, out=39)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.symm_apply_apply,
  Equiv.symm_apply_apply]
```

**lean_error:** tail step 1/2 ('rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.symm_apply_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 20.1s, verify 0.1s, in=1814, out=295)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [eq_symm_apply, unitCompPartialBijective_symm_natural, symm_apply_apply]
```

**lean_error:** tail step 1/1 ('simp only [eq_symm_apply, unitCompPartialBijective_symm_natural, symm_apply_apply]'): unknown identifier 'eq_symm_apply'

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 23.1s, verify 0.1s, in=1814, out=343)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← Equiv.eq_symm_apply (unitCompPartialBijective A hB'), Equiv.symm_apply_apply,
  unitCompPartialBijective_symm_natural A h hB hB' f]
```

**lean_error:** tail step 1/2 ("rw [← Equiv.eq_symm_apply (unitCompPartialBijective A hB'), Equiv.symm_apply_apply,"): <stdin>:1:83: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 24.7s, verify 0.1s, in=1814, out=485)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Equiv.eq_symm_apply, CategoryTheory.unitCompPartialBijective_symm_natural,
  Equiv.symm_apply_apply]
```

**lean_error:** tail step 1/2 ('simp only [Equiv.eq_symm_apply, CategoryTheory.unitCompPartialBijective_symm_natural,'): <stdin>:1:85: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 68.9s, verify 0.1s, in=1814, out=2199)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← eq_symm_apply (unitCompPartialBijective A hB'), unitCompPartialBijective_symm_natural,
  symm_apply_apply, symm_apply_apply, eq_comm]
```

**lean_error:** tail step 1/2 ("rw [← eq_symm_apply (unitCompPartialBijective A hB'), unitCompPartialBijective_symm_natural,"): <stdin>:1:92: unexpected end of input; expected ']'

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 102.4s, verify 0.2s, in=1838, out=4153)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply (Equiv.eq_symm_apply (unitCompPartialBijective A hB')).mpr
rw [unitCompPartialBijective_symm_natural A h hB hB' (unitCompPartialBijective A hB f)]
simp only [Equiv.symm_apply_apply]
```

**lean_error:** tail step 1/3 ("apply (Equiv.eq_symm_apply (unitCompPartialBijective A hB')).mpr"): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 108.9s, verify 0.1s, in=1838, out=4448)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply eq_symm_apply.mp
rw [unitCompPartialBijective_symm_natural]
rw [symm_apply_apply]
```

**lean_error:** tail step 1/3 ('apply eq_symm_apply.mp'): unknown identifier 'eq_symm_apply.mp'

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 119.2s, verify 0.1s, in=1838, out=4911)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Equiv.eq_symm_apply (unitCompPartialBijective A hB')].mp
rw [Equiv.symm_apply_apply]
rw [unitCompPartialBijective_symm_natural A h]
rw [Equiv.symm_apply_apply]
```

**lean_error:** tail step 1/4 ("rw [Equiv.eq_symm_apply (unitCompPartialBijective A hB')].mp"): <stdin>:1:57: expected end of input

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 135.0s, verify 0.2s, in=1838, out=5609)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.symm_apply_apply]
```

**lean_error:** tail step 1/1 ('rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.symm_apply_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.6s, verify 0.1s, in=1838, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

**lean_error:** tail step 1/1 ('simp'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.5s, verify 0.1s, in=1838, out=17)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [unitCompPartialBijective_symm_natural]
```

**lean_error:** tail step 1/1 ('simp [unitCompPartialBijective_symm_natural]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.0s, verify 0.2s, in=1838, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.apply_symm_apply]
```

**lean_error:** tail step 1/1 ('rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.apply_symm_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.6s, verify 0.1s, in=1838, out=39)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.symm_apply_apply,
  Equiv.symm_apply_apply]
```

**lean_error:** tail step 1/2 ('rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.symm_apply_apply,'): <stdin>:1:87: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 12.6s, verify 0.1s, in=1838, out=380)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Equiv.eq_symm_apply, CategoryTheory.unitCompPartialBijective_symm_natural, Equiv.symm_apply_apply]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 16.2s, verify 0.1s, in=1838, out=486)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.symm_apply_apply]
```

**lean_error:** tail step 1/1 ('rw [Equiv.eq_symm_apply, unitCompPartialBijective_symm_natural, Equiv.symm_apply_apply]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 16.4s, verify 0.1s, in=1838, out=489)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply eq_symm_apply
simpa using unitCompPartialBijective_symm_natural A h hB hB' _
```

**lean_error:** tail step 1/2 ('apply eq_symm_apply'): unknown identifier 'eq_symm_apply'

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 20.2s, verify 0.1s, in=1838, out=621)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Equiv.eq_symm_apply (unitCompPartialBijective A hB'), unitCompPartialBijective_symm_natural A h hB hB',
  Equiv.symm_apply_apply]
```

**lean_error:** tail step 1/2 ("rw [← Equiv.eq_symm_apply (unitCompPartialBijective A hB'), unitCompPartialBijective_symm_natural A h hB hB',"): <stdin>:1:109: unexpected end of input; expected ']'
