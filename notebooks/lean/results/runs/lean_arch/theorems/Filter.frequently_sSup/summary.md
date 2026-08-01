# Filter.frequently_sSup   (k=0, 1 tactics total)

file: `Mathlib/Order/Filter/Basic.lean`  

**Ground-truth tail (from k):**
```lean
simp only [Filter.Frequently, not_forall, eventually_sSup, exists_prop]
```

**True premises at k:** `Filter.Frequently`, `Classical.not_forall`, `Filter.eventually_sSup`, `exists_prop`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |
| `hint:3` | ✘ | ✓ | ✘ |
| `noise:3` | ✘ | ✓ | · |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 3.5s, verify 6.2s, in=314, out=90)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · rintro ⟨x, h, hx⟩
    obtain ⟨f, hf, hxf⟩ := (mem_sSup fs).mp h
    exact ⟨f, hf, x, hxf, hx⟩
  · rintro ⟨f, hf, x, hxf, hx⟩
    exact ⟨x, (mem_sSup fs).mpr ⟨f, hf, hxf⟩, hx⟩
```

**lean_error:** tail step 2/6 ('· rintro ⟨x, h, hx⟩'): rcases tactic failed: a✝ : (∀ᶠ (x : α) in sSup fs, ¬(fun x => p x) x) → False is not an inductive datatype

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.7s, verify 0.1s, in=286, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [frequently_sup]
simp only [exists_prop, frequently_exists]
exact forall_congr' fun _ => frequently_filter_of_mem_iff
```

**lean_error:** tail step 1/3 ('rw [frequently_sup]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=303, out=33)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [sSup_eq_iSup, exists_prop, eventually_iSup_iff]
simp only [exists_prop, and_exists, exists_true]
```

**lean_error:** tail step 1/2 ('rw [sSup_eq_iSup, exists_prop, eventually_iSup_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.1s, in=983, out=32)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
unfold Frequently,
rw [not_forall, eventually_sSup],
simp only [exists_prop, not_exists, not_forall],
exact Iff.rfl
```

**lean_error:** tail step 1/4 ('unfold Frequently,'): <stdin>:1:17: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.1s, verify 0.3s, in=956, out=35)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Filter.Frequently, Filter.eventually_sSup, Classical.not_forall]
simp only [exists_prop, Filter.Frequently, not_not]
rfl
```

**lean_error:** tail step 3/3 ('rfl'): type mismatch

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 90.0s, verify 0.1s, in=972, out=5617)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Frequently, eventually_sSup],
rw [not_forall]
```

**lean_error:** tail step 1/2 ('rw [Frequently, eventually_sSup],'): <stdin>:1:32: expected end of input

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1564, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
unfold Frequently
rw [not_forall]
simp [eventually_sSup]
rw [exists_prop]
simp
exact Iff.rfl
```

**lean_error:** tail step 1/6 ('unfold Frequently'): unknown constant 'Frequently'

### `hint:3` · llama4-maverick-base · rollout 0 → **success**  (gen 1.8s, verify 0.3s, in=1539, out=35)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.Frequently, Filter.eventually_sSup, not_forall]
simp only [not_forall, exists_prop, Filter.Frequently]
rfl
```

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.9s, verify 0.1s, in=1553, out=29)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.Frequently, Classical.not_forall]
rw [Filter.eventually_sSup]
simp [exists_prop]
```

**lean_error:** tail step 1/3 ('rw [Filter.Frequently, Classical.not_forall]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.3s, verify 0.2s, in=1587, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
unfold Frequently,
simp only [not_forall, eventually_sSup],
push_neg,
exact exists_prop
```

**lean_error:** tail step 1/4 ('unfold Frequently,'): <stdin>:1:17: expected end of input

### `noise:3` · llama4-maverick-base · rollout 0 → **success**  (gen 0.9s, verify 0.8s, in=1626, out=39)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.Frequently, Filter.eventually_sSup, not_forall]
simp only [not_forall, exists_prop, Filter.Frequently]
simp only [not_not]
```

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **incomplete**  (gen 0.9s, verify 0.9s, in=1576, out=25)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.Frequently, eventually_sSup]
simp only [not_forall, exists_prop]
```

**final state (truncated):**
```
α : Type u
β : Type v
γ : Type w
δ : Type u_1
ι : Sort x
p : α → Prop
...
```
