# Set.partiallyWellOrderedOn_insert   (k=0, 1 tactics total)

file: `Mathlib/Order/WellFoundedSet.lean`  

**Ground-truth tail (from k):**
```lean
simp only [← singleton_union, partiallyWellOrderedOn_union,
  partiallyWellOrderedOn_singleton, true_and_iff]
```

**True premises at k:** `Set.singleton_union`, `Set.partiallyWellOrderedOn_union`, `Set.partiallyWellOrderedOn_singleton`, `true_and_iff`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | ✘ · · · | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ |
| `noise:3` | ✘ ✘ ✘ ✘ | ✘ ✘ ✘ ✘ | ✘ ✘ ✓ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 71.9s, verify 0.1s, in=288, out=3032)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· apply PartiallyWellOrderedOn.mono (s := s) (t := insert a s)
  exact subset_insert a s
· apply PartiallyWellOrderedOn.insert
```

**lean_error:** tail step 1/4 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 115.0s, verify 0.1s, in=288, out=4952)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
apply PartiallyWellOrderedOn.mono (subset_insert a s)
apply PartiallyWellOrderedOn.insert
```

**lean_error:** tail step 1/3 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 147.8s, verify 0.1s, in=288, out=6385)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
apply PartiallyWellOrderedOn.mono (subset_insert a s)
intro h
unfold PartiallyWellOrderedOn
intro f hf
set S := {n | f n = a} with S_eq
by_cases hS : Infinite S
obtain ⟨x, mono_x, x_S⟩ := exists_strictMono_mem hS
use x 0, x 1
exact ⟨mono_x zero_lt_one, inst✝ a a⟩
have S_fin : Finite S := finite_of_not_infinite hS
obtain ⟨N, hN⟩ := finite.exists_lt_all_not_mem S_fin
let g := fun k => f (N + k)
have hg : ∀ k, g k ∈ s := by
  intro k
  have : g k ≠ a := by
    rw [S_eq, Set.mem_setOf_eq]
    exact mt (hN (N + k) (le_add_left rfl.le)) (by simp)
  exact mem_of_insert_of_not_mem (hf (N + k)) this
obtain ⟨i, j, hij, hrij⟩ := h g hg
use N + i, N + j
exact ⟨add_lt_add_left hij N, hrij⟩
```

**lean_error:** tail step 1/22 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 220.7s, verify 0.1s, in=288, out=10000)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
apply PartiallyWellOrderedOn.mono
exact subset_insert
intro h_s
apply PartiallyWellOrderedOn.intro
intro f
by_cases h_a : Infinite {n | f n = a}
obtain ⟨i, hi⟩ := Set.nonempty_of_infinite h_a
obtain ⟨j, hj⟩ := Set.exists_lt_mem_of_infinite h_a i
use i, j
exact ⟨hj, inst✝.refl a⟩
have h_T : Infinite {n | f n ∈ s} := by
convert Set.infinite_compl ⟨h_a⟩ using 1
ext n
rw [mem_insert_iff]
constructor
rintro (rfl | h) <;> exact h
intro h; exact Or.inr h
obtain ⟨g, hg_enum⟩ := Set.Nat.exists_strictMono_enum h_T
let f' := f ∘ g
have hf' : ∀ n, f' n ∈ s := fun n => hg_enum.1 (Set.mem_image_of_mem g n)
obtain ⟨k, l, h_kl, h_rel⟩ := h_s f'
use g k, g l
exact ⟨hg_enum.2.strict_mono h_kl, h_rel⟩
```

**lean_error:** tail step 1/24 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 0.9s, verify 0.1s, in=288, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [insert_eq, partiallyWellOrderedOn_union_left]
```

**lean_error:** tail step 1/1 ('simp [insert_eq, partiallyWellOrderedOn_union_left]'): unknown identifier 'partiallyWellOrderedOn_union_left'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **incomplete**  (gen 1.1s, verify 0.1s, in=288, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [insert_eq, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
r : α → α → Prop
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **incomplete**  (gen 1.2s, verify 0.1s, in=288, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [insert_eq, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
r : α → α → Prop
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **incomplete**  (gen 1.3s, verify 0.1s, in=288, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp_rw [insert_eq, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton]
```

**final state (truncated):**
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
r : α → α → Prop
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 7.9s, verify 0.1s, in=288, out=259)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [partiallyWellOrderedOn_union]
```

**lean_error:** tail step 1/1 ('simp [partiallyWellOrderedOn_union]'): simp made no progress

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 8.9s, verify 0.1s, in=288, out=295)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [PartiallyWellOrderedOn_union, PartiallyWellOrderedOn_singleton]
```

**lean_error:** tail step 1/1 ('simp [PartiallyWellOrderedOn_union, PartiallyWellOrderedOn_singleton]'): unknown identifier 'PartiallyWellOrderedOn_union'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 9.0s, verify 0.1s, in=288, out=293)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [insert_eq, pwo_on_union, pwo_on_singleton]
```

**lean_error:** tail step 1/1 ('simp only [insert_eq, pwo_on_union, pwo_on_singleton]'): unknown identifier 'pwo_on_union'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 10.7s, verify 0.1s, in=288, out=339)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simpa [← insert_eq] using PartiallyWellOrderedOn.union_left
```

**lean_error:** tail step 1/1 ('simpa [← insert_eq] using PartiallyWellOrderedOn.union_left'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 22.6s, verify 0.1s, in=827, out=922)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('rw [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 47.9s, verify 0.1s, in=827, out=1945)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('rw [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 48.0s, verify 0.1s, in=827, out=1948)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [singleton_union]
simp [partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]
```

**lean_error:** tail step 1/2 ('rw [singleton_union]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 65.4s, verify 0.3s, in=827, out=2732)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← Set.singleton_union]
rw [Set.partiallyWellOrderedOn_union]
rw [Set.partiallyWellOrderedOn_singleton, true_and_iff]
```

**lean_error:** tail step 3/3 ('rw [Set.partiallyWellOrderedOn_singleton, true_and_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.6s, verify 0.1s, in=827, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,'): <stdin>:1:86: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.7s, verify 0.1s, in=827, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,'): <stdin>:1:86: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=827, out=27)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,'): <stdin>:1:86: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.9s, verify 0.1s, in=827, out=28)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,'): <stdin>:1:91: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 5.1s, verify 0.1s, in=827, out=167)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,'): <stdin>:1:91: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 6.1s, verify 0.1s, in=827, out=198)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [← singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('rw [← singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,'): <stdin>:1:86: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 6.8s, verify 0.1s, in=827, out=223)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Set.singleton_union, Set.partiallyWellOrderedOn_union,
  Set.partiallyWellOrderedOn_singleton, true_and_iff]
```

**lean_error:** tail step 1/2 ('simp only [Set.singleton_union, Set.partiallyWellOrderedOn_union,'): <stdin>:1:65: unexpected end of input; expected ']'

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 7.0s, verify 0.1s, in=827, out=229)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp_rw [← singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('simp_rw [← singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,'): <stdin>:1:91: unexpected end of input; expected ']'

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 34.0s, verify 0.1s, in=1154, out=534)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]'): simp made no progress

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 53.8s, verify 0.1s, in=1154, out=1253)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]'): simp made no progress

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 54.4s, verify 0.1s, in=1154, out=1308)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]'): simp made no progress

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 101.2s, verify 0.1s, in=1154, out=2950)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [singleton_union, partiallyWellOrderedOn_union]
simp only [partiallyWellOrderedOn_singleton, true_and_iff]
```

**lean_error:** tail step 1/2 ('rw [singleton_union, partiallyWellOrderedOn_union]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 2.0s, verify 0.2s, in=1154, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,'): <stdin>:1:86: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 2.2s, verify 0.1s, in=1154, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,'): <stdin>:1:86: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 2.2s, verify 0.1s, in=1154, out=27)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,'): <stdin>:1:86: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 2.3s, verify 0.1s, in=1154, out=28)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,'): <stdin>:1:91: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 10.5s, verify 0.1s, in=1154, out=187)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]'): simp made no progress

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 10.8s, verify 0.1s, in=1154, out=186)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,'): <stdin>:1:91: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 11.4s, verify 0.1s, in=1154, out=192)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,'): <stdin>:1:91: unexpected end of input; expected ']'

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 12.5s, verify 0.1s, in=1154, out=273)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Set.singleton_union, Set.partiallyWellOrderedOn_union,
  Set.partiallyWellOrderedOn_singleton, true_and_iff]
```

**lean_error:** tail step 1/2 ('simp only [Set.singleton_union, Set.partiallyWellOrderedOn_union,'): <stdin>:1:65: unexpected end of input; expected ']'

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 20.5s, verify 0.1s, in=1179, out=842)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [singleton_union]
rw [partiallyWellOrderedOn_union]
apply true_and_iff
```

**lean_error:** tail step 1/3 ('rw [singleton_union]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 21.9s, verify 0.3s, in=1179, out=900)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [←singleton_union]
rw [partiallyWellOrderedOn_union]
rw [partiallyWellOrderedOn_singleton]
rw [true_and_iff]
```

**lean_error:** tail step 3/4 ('rw [partiallyWellOrderedOn_singleton]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 38.6s, verify 0.1s, in=1179, out=1557)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Set.singleton_union]
rw [Set.partiallyWellOrderedOn_union]
rw [Set.partiallyWellOrderedOn_singleton]
rw [true_and_iff]
```

**lean_error:** tail step 1/4 ('rw [Set.singleton_union]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 44.2s, verify 0.3s, in=1179, out=1799)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [←singleton_union]
rw [partiallyWellOrderedOn_union]
rw [partiallyWellOrderedOn_singleton]
rw [true_and_iff]
```

**lean_error:** tail step 3/4 ('rw [partiallyWellOrderedOn_singleton]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.0s, verify 0.1s, in=1179, out=23)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, singleton_union]
```

**lean_error:** tail step 1/1 ('simp [partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, singleton_union]'): simp made no progress

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.4s, verify 0.1s, in=1179, out=26)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [insert_eq, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]
```

**lean_error:** tail step 1/1 ('rw [insert_eq, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.5s, verify 0.1s, in=1179, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,'): <stdin>:1:86: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.8s, verify 0.1s, in=1179, out=27)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('simp [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,'): <stdin>:1:86: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 5.2s, verify 0.1s, in=1179, out=169)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,'): <stdin>:1:91: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 5.5s, verify 0.1s, in=1179, out=177)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton,'): <stdin>:1:91: unexpected end of input; expected ']'

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 6.9s, verify 0.1s, in=1179, out=227)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp_rw [← singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton, true_and_iff]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 8.5s, verify 0.1s, in=1179, out=283)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton a,
  true_and_iff]
```

**lean_error:** tail step 1/2 ('simp only [singleton_union, partiallyWellOrderedOn_union, partiallyWellOrderedOn_singleton a,'): <stdin>:1:93: unexpected end of input; expected ']'
