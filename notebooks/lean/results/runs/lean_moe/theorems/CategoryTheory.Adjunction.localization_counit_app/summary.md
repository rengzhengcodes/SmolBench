# CategoryTheory.Adjunction.localization_counit_app   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Localization/Adjunction.lean`  

**Ground-truth tail (from k):**
```lean
apply Localization.η_app
```

**True premises at k:** `CategoryTheory.Adjunction.Localization.η_app`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | · | ✘ | ✘ |
| `hint:2` | ✓ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **incomplete**  (gen 1.4s, verify 0.2s, in=690, out=291)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp
```

**final state (truncated):**
```
C₁ : Type u_1
C₂ : Type u_2
D₁ : Type u_3
D₂ : Type u_4
inst✝⁷ : Category.{u_8, u_1} C₁
inst✝⁶ : Category.{u_7, u_2} C₂
...
```

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 58.4s, verify 0.1s, in=654, out=7204)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 3.9s, verify 0.1s, in=613, out=306)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 6.4s, verify 0.1s, in=1136, out=1485)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [localization] using (Localization.η_app (adj:=adj) (L₁:=L₁) (L₂:=L₂) (W₂:=W₂) (G':=G') (F':=F') X₂)
```

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 90.7s, verify 0.1s, in=1134, out=11670)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h : (localization adj L₁ W₁ L₂ W₂ G' F').counit.app (L₂.obj X₂) = G'.map ((CatCommSq.iso F L₂ L₁ F').inv.app X₂) ≫ (CatCommSq.iso G L₁ L₂ G').inv.app (F.obj X₂) ≫ L₂.map (adj.counit.app X₂) := by
  rw [η_app]
  <;>
  rfl
exact h
```

**lean_error:** tail step 1/5 ("have h : (localization adj L₁ W₁ L₂ W₂ G' F').counit.app (L₂.obj X₂) = G'.map ((CatCommSq.iso F L₂ L₁ F').inv.app X₂) ≫ (CatCommSq.iso G L₁ L₂ G').inv.app (F.obj X₂) ≫ L₂.map (adj.counit.app X₂) := by"): <stdin>:1:200: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 82.3s, verify 0.7s, in=1067, out=9116)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [η_app]
```

**lean_error:** tail step 1/1 ('rw [η_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.7s, verify 0.1s, in=1848, out=1225)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [localization] using
  (η_app (adj:=adj) (L₁:=L₁) (L₂:=L₂) (W₂:=W₂) (G':=G') (F':=F') X₂)
```

**lean_error:** tail step 1/2 ('simpa [localization] using'): <stdin>:1:26: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 141.0s, verify 0.1s, in=1869, out=19450)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply η_app
```

**lean_error:** tail step 1/1 ('apply η_app'): unknown identifier 'η_app'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.4s, verify 0.2s, in=1771, out=530)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [← η_app]
<;> simp [localization]
```

**lean_error:** tail step 1/2 ('rw [← η_app]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.9s, verify 0.1s, in=1778, out=1158)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [Adjunction.localization] using (η_app (adj:=adj) (L₁:=L₁) (L₂:=L₂) (W₂:=W₂) (G':=G') (F':=F') X₂)
```

**lean_error:** tail step 1/1 ("simpa [Adjunction.localization] using (η_app (adj:=adj) (L₁:=L₁) (L₂:=L₂) (W₂:=W₂) (G':=G') (F':=F') X₂)"): unknown identifier 'η_app'

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 104.6s, verify 0.1s, in=1968, out=13576)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h : (localization adj L₁ W₁ L₂ W₂ G' F').counit.app (L₂.obj X₂) = G'.map ((CatCommSq.iso F L₂ L₁ F').inv.app X₂) ≫ (CatCommSq.iso G L₁ L₂ G').inv.app (F.obj X₂) ≫ L₂.map (adj.counit.app X₂) := by
  have h₁ : (η adj L₁ L₂ W₂ G' F').app (L₂.obj X₂) = G'.map ((CatCommSq.iso F L₂ L₁ F').inv.app X₂) ≫ (CatCommSq.iso G L₁ L₂ G').inv.app (F.obj X₂) ≫ L₂.map (adj.counit.app X₂) := by
    apply η_app
  have h₂ : (localization adj L₁ W₁ L₂ W₂ G' F').counit.app (L₂.obj X₂) = (η adj L₁ L₂ W₂ G' F').app (L₂.obj X₂) := by
    rfl
  rw [h₂]
  exact h₁
```

**lean_error:** tail step 1/7 ("have h : (localization adj L₁ W₁ L₂ W₂ G' F').counit.app (L₂.obj X₂) = G'.map ((CatCommSq.iso F L₂ L₁ F').inv.app X₂) ≫ (CatCommSq.iso G L₁ L₂ G').inv.app (F.obj X₂) ≫ L₂.map (adj.counit.app X₂) := by"): <stdin>:1:200: unexpected end of input; expected '{'

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.3s, verify 0.2s, in=1781, out=761)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← η_app]
<;> rfl
```

**lean_error:** tail step 1/2 ('rw [← η_app]'): tactic 'rewrite' failed, equality or iff proof expected
