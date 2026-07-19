# CategoryTheory.Limits.pullback_map_eq_pullbackFstFstIso_inv   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/Diagonal.lean`  

**Ground-truth tail (from k):**
```lean
simp only [pullbackFstFstIso_inv, lift_snd_assoc, lift_fst]
```

**True premises at k:** `CategoryTheory.Limits.pullbackFstFstIso_inv`, `CategoryTheory.Limits.pullback.lift_snd_assoc`, `CategoryTheory.Limits.pullback.lift_fst`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | · ✘ ✘ ✘ | ✓ ✓ ✓ ✓ | ✓ ✓ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✘ | ✓ ✓ ✓ ✓ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✘ | ✓ ✓ ✓ ✓ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **incomplete**  (gen 108.5s, verify 0.4s, in=423, out=3987)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
simp [map, pullbackFstFstIso]
```

**final state (truncated):**
```
case h₁
C : Type u_1
inst✝² : Category.{u_2, u_1} C
X✝ Y✝ Z : C
inst✝¹ : HasPullbacks C
X Y S X' Y' S' : C
...
```

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 178.0s, verify 0.1s, in=423, out=6792)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
hom_ext
simp [map_fst, map_snd]
simp [map_snd, map_fst]
```

**lean_error:** tail step 1/3 ('hom_ext'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 190.9s, verify 0.3s, in=423, out=7440)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
simp [map_fst, pullbackFstFstIso_comp_snd, ← assoc]
simp [map_snd, pullbackFstFstIso_comp_fst, ← assoc]
```

**lean_error:** tail step 2/3 ('simp [map_fst, pullbackFstFstIso_comp_snd, ← assoc]'): unknown identifier 'map_fst'

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 191.6s, verify 0.2s, in=423, out=7471)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [←iso.inv_comp_eq]
simp only [category.assoc]
rw [pullbackFstFstIso_hom_comp_fst, pullbackFstFstIso_hom_comp_snd]
simp [*]
```

**lean_error:** tail step 1/4 ('rw [←iso.inv_comp_eq]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 0.7s, verify 0.1s, in=423, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [map]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.8s, verify 0.1s, in=423, out=9)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [map]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.3s, verify 0.1s, in=423, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pullbackFstFstIso]
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.9s, verify 0.1s, in=423, out=6)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 9.6s, verify 0.1s, in=423, out=263)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 11.3s, verify 0.1s, in=423, out=319)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 30.7s, verify 0.1s, in=423, out=947)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [pullback.hom_ext, assoc, Iso.inv_hom_id, pullback.condition,
  pullbackFstFstIso_hom_snd, pullbackFstFstIso_hom_fst, map_fst, map_snd,
  pullbackFstFstIso_inv_snd, pullbackFstFstIso_inv_fst, Iso.hom_inv_id, pullback.condition]
```

**lean_error:** tail step 1/3 ('simp only [pullback.hom_ext, assoc, Iso.inv_hom_id, pullback.condition,'): <stdin>:1:71: unexpected end of input; expected ']'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 37.7s, verify 0.1s, in=423, out=1180)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [pullbackFstFstIso_hom, map_fst]
```

**lean_error:** tail step 1/1 ('simp [pullbackFstFstIso_hom, map_fst]'): unknown identifier 'map_fst'

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 109.9s, verify 0.4s, in=870, out=4042)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply pullback.hom_ext
split
exact pullback.lift_fst _ _ _
exact pullback.lift_fst _ _ _
```

**lean_error:** tail step 2/4 ('split'): tactic 'split' failed

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 167.5s, verify 0.4s, in=870, out=6342)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext
apply pullback.lift_fst
apply pullback.lift_snd_assoc
```

**lean_error:** tail step 2/3 ('apply pullback.lift_fst'): tactic 'apply' failed, failed to unify

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 184.4s, verify 0.6s, in=870, out=7124)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply pullback.hom_ext
rw [pullback.lift_fst]
rw [pullback.lift_snd_assoc]
```

**lean_error:** tail step 3/3 ('rw [pullback.lift_snd_assoc]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 191.5s, verify 0.1s, in=870, out=7465)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
ext; apply pullback.lift_fst
```

**lean_error:** tail step 1/1 ('ext; apply pullback.lift_fst'): <stdin>:1:3: expected end of input

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.1s, verify 0.2s, in=870, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [map, pullbackFstFstIso_inv]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.5s, verify 0.1s, in=870, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [← Iso.eq_inv_comp, pullback.lift_fst]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.2s, verify 0.1s, in=870, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [pullback.map, pullbackFstFstIso_inv]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.3s, verify 0.1s, in=870, out=57)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [← cancel_mono i₃, assoc, pullbackFstFstIso_inv, pullback.lift_fst,
  pullback.map_fst, pullback.lift_snd_assoc, Category.assoc, Iso.inv_hom_id, comp_id]
```

**lean_error:** tail step 1/2 ('simp only [← cancel_mono i₃, assoc, pullbackFstFstIso_inv, pullback.lift_fst,'): <stdin>:1:77: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 10.2s, verify 0.1s, in=870, out=282)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [pullback.lift_fst, e₁]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 14.5s, verify 0.1s, in=870, out=423)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [pullback.lift_fst]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 14.7s, verify 0.1s, in=870, out=429)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [map, pullbackFstFstIso_inv, pullback.lift_snd_assoc, pullback.lift_fst]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 20.7s, verify 0.1s, in=870, out=634)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [map, pullbackFstFstIso_inv, pullback.lift_snd_assoc, pullback.lift_fst]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 221.3s, verify 0.1s, in=1006, out=4976)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
ext1; apply pullback.lift_fst
```

**lean_error:** tail step 1/1 ('ext1; apply pullback.lift_fst'): <stdin>:1:4: expected end of input

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 242.5s, verify 0.1s, in=1006, out=5695)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw pullbackFstFstIso_inv
apply pullback.hom_ext
apply pullback.lift_fst
apply pullback.lift_snd_assoc
```

**lean_error:** tail step 1/4 ('rw pullbackFstFstIso_inv'): <stdin>:1:3: expected '['

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 243.9s, verify 0.1s, in=1006, out=5706)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply pullback.hom_ext;
  rw pullback.lift_fst
```

**lean_error:** tail step 1/2 ('apply pullback.hom_ext;'): <stdin>:1:22: expected end of input

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 311.9s, verify 0.2s, in=1006, out=6592)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [←pullback.lift_fst, ←pullback.lift_snd_assoc]
```

**lean_error:** tail step 1/1 ('rw [←pullback.lift_fst, ←pullback.lift_snd_assoc]'): tactic 'rewrite' failed, pattern is a metavariable

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.7s, verify 0.1s, in=1006, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [map, pullbackFstFstIso_inv]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.9s, verify 0.1s, in=1006, out=19)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [← Iso.eq_inv_comp, pullback.lift_fst]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.1s, verify 0.1s, in=1006, out=20)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [pullback.map, pullbackFstFstIso_inv]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.4s, verify 0.1s, in=1006, out=45)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [← cancel_mono f', Category.assoc, pullbackFstFstIso_inv, pullback.lift_fst,
pullback.lift_snd, ← e₁, ← e₂]
```

**lean_error:** tail step 1/2 ("simp only [← cancel_mono f', Category.assoc, pullbackFstFstIso_inv, pullback.lift_fst,"): <stdin>:1:86: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 17.2s, verify 0.6s, in=1006, out=222)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [pullbackFstFstIso_inv, pullback.lift_snd_assoc, pullback.lift_fst]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 20.2s, verify 0.1s, in=1006, out=348)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [pullback.lift_snd_assoc, pullback.lift_fst]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 20.5s, verify 0.1s, in=1006, out=359)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [pullback.lift_fst, pullback.lift_snd_assoc, pullbackFstFstIso_inv]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 24.9s, verify 0.1s, in=1006, out=476)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [pullback.lift_snd_assoc, pullbackFstFstIso_inv, pullback.lift_fst]
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 102.2s, verify 0.1s, in=1030, out=3763)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply pullback.hom_ext,
  rw [pullback.lift_fst, category.assoc, category.assoc, pullbackFstFstIso_inv_fst, category.id_comp],
  rw [pullback.lift_snd_assoc, category.assoc, pullbackFstFstIso_inv_snd, category.id_comp]
```

**lean_error:** tail step 1/3 ('apply pullback.hom_ext,'): <stdin>:1:22: expected end of input

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 171.1s, verify 0.3s, in=1030, out=6494)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply pullback.hom_ext
· rw [pullback.lift_fst, pullback.lift_fst]
· rw [pullback.lift_snd_assoc, pullback.lift_snd_assoc]
```

**lean_error:** tail step 2/3 ('· rw [pullback.lift_fst, pullback.lift_fst]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 189.5s, verify 0.4s, in=1030, out=7373)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply pullback.hom_ext
apply pullback.lift_fst
apply pullback.lift_snd_assoc
```

**lean_error:** tail step 2/3 ('apply pullback.lift_fst'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 200.1s, verify 0.1s, in=1030, out=7882)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply Pullback.hom_ext; simp [pullback.lift_fst, pullback.lift_snd_assoc]
```

**lean_error:** tail step 1/1 ('apply Pullback.hom_ext; simp [pullback.lift_fst, pullback.lift_snd_assoc]'): <stdin>:1:22: expected end of input

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 0.9s, verify 0.1s, in=1030, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [map]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.0s, verify 0.1s, in=1030, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [map, pullbackFstFstIso_inv]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.4s, verify 0.1s, in=1030, out=19)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [← Iso.eq_inv_comp, pullback.lift_fst]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.6s, verify 0.1s, in=1030, out=20)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [pullback.map, pullbackFstFstIso_inv]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 9.7s, verify 0.1s, in=1030, out=264)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [pullback.lift_fst, pullback.lift_snd_assoc, pullbackFstFstIso_inv]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 10.9s, verify 0.1s, in=1030, out=304)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [← Category.assoc, pullbackFstFstIso_inv, pullback.lift_fst] <;> aesop_cat
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 15.1s, verify 0.1s, in=1030, out=442)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [map, pullbackFstFstIso_inv, pullback.lift_fst, pullback.lift_snd_assoc]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 17.8s, verify 0.2s, in=1030, out=517)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
ext <;> simp [pullback.lift_fst, pullback.lift_snd_assoc, pullbackFstFstIso_inv]
```
