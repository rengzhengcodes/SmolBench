# CategoryTheory.Adjunction.localization_unit_app   (k=0, 1 tactics total)

file: `Mathlib/CategoryTheory/Localization/Adjunction.lean`  

**Ground-truth tail (from k):**
```lean
apply Localization.ε_app
```

**True premises at k:** `CategoryTheory.Adjunction.Localization.ε_app`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 0.4s, in=696, out=249)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa
```

**lean_error:** tail step 1/1 ('simpa'): tactic 'assumption' failed

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 2.2s, verify 0.3s, in=1185, out=517)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using (ε_app (adj:=adj) (L₁:=L₁) (W₁:=W₁) (L₂:=L₂) (G':=G') (F':=F') X₁)
```

**lean_error:** tail step 1/1 ("simpa using (ε_app (adj:=adj) (L₁:=L₁) (W₁:=W₁) (L₂:=L₂) (G':=G') (F':=F') X₁)"): unknown identifier 'ε_app'

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.6s, verify 0.1s, in=1897, out=1203)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [Adjunction.localization] using
  (Adjunction.Localization.ε_app (adj:=adj) (L₁:=L₁) (W₁:=W₁) (L₂:=L₂) (G':=G') (F':=F') X₁)
```

**lean_error:** tail step 1/2 ('simpa [Adjunction.localization] using'): <stdin>:1:37: unexpected end of input

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.2s, verify 0.3s, in=1827, out=754)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa using ε_app (adj:=adj) (L₁:=L₁) (W₁:=W₁) (L₂:=L₂) (G':=G') (F':=F') X₁
```

**lean_error:** tail step 1/1 ("simpa using ε_app (adj:=adj) (L₁:=L₁) (W₁:=W₁) (L₂:=L₂) (G':=G') (F':=F') X₁"): unknown identifier 'ε_app'
