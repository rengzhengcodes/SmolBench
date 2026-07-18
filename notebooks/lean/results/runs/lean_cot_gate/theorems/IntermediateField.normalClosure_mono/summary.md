# IntermediateField.normalClosure_mono   (k=1, 2 tactics total)

file: `Mathlib/FieldTheory/NormalClosure.lean`  

**Ground-truth tail (from k):**
```lean
exact iSup_mono (fun f ↦ map_mono f h)
```

**True premises at k:** `iSup_mono`, `IntermediateField.map_mono`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | X X X | ✘ ✘ ✘ ✓ ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | X X X X | ✓ ✘ ✓ ✓ ✘ ✓ ✓ ✓ |
| `hint:3` | ✘ ✘ ✓ ✘ | · | ✓ ✓ ✘ ✓ ✘ ✓ ✓ · |
| `noise:3` | ✘ ✘ ✘ ✘ | X X X | ✓ ✓ ✓ ✘ ✓ ✓ ✘ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 30.6s, verify 0.1s, in=289, out=1097)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply supr_le_supr
intro f
apply map_mono
exact h
```

**lean_error:** tail step 1/4 ('apply supr_le_supr'): unknown identifier 'supr_le_supr'

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 96.3s, verify 0.1s, in=289, out=4002)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply supr_le_supr
intros f
apply SetLike.le_of_subset
apply image_subset
exact h
```

**lean_error:** tail step 1/5 ('apply supr_le_supr'): unknown identifier 'supr_le_supr'

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 178.9s, verify 0.1s, in=289, out=8159)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
sup_mono $ λ f ↦ let ⟨g, hg⟩ := (IntermediateField.inclusion h).extend f in ⟨g, map_mono (Set.image_subset g (Set.univ_inter (IntermediateField.inclusion h).source.carrier))⟩
```

**lean_error:** tail step 1/1 ('sup_mono $ λ f ↦ let ⟨g, hg⟩ := (IntermediateField.inclusion h).extend f in ⟨g, map_mono (Set.image_subset g (Set.univ_inter (IntermediateField.inclusion h).source.carrier))⟩'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 214.0s, verify 0.1s, in=289, out=10176)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply supr_le
intro f
obtain ⟨τ, hτ⟩ := Normal.exists_alg_hom K f
have hg := τ.restrict_domain K'
have : map f K ≤ map hg K' := map_mono hg h
transitivity map hg K'
exact this
apply le_supr hg
```

**lean_error:** tail step 1/8 ('apply supr_le'): unknown identifier 'supr_le'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **exception**  (gen 3.1s, verify 300.1s, in=289, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact iSup₂_mono' fun _ => map_mono h
```

**lean_error:** DojoTacticTimeoutError: 

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **exception**  (gen 1203.7s, verify 300.1s, in=289, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact iSup_mono fun f ↦ map_mono h
```

**lean_error:** DojoTacticTimeoutError: 

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **exception**  (gen 3433.7s, verify 413.1s, in=289, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact iSup_mono fun _ => map_mono h
```

**lean_error:** DojoTacticTimeoutError: 

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 7.5s, verify 0.1s, in=289, out=206)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact iSup_le_iSup fun f ↦ h.map f
```

**lean_error:** tail step 1/1 ('exact iSup_le_iSup fun f ↦ h.map f'): unknown identifier 'iSup_le_iSup'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 7 → **lean_error**  (gen 8.5s, verify 0.1s, in=289, out=216)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun f => map_mono h'): application type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 8.7s, verify 0.1s, in=289, out=243)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact iSup_le_iSup fun f => map_le_map h
```

**lean_error:** tail step 1/1 ('exact iSup_le_iSup fun f => map_le_map h'): unknown identifier 'iSup_le_iSup'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 5 → **success**  (gen 9.2s, verify 0.1s, in=289, out=254)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact iSup_mono fun f ↦ map_mono f h
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 11.6s, verify 0.1s, in=289, out=215)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact iSup_mono fun f => h.mono_map f
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun f => h.mono_map f'): invalid field 'mono_map', the environment does not contain 'LE.le.mono_map'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 12.1s, verify 0.1s, in=289, out=226)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact iSup_mono fun f => map_le_map h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun f => map_le_map h'): unknown identifier 'map_le_map'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 12.2s, verify 0.1s, in=289, out=229)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact supr_mono fun f => h.map f
```

**lean_error:** tail step 1/1 ('exact supr_mono fun f => h.map f'): unknown identifier 'supr_mono'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 12.9s, verify 0.1s, in=289, out=255)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact iSup_le_iSup fun f => map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_le_iSup fun f => map_mono h'): unknown identifier 'iSup_le_iSup'

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 24.6s, verify 0.3s, in=630, out=1010)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply map_mono h
```

**lean_error:** tail step 3/3 ('apply map_mono h'): application type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 40.3s, verify 0.3s, in=630, out=1665)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply map_mono h
```

**lean_error:** tail step 3/3 ('apply map_mono h'): application type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 69.5s, verify 0.4s, in=630, out=2765)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply iSup_mono
intro f
exact map_mono h
```

**lean_error:** tail step 3/3 ('exact map_mono h'): type mismatch

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 89.6s, verify 0.3s, in=630, out=3815)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply map_mono h
```

**lean_error:** tail step 3/3 ('apply map_mono h'): application type mismatch

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **exception**  (gen 303.3s, verify 300.1s, in=630, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono f h
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **exception**  (gen 603.4s, verify 300.1s, in=630, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_mono fun _ ↦ map_mono h
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **exception**  (gen 2120.5s, verify 320.6s, in=630, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_mono fun f ↦ map_mono f h
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **exception**  (gen 2598.4s, verify 494.0s, in=630, out=16)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono f h
```

**lean_error:** DojoTacticTimeoutError: 

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 8.3s, verify 0.1s, in=630, out=233)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono f h
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 10.7s, verify 0.1s, in=630, out=185)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_mono fun f ↦ map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun f ↦ map_mono h'): application type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 12.0s, verify 0.1s, in=630, out=228)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_mono fun f ↦ map_mono f h
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 13.4s, verify 0.1s, in=630, out=270)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_mono fun f ↦ map_mono f h
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 4 → **lean_error**  (gen 15.2s, verify 0.7s, in=630, out=196)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono h f
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun f => map_mono h f'): type mismatch

### `hint:2` · qwen3-lean-cot-r128 · rollout 6 → **success**  (gen 15.9s, verify 0.1s, in=630, out=175)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
apply iSup_mono fun f => map_mono f h
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 7 → **success**  (gen 16.8s, verify 0.1s, in=630, out=201)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono f h
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 5 → **success**  (gen 18.1s, verify 0.1s, in=630, out=254)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono f h
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 34.5s, verify 0.3s, in=3385, out=599)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply map_mono h
```

**lean_error:** tail step 3/3 ('apply map_mono h'): application type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 55.8s, verify 0.3s, in=3385, out=937)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply iSup_mono
exact map_mono h
```

**lean_error:** tail step 2/2 ('exact map_mono h'): type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 103.3s, verify 0.2s, in=3385, out=3434)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply iSup_mono
exact fun f => map_mono f h
```

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 162.0s, verify 0.1s, in=3385, out=6526)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply iSup_mono (map_mono h)
```

**lean_error:** tail step 1/1 ('apply iSup_mono (map_mono h)'): application type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 24.1s, verify 0.1s, in=3385, out=274)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact iSup_mono fun f ↦ map_mono _ h
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 4 → **success**  (gen 24.6s, verify 0.1s, in=3385, out=207)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact iSup_mono fun f ↦ map_mono f h
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 24.7s, verify 0.1s, in=3385, out=251)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact iSup_mono fun f ↦ map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun f ↦ map_mono h'): application type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 24.9s, verify 0.1s, in=3385, out=220)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply iSup_mono fun _ ↦ IntermediateField.map_mono _ h
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 6 → **lean_error**  (gen 26.8s, verify 0.1s, in=3385, out=241)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact iSup_mono (map_mono h)
```

**lean_error:** tail step 1/1 ('exact iSup_mono (map_mono h)'): application type mismatch

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 27.0s, verify 0.1s, in=3385, out=276)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono f h
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 7 → **success**  (gen 27.9s, verify 0.1s, in=3385, out=272)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono f h
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 5 → **incomplete**  (gen 28.0s, verify 0.1s, in=3385, out=316)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
gcongr
```

**final state (truncated):**
```
case h
F : Type u_1
K✝ : Type u_2
L : Type u_3
inst✝⁵ : Field F
inst✝⁴ : Field K✝
...
```

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 20.0s, verify 0.3s, in=3414, out=655)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply iSup_mono
intro f
apply map_mono h
```

**lean_error:** tail step 3/3 ('apply map_mono h'): application type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 26.1s, verify 0.3s, in=3414, out=1075)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply iSup_mono
intro f
exact map_mono h
```

**lean_error:** tail step 3/3 ('exact map_mono h'): type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 107.5s, verify 0.2s, in=3414, out=4721)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply iSup_mono
fun f => map_mono h
```

**lean_error:** tail step 2/2 ('fun f => map_mono h'): <stdin>:1:0: expected tactic

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 214.1s, verify 0.4s, in=3414, out=10181)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
apply iSup_mono
intros f
apply map_mono h
```

**lean_error:** tail step 3/3 ('apply map_mono h'): application type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **exception**  (gen 903.6s, verify 300.2s, in=3414, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono _ h
```

**lean_error:** DojoTacticTimeoutError: 

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **exception**  (gen 1503.9s, verify 300.5s, in=3414, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono _ h
```

**lean_error:** DojoTacticTimeoutError: 

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **exception**  (gen 1813.7s, verify 301.6s, in=3414, out=16)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_mono fun _ ↦ map_mono h
```

**lean_error:** DojoTacticTimeoutError: 

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 18.2s, verify 0.1s, in=3414, out=234)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_mono fun f => K.map_mono f h
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 4 → **success**  (gen 18.9s, verify 0.1s, in=3414, out=199)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_mono fun f ↦ map_mono f h
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 19.7s, verify 0.1s, in=3414, out=258)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono f h
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 5 → **lean_error**  (gen 20.2s, verify 0.1s, in=3414, out=234)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_mono h.map_mono
```

**lean_error:** tail step 1/1 ('exact iSup_mono h.map_mono'): invalid field 'map_mono', the environment does not contain 'LE.le.map_mono'

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 20.5s, verify 0.1s, in=3414, out=248)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_mono fun f ↦ map_mono f h
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 6 → **success**  (gen 20.6s, verify 0.1s, in=3414, out=223)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono f h
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 21.2s, verify 0.1s, in=3414, out=208)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_mono fun f ↦ map_mono h
```

**lean_error:** tail step 1/1 ('exact iSup_mono fun f ↦ map_mono h'): application type mismatch

### `noise:3` · qwen3-lean-cot-r128 · rollout 7 → **success**  (gen 22.4s, verify 0.1s, in=3414, out=210)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact iSup_mono fun f => map_mono f h
```
