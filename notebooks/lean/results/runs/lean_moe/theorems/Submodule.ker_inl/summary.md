# Submodule.ker_inl   (k=0, 1 tactics total)

file: `Mathlib/LinearAlgebra/Prod.lean`  

**Ground-truth tail (from k):**
```lean
rw [ker, ← prod_bot, prod_comap_inl]
```

**True premises at k:** `LinearMap.ker`, `Submodule.prod_bot`, `Submodule.prod_comap_inl`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✘ | ✓ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.7s, verify 0.1s, in=400, out=476)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa using (LinearMap.ker_inl (R:=R) (M:=M) (M₂:=M₂))
```

**lean_error:** tail step 1/1 ('simpa using (LinearMap.ker_inl (R:=R) (M:=M) (M₂:=M₂))'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 22.3s, verify 0.1s, in=351, out=2568)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply LinearMap.ker_inl
```

**lean_error:** tail step 1/1 ('apply LinearMap.ker_inl'): invalid field notation, type is not of the form (C ...) where C is a constant

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 5.5s, verify 0.1s, in=347, out=416)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact LinearMap.ker_inl
```

**lean_error:** tail step 1/1 ('exact LinearMap.ker_inl'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.9s, verify 0.1s, in=881, out=538)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [LinearMap.ker, Submodule.prod_bot] using
  (Submodule.prod_comap_inl (p:= (⊥ : Submodule R M)) (q:= (⊥ : Submodule R M₂)))
```

**lean_error:** tail step 1/2 ('simpa [LinearMap.ker, Submodule.prod_bot] using'): <stdin>:1:47: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 23.8s, verify 0.4s, in=846, out=2777)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [ker, Submodule.prod_bot, Submodule.prod_comap_inl]
```

**lean_error:** tail step 1/1 ('simp [ker, Submodule.prod_bot, Submodule.prod_comap_inl]'): tactic 'simp' failed, nested error:

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 7.0s, verify 0.1s, in=821, out=569)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]
```

**lean_error:** tail step 1/1 ('rw [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.4s, verify 0.1s, in=1854, out=791)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa [LinearMap.ker, Submodule.prod_bot] using
  (Submodule.prod_comap_inl (p := (⊥ : Submodule R M)) (q := (⊥ : Submodule R M₂)))
```

**lean_error:** tail step 1/2 ('simpa [LinearMap.ker, Submodule.prod_bot] using'): <stdin>:1:47: unexpected end of input

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 81.1s, verify 0.3s, in=1837, out=9788)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [LinearMap.ker]
rw [Submodule.prod_bot]
rw [LinearMap.comap]
rw [Submodule.prod_comap_inl]
```

**lean_error:** tail step 2/4 ('rw [Submodule.prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 52.0s, verify 0.1s, in=1817, out=5649)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [LinearMap.ker, ← Submodule.prod_bot, Submodule.prod_comap_inl]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 4.3s, verify 0.1s, in=1772, out=638)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simpa [LinearMap.ker, Submodule.prod_bot] using
  (Submodule.prod_comap_inl (p := (⊥ : Submodule R M)) (q := (⊥ : Submodule R M₂)))
```

**lean_error:** tail step 1/2 ('simpa [LinearMap.ker, Submodule.prod_bot] using'): <stdin>:1:47: unexpected end of input

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 20.1s, verify 0.3s, in=2009, out=2311)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [LinearMap.ker]
rw [Submodule.prod_bot]
rw [Submodule.prod_comap_inl]
```

**lean_error:** tail step 2/3 ('rw [Submodule.prod_bot]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 6.6s, verify 0.4s, in=1812, out=526)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]
```

**lean_error:** tail step 1/1 ('simp [LinearMap.ker, Submodule.prod_bot, Submodule.prod_comap_inl]'): tactic 'simp' failed, nested error:
