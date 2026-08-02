# CategoryTheory.Subobject.map_pullback   (k=13, 14 tactics total)

file: `Mathlib/CategoryTheory/Subobject/Basic.lean`  

**Ground-truth tail (from k):**
```lean
apply PullbackCone.IsLimit.lift_snd
```

**True premises at k:** `CategoryTheory.Limits.PullbackCone.IsLimit.lift_snd`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✓ |
| `hint:2` | ✓ | ✓ | ✘ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 15.7s, verify 0.5s, in=462, out=3277)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using
  t.fac
    (PullbackCone.mk (pullback.fst ≫ MonoOver.arrow a) pullback.snd
      (by
        simpa [Category.assoc] using pullback.condition))
    WalkingPullback.right
```

**lean_error:** tail step 1/6 ('simpa using'): <stdin>:1:11: unexpected end of input

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 244.2s, verify 0.1s, in=415, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
def PullbackCone.mk {X Y Z : C} {f : X → Y} {g : Z → Y} (h : f = g) : PullbackCone f g :=
  ⟨X, fun x => x, fun z => z, by simp [h]⟩
```

**lean_error:** tail step 1/2 ('def PullbackCone.mk {X Y Z : C} {f : X → Y} {g : Z → Y} (h : f = g) : PullbackCone f g :='): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 7.0s, verify 0.6s, in=404, out=618)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply PullbackCone.IsLimit.lift_snd
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 10.5s, verify 0.6s, in=1052, out=2020)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using (PullbackCone.IsLimit.lift_snd t (pullback.fst ≫ a.arrow) pullback.snd _)
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 153.0s, verify 0.6s, in=1032, out=20501)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply PullbackCone.IsLimit.lift_snd
<;> simp_all [PullbackCone.snd]
<;> try assump
<;> try aesop
<;>
  (try
    {
      intros
      <;>
      (try
        {
          simp_all [MonoOver.arrow]
          <;>
          try
            {
              aesop
            }
        })
      <;>
      try
        {
          aesop
        }
    })
  <;>
  try
    {
      simp_all [comm]
      <;>
      try
        {
          aesop
        }
    }
```

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 11.8s, verify 0.1s, in=993, out=1152)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [PullbackCone.IsLimit.lift_snd]
```

**lean_error:** tail step 1/1 ('simp [PullbackCone.IsLimit.lift_snd]'): simp made no progress

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 29.5s, verify 0.2s, in=1288, out=6423)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa using
  (PullbackCone.IsLimit.lift_snd (t:=t)
    (h:=pullback.fst ≫ a.arrow) (k:=pullback.snd)
    (by
      rw [Category.assoc, ← comm, pullback.condition_assoc]))
```

**lean_error:** tail step 1/5 ('simpa using'): <stdin>:1:11: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 142.7s, verify 0.1s, in=1276, out=19329)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ : PullbackCone.IsLimit.lift t (pullback.fst ≫ MonoOver.arrow a) pullback.snd _ ≫ g = pullback.snd := by
  have h₂ : PullbackCone.IsLimit.lift t (pullback.fst ≫ MonoOver.arrow a) pullback.snd _ ≫ (PullbackCone.mk f g comm).snd = pullback.snd := by
    apply PullbackCone.IsLimit.lift_snd
    <;>
    (try
      {
        -- Prove that (pullback.fst ≫ MonoOver.arrow a) ≫ f = pullback.snd ≫ g
        -- where f and g are the legs of the pullback cone
        have h₃ : (pullback.fst ≫ MonoOver.arrow a) ≫ f = pullback.snd ≫ g := by
          -- Use the given commutativity condition and properties of the pullback
          have h₄ : (pullback.fst ≫ MonoOver.arrow a) ≫ f = pullback.fst ≫ (MonoOver.arrow a ≫ f) := by
            simp [assoc]
          have h₅ : pullback.snd ≫ g = pullback.snd ≫ g := by rfl
          -- We need to show that MonoOver.arrow a ≫ f = something related to g
          -- This is where we would use the specific properties of the pullback and the monoOver structure
          -- For now, we use the given commutativity condition in the context
          have h₆ : f ≫ h = g ≫ k := comm
          -- This is a placeholder; the actual proof would involve more detailed reasoning
          simp_all [PullbackCone.mk, MonoOver.arrow]
          <;>
          try aesop
        exact h₃
      })
  -- Now we need to show that (PullbackCone.mk f g comm).snd = g
  have h₃ : (PullbackCone.mk f g comm).snd = g := by
    -- This would follow from the definition of the pullback cone and the fact that g is one of the legs
    -- In the pullback cone of f and g, the snd leg is g
    -- However, we need to be careful about the exact definition of PullbackCone.mk
    -- For the sake of this proof, we assume it holds based on the context
    have h₄ : (PullbackCone.mk f g comm).snd = g := by
      -- Use the fact that the pullback cone is constructed from f and g
      -- and that the snd leg is g
      rfl
    exact h₄
  rw [h₃] at h₂
  exact h₂

exact h₁
```

**lean_error:** tail step 1/37 ('have h₁ : PullbackCone.IsLimit.lift t (pullback.fst ≫ MonoOver.arrow a) pullback.snd _ ≫ g = pullback.snd := by'): <stdin>:1:111: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 8.2s, verify 0.6s, in=1232, out=828)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply PullbackCone.IsLimit.lift_snd
· exact t
· exact pullback.fst ≫ MonoOver.arrow a
· exact pullback.snd
· dsimp
  rw [← pullback.condition, assoc]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 7.5s, verify 0.2s, in=1284, out=1565)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 243.9s, verify 0.1s, in=1327, out=32768)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 21.1s, verify 0.8s, in=1247, out=2157)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply PullbackCone.IsLimit.lift_snd
exact t
exact pullback.fst ≫ MonoOver.arrow a
exact pullback.snd
assumption
```
