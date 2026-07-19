# CategoryTheory.Groupoid.Free.lift_unique   (k=9, 10 tactics total)

file: `Mathlib/CategoryTheory/Groupoid/FreeGroupoid.lean`  

**Ground-truth tail (from k):**
```lean
convert this <;> simp only [inv_eq_inv]
```

**True premises at k:** `CategoryTheory.Groupoid.inv_eq_inv`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✓ ✘ ✓ | ✓ ✓ · · | ✘ ✘ ✘ · |
| `hint:3` | ✘ ✓ ✘ ✓ | ✓ ✘ ✓ ✓ | ✓ ✘ ✘ ✘ |
| `noise:3` | ✘ ✓ ✘ ✘ | ✓ ✓ · · | ✘ · ✘ · |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 12.8s, verify 0.2s, in=407, out=485)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact this
```

**lean_error:** tail step 1/1 ('exact this'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 18.2s, verify 0.2s, in=407, out=692)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact this
```

**lean_error:** tail step 1/1 ('exact this'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 32.1s, verify 0.2s, in=407, out=1217)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact this
```

**lean_error:** tail step 1/1 ('exact this'): type mismatch

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 41.0s, verify 0.2s, in=407, out=1549)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact this
```

**lean_error:** tail step 1/1 ('exact this'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=407, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.1s, verify 0.2s, in=407, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
assumption
```

**lean_error:** tail step 1/1 ('assumption'): tactic 'assumption' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.4s, verify 0.2s, in=407, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
assumption
```

**lean_error:** tail step 1/1 ('assumption'): tactic 'assumption' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.7s, verify 0.2s, in=407, out=7)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact this
```

**lean_error:** tail step 1/1 ('exact this'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 4.7s, verify 0.2s, in=407, out=132)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact this
```

**lean_error:** tail step 1/1 ('exact this'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 5.4s, verify 0.2s, in=407, out=125)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rwa [← this]
```

**lean_error:** tail step 1/1 ('rwa [← this]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 6.5s, verify 0.2s, in=407, out=162)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact this
```

**lean_error:** tail step 1/1 ('exact this'): type mismatch

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 6.7s, verify 0.1s, in=407, out=168)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa only [CategoryTheory.inv_eq_inv] using this
```

**lean_error:** tail step 1/1 ('simpa only [CategoryTheory.inv_eq_inv] using this'): unknown identifier 'CategoryTheory.inv_eq_inv'

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 18.7s, verify 0.1s, in=757, out=710)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [inv_eq_inv, inv_eq_inv], exact this
```

**lean_error:** tail step 1/1 ('rw [inv_eq_inv, inv_eq_inv], exact this'): <stdin>:1:27: expected end of input

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 46.0s, verify 0.1s, in=757, out=1730)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Groupoid.inv_eq_inv, this, ← Groupoid.inv_eq_inv]
```

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 73.5s, verify 0.1s, in=757, out=2740)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw inv_eq_inv
exact this
```

**lean_error:** tail step 1/2 ('rw inv_eq_inv'): <stdin>:1:3: expected '['

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 108.6s, verify 0.4s, in=757, out=4185)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Groupoid.inv_eq_inv]
rw [this]
rw [Groupoid.inv_eq_inv]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.8s, verify 0.1s, in=757, out=6)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.3s, verify 0.1s, in=757, out=9)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [this]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 2.1s, verify 0.2s, in=757, out=14)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Groupoid.inv_eq_inv]
```

**final state (truncated):**
```
V : Type u
inst✝¹ : Quiver V
V' : Type u'
inst✝ : Groupoid V'
φ✝ φ : V ⥤q V'
Φ : FreeGroupoid V ⥤ V'
...
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 2.7s, verify 0.2s, in=757, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [← Functor.toPrefunctor_comp, Prefunctor.comp_map, Paths.of_map, inv_eq_inv]
```

**final state (truncated):**
```
V : Type u
inst✝¹ : Quiver V
V' : Type u'
inst✝ : Groupoid V'
φ✝ φ : V ⥤q V'
Φ : FreeGroupoid V ⥤ V'
...
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 5.1s, verify 0.2s, in=757, out=142)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rwa [Groupoid.inv_eq_inv]
```

**lean_error:** tail step 1/1 ('rwa [Groupoid.inv_eq_inv]'): tactic 'assumption' failed

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 7.3s, verify 0.2s, in=757, out=178)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rwa [Groupoid.inv_eq_inv]
```

**lean_error:** tail step 1/1 ('rwa [Groupoid.inv_eq_inv]'): tactic 'assumption' failed

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 7.5s, verify 0.2s, in=757, out=211)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rwa [Groupoid.inv_eq_inv]
```

**lean_error:** tail step 1/1 ('rwa [Groupoid.inv_eq_inv]'): tactic 'assumption' failed

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 8.4s, verify 0.1s, in=757, out=225)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [CategoryTheory.Groupoid.inv_eq_inv]
```

**final state (truncated):**
```
V : Type u
inst✝¹ : Quiver V
V' : Type u'
inst✝ : Groupoid V'
φ✝ φ : V ⥤q V'
Φ : FreeGroupoid V ⥤ V'
...
```

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 75.2s, verify 0.3s, in=859, out=2084)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [inv_eq_inv]
exact this
```

**lean_error:** tail step 2/2 ('exact this'): type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 117.5s, verify 0.1s, in=859, out=4094)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Groupoid.inv_eq_inv, this, Groupoid.inv_eq_inv]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 151.1s, verify 0.2s, in=859, out=5628)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
exact this
```

**lean_error:** tail step 1/1 ('exact this'): type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **success**  (gen 152.3s, verify 0.3s, in=859, out=5460)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Groupoid.inv_eq_inv, Groupoid.inv_eq_inv]
exact this
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.2s, verify 0.2s, in=859, out=6)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.4s, verify 0.1s, in=859, out=7)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rfl
```

**lean_error:** tail step 1/1 ('rfl'): type mismatch

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 2.6s, verify 0.1s, in=859, out=11)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [inv_eq_inv]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.8s, verify 0.1s, in=859, out=13)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [IsIso.inv_eq_inv]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 9.9s, verify 0.1s, in=859, out=169)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [Groupoid.inv_eq_inv]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 10.0s, verify 0.2s, in=859, out=154)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rwa [Groupoid.inv_eq_inv]
```

**lean_error:** tail step 1/1 ('rwa [Groupoid.inv_eq_inv]'): tactic 'assumption' failed

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 10.3s, verify 0.2s, in=859, out=173)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rwa [Groupoid.inv_eq_inv]
```

**lean_error:** tail step 1/1 ('rwa [Groupoid.inv_eq_inv]'): tactic 'assumption' failed

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 11.1s, verify 0.1s, in=859, out=149)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [inv_eq_inv] <;> exact this
```

**lean_error:** tail step 1/1 ('rw [inv_eq_inv] <;> exact this'): type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 12.1s, verify 0.2s, in=884, out=456)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
exact this
```

**lean_error:** tail step 1/1 ('exact this'): type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **success**  (gen 72.1s, verify 0.1s, in=884, out=2685)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [inv_eq_inv]
exact this
```

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 117.7s, verify 0.3s, in=884, out=4596)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [← Groupoid.inv_eq_inv] at this
exact this
```

**lean_error:** tail step 2/2 ('exact this'): type mismatch

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 120.0s, verify 0.3s, in=884, out=4695)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [inv_eq_inv] at this
exact this
```

**lean_error:** tail step 2/2 ('exact this'): type mismatch

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 0.7s, verify 0.1s, in=884, out=6)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.6s, verify 0.1s, in=884, out=9)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [this]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 1.9s, verify 0.2s, in=884, out=14)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Groupoid.inv_eq_inv]
```

**final state (truncated):**
```
V : Type u
inst✝¹ : Quiver V
V' : Type u'
inst✝ : Groupoid V'
φ✝ φ : V ⥤q V'
Φ : FreeGroupoid V ⥤ V'
...
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 3.0s, verify 0.2s, in=884, out=30)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [← Functor.toPrefunctor_comp, Prefunctor.comp_map, Paths.of_map, inv_eq_inv]
```

**final state (truncated):**
```
V : Type u
inst✝¹ : Quiver V
V' : Type u'
inst✝ : Groupoid V'
φ✝ φ : V ⥤q V'
Φ : FreeGroupoid V ⥤ V'
...
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 6.3s, verify 0.2s, in=884, out=178)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rwa [Groupoid.inv_eq_inv]
```

**lean_error:** tail step 1/1 ('rwa [Groupoid.inv_eq_inv]'): tactic 'assumption' failed

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **incomplete**  (gen 6.9s, verify 0.1s, in=884, out=197)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [inv_eq_inv]
```

**final state (truncated):**
```
V : Type u
inst✝¹ : Quiver V
V' : Type u'
inst✝ : Groupoid V'
φ✝ φ : V ⥤q V'
Φ : FreeGroupoid V ⥤ V'
...
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 7.0s, verify 0.2s, in=884, out=171)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rwa [CategoryTheory.Groupoid.inv_eq_inv]
```

**lean_error:** tail step 1/1 ('rwa [CategoryTheory.Groupoid.inv_eq_inv]'): tactic 'assumption' failed

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **incomplete**  (gen 7.7s, verify 0.1s, in=884, out=225)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [CategoryTheory.Groupoid.inv_eq_inv]
```

**final state (truncated):**
```
V : Type u
inst✝¹ : Quiver V
V' : Type u'
inst✝ : Groupoid V'
φ✝ φ : V ⥤q V'
Φ : FreeGroupoid V ⥤ V'
...
```
