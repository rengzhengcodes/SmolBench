# CategoryTheory.IsPushout.of_isBilimit   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Limits/Shapes/CommSq.lean`  

**Ground-truth tail (from k):**
```lean
convert IsPushout.of_is_coproduct' h.isColimit HasZeroObject.zeroIsInitial
```

**True premises at k:** `CategoryTheory.IsPushout.of_is_coproduct'`, `CategoryTheory.Limits.HasZeroObject.zeroIsInitial`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 188.8s, verify 0.3s, in=291, out=7383)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply IsPushout.mk _ _
  intro Q k l w
  use b.universal k l
  simp
  simp
  intro m' hm1 hm2
  apply b.hom_ext
  exact hm1
  exact hm2
```

**lean_error:** tail step 2/9 ('intro Q k l w'): tactic 'introN' failed, insufficient number of binders

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 205.6s, verify 0.1s, in=291, out=8095)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
  · rw [comp_zero, comp_zero]
  · intro Q x y h
    use h.is_colimit.desc (BinaryCofan.mk x y)
    · simp
    apply h.is_colimit.uniq
```

**lean_error:** tail step 1/6 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 210.1s, verify 0.1s, in=291, out=8283)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· rw [zero_comp, zero_comp]
· intros Q x y h_comm
  use h.is_colimit.desc (BinaryCocone.mk x y)
  split
  · exact h.is_colimit.fac _ WalkingBinaryCofan.left
  · exact h.is_colimit.fac _ WalkingBinaryCofan.right
  · intro e' he1 he2
    apply h.is_colimit.hom_ext
    constructor
    exact he1
    exact he2
```

**lean_error:** tail step 1/12 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 255.5s, verify 0.1s, in=291, out=10319)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
apply zero_comp
apply h.2
```

**lean_error:** tail step 1/3 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.2s, verify 0.1s, in=291, out=20)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IsPushout.of_isColimit_zero _ _ _ h.colimit
```

**lean_error:** tail step 1/1 ('exact IsPushout.of_isColimit_zero _ _ _ h.colimit'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.5s, verify 0.1s, in=291, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact isPushout_of_isColimit_of_isColimit_coconeAtZero b.isColimit
```

**lean_error:** tail step 1/1 ('exact isPushout_of_isColimit_of_isColimit_coconeAtZero b.isColimit'): unknown identifier 'isPushout_of_isColimit_of_isColimit_coconeAtZero'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=291, out=26)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.isPushout_of_isZero_left_of_isZero_right _ _ zeroIsZero zeroIsZero
```

**lean_error:** tail step 1/1 ('exact h.isPushout_of_isZero_left_of_isZero_right _ _ zeroIsZero zeroIsZero'): invalid field 'isPushout_of_isZero_left_of_isZero_right', the environment does not contain 'CategoryTheory.Limits.BinaryBicone.IsBilimit.isPushout_of_isZero_left_of_isZero_right'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.9s, verify 0.1s, in=291, out=54)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IsPushout.of_ι_inr_eq_zero _ _ (h.eq_of_w _ (b.fac _ WalkingBiconePoint.left)
  (b.fac _ WalkingBiconePoint.right).trans (zero_comp _).symm)
```

**lean_error:** tail step 1/2 ('exact IsPushout.of_ι_inr_eq_zero _ _ (h.eq_of_w _ (b.fac _ WalkingBiconePoint.left)'): <stdin>:1:83: unexpected end of input; expected ')', ',' or ':'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 6.1s, verify 0.1s, in=291, out=160)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.isPushout
```

**lean_error:** tail step 1/1 ('exact h.isPushout'): invalid field 'isPushout', the environment does not contain 'CategoryTheory.Limits.BinaryBicone.IsBilimit.isPushout'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 7.9s, verify 0.1s, in=291, out=214)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact b.IsBilimit.isPushout_of_inl_of_inr
```

**lean_error:** tail step 1/1 ('exact b.IsBilimit.isPushout_of_inl_of_inr'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 9.7s, verify 0.1s, in=291, out=270)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using h.isPushout
```

**lean_error:** tail step 1/1 ('simpa using h.isPushout'): invalid field 'isPushout', the environment does not contain 'CategoryTheory.Limits.BinaryBicone.IsBilimit.isPushout'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 11.1s, verify 0.1s, in=291, out=321)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact h.isColimit.isPushout_of_isColimit_of_isColimit
```

**lean_error:** tail step 1/1 ('exact h.isColimit.isPushout_of_isColimit_of_isColimit'): invalid field 'isPushout_of_isColimit_of_isColimit', the environment does not contain 'CategoryTheory.Limits.IsColimit.isPushout_of_isColimit_of_isColimit'

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 126.5s, verify 0.1s, in=692, out=5041)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply CategoryTheory.IsPushout.of_is_coproduct' h.as_colimit (zeroIsInitial)
```

**lean_error:** tail step 1/1 ("apply CategoryTheory.IsPushout.of_is_coproduct' h.as_colimit (zeroIsInitial)"): invalid field 'as_colimit', the environment does not contain 'CategoryTheory.Limits.BinaryBicone.IsBilimit.as_colimit'

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 127.8s, verify 0.1s, in=692, out=5091)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply CategoryTheory.IsPushout.of_is_coproduct' h (CategoryTheory.Limits.HasZeroObject.zeroIsInitial)
```

**lean_error:** tail step 1/1 ("apply CategoryTheory.IsPushout.of_is_coproduct' h (CategoryTheory.Limits.HasZeroObject.zeroIsInitial)"): application type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 178.2s, verify 0.1s, in=692, out=6974)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply IsPushout.of_is_coproduct' h.2 (zeroIsInitial C)
```

**lean_error:** tail step 1/1 ("apply IsPushout.of_is_coproduct' h.2 (zeroIsInitial C)"): unknown identifier 'zeroIsInitial'

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 196.9s, verify 0.1s, in=692, out=7723)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact of_is_coproduct' h.isColimit zeroIsInitial
```

**lean_error:** tail step 1/1 ("exact of_is_coproduct' h.isColimit zeroIsInitial"): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.3s, verify 0.1s, in=692, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial"): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.5s, verify 0.2s, in=692, out=26)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isCoproduct HasZeroObject.zeroIsInitial
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isCoproduct HasZeroObject.zeroIsInitial"): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.0s, verify 0.1s, in=692, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial.{v₁, u₁} C)
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial.{v₁, u₁} C)"): type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.3s, verify 0.1s, in=692, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial"): type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 9.4s, verify 0.1s, in=692, out=260)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply of_is_coproduct' h.is_colimit (zeroIsInitial C)
```

**lean_error:** tail step 1/1 ("apply of_is_coproduct' h.is_colimit (zeroIsInitial C)"): invalid field 'is_colimit', the environment does not contain 'CategoryTheory.Limits.BinaryBicone.IsBilimit.is_colimit'

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 9.5s, verify 0.1s, in=692, out=266)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial C)
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial C)"): type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 9.9s, verify 0.2s, in=692, out=272)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact of_is_coproduct' h.isCofork zeroIsInitial
```

**lean_error:** tail step 1/1 ("exact of_is_coproduct' h.isCofork zeroIsInitial"): type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 13.9s, verify 0.1s, in=692, out=412)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply of_is_coproduct' h.isColimit (zeroIsInitial C)
```

**lean_error:** tail step 1/1 ("apply of_is_coproduct' h.isColimit (zeroIsInitial C)"): unknown identifier 'zeroIsInitial'

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 261.8s, verify 0.1s, in=1011, out=5547)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply of_is_coproduct' h zeroIsInitial
```

**lean_error:** tail step 1/1 ("apply of_is_coproduct' h zeroIsInitial"): application type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 275.5s, verify 0.1s, in=1011, out=6637)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply CategoryTheory.IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial)
```

**lean_error:** tail step 1/1 ("apply CategoryTheory.IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial)"): unknown identifier 'zeroIsInitial'

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 304.1s, verify 0.2s, in=1011, out=7299)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply CategoryTheory.IsPushout.of_is_coproduct'
exact h.colimit_cofan
exact HasZeroObject.zeroIsInitial Z
```

**lean_error:** tail step 1/3 ("apply CategoryTheory.IsPushout.of_is_coproduct'"): tactic 'apply' failed, failed to unify

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 338.3s, verify 0.1s, in=1011, out=9530)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply CategoryTheory.IsPushout.of_is_coproduct' h (zeroIsInitial C)
```

**lean_error:** tail step 1/1 ("apply CategoryTheory.IsPushout.of_is_coproduct' h (zeroIsInitial C)"): application type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.4s, verify 0.1s, in=1011, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial"): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.6s, verify 0.2s, in=1011, out=23)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isCoproduct zeroIsInitial
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isCoproduct zeroIsInitial"): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.7s, verify 0.1s, in=1011, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial"): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.9s, verify 0.2s, in=1011, out=32)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial.{v₁, u₁} C)
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial.{v₁, u₁} C)"): type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 15.7s, verify 0.1s, in=1011, out=263)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply of_is_coproduct' h.isColimit zeroIsInitial
```

**lean_error:** tail step 1/1 ("apply of_is_coproduct' h.isColimit zeroIsInitial"): unknown identifier 'zeroIsInitial'

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 16.4s, verify 0.1s, in=1011, out=344)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact of_is_coproduct' h.isColimit (zeroIsInitial : IsInitial (0 : C))
```

**lean_error:** tail step 1/1 ("exact of_is_coproduct' h.isColimit (zeroIsInitial : IsInitial (0 : C))"): type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 17.5s, verify 0.1s, in=1011, out=348)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsPushout.of_is_coproduct' h.isCoproduct zeroIsInitial
```

**lean_error:** tail step 1/1 ("apply IsPushout.of_is_coproduct' h.isCoproduct zeroIsInitial"): invalid field 'isCoproduct', the environment does not contain 'CategoryTheory.Limits.BinaryBicone.IsBilimit.isCoproduct'

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 21.6s, verify 0.1s, in=1011, out=461)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial _ : IsInitial (0 : C))
```

**lean_error:** tail step 1/1 ("apply IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial _ : IsInitial (0 : C))"): unknown identifier 'zeroIsInitial'

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 107.2s, verify 0.1s, in=1036, out=4310)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply CategoryTheory.IsPushout.of_is_coproduct' h.bicofan.is_colimit (zeroIsInitial C)
```

**lean_error:** tail step 1/1 ("apply CategoryTheory.IsPushout.of_is_coproduct' h.bicofan.is_colimit (zeroIsInitial C)"): invalid field 'bicofan', the environment does not contain 'CategoryTheory.Limits.BinaryBicone.IsBilimit.bicofan'

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 113.4s, verify 0.1s, in=1036, out=4544)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply of_is_coproduct' h.isColimit (zeroIsInitial C)
```

**lean_error:** tail step 1/1 ("apply of_is_coproduct' h.isColimit (zeroIsInitial C)"): unknown identifier 'zeroIsInitial'

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 130.2s, verify 0.1s, in=1036, out=5183)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply of_is_coproduct' h (zeroIsInitial)
```

**lean_error:** tail step 1/1 ("apply of_is_coproduct' h (zeroIsInitial)"): application type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 295.2s, verify 0.1s, in=1036, out=12043)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
of_is_coproduct' _ (zeroIsInitial : IsInitial (0 : C))
exact h.is_colimit
```

**lean_error:** tail step 1/2 ("of_is_coproduct' _ (zeroIsInitial : IsInitial (0 : C))"): <stdin>:1:1: unknown tactic

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.8s, verify 0.2s, in=1036, out=29)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.colimitCocone.isColimit (zeroIsInitial C)
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.colimitCocone.isColimit (zeroIsInitial C)"): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.1s, verify 0.2s, in=1036, out=33)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' (Limits.IsColimit.of_isBilimit h) (zeroIsInitial C)
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' (Limits.IsColimit.of_isBilimit h) (zeroIsInitial C)"): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 3.1s, verify 0.1s, in=1036, out=22)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isColimit zeroIsInitial"): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 71.2s, verify 0.1s, in=1036, out=31)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial.{v₁, u₁} _)
```

**lean_error:** tail step 1/1 ("exact IsPushout.of_is_coproduct' h.isColimit (zeroIsInitial.{v₁, u₁} _)"): type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 7.8s, verify 0.1s, in=1036, out=204)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsPushout.of_is_coproduct' h.is_colimit zeroIsInitial
```

**lean_error:** tail step 1/1 ("apply IsPushout.of_is_coproduct' h.is_colimit zeroIsInitial"): invalid field 'is_colimit', the environment does not contain 'CategoryTheory.Limits.BinaryBicone.IsBilimit.is_colimit'

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 9.1s, verify 0.1s, in=1036, out=248)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply of_is_coproduct' (BinaryCofan.isColimit.mk _ h) zeroIsInitial
```

**lean_error:** tail step 1/1 ("apply of_is_coproduct' (BinaryCofan.isColimit.mk _ h) zeroIsInitial"): invalid field notation, type is not of the form (C ...) where C is a constant

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 9.8s, verify 0.1s, in=1036, out=271)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply IsPushout.of_is_coproduct' h.is_colimit HasZeroObject.zeroIsInitial
```

**lean_error:** tail step 1/1 ("apply IsPushout.of_is_coproduct' h.is_colimit HasZeroObject.zeroIsInitial"): invalid field 'is_colimit', the environment does not contain 'CategoryTheory.Limits.BinaryBicone.IsBilimit.is_colimit'

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 10.5s, verify 0.1s, in=1036, out=299)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply of_is_coproduct' h.bicoprodIsColimit zeroIsInitial
```

**lean_error:** tail step 1/1 ("apply of_is_coproduct' h.bicoprodIsColimit zeroIsInitial"): invalid field 'bicoprodIsColimit', the environment does not contain 'CategoryTheory.Limits.BinaryBicone.IsBilimit.bicoprodIsColimit'
