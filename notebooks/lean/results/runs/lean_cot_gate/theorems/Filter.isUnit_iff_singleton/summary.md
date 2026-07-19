# Filter.isUnit_iff_singleton   (k=0, 1 tactics total)

file: `Mathlib/Order/Filter/Pointwise.lean`  

**Ground-truth tail (from k):**
```lean
simp only [isUnit_iff, Group.isUnit, and_true_iff]
```

**True premises at k:** `Filter.isUnit_iff`, `Group.isUnit`, `and_true_iff`

## Verdict matrix

| rung | qwen3-235b-a22b-base | qwen3-lean-bare-r128 | qwen3-lean-cot-r128 |
| --- | --- | --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ | · ✘ ✘ ✘ | ✘ ✘ · ✘ |
| `hint:2` | ✘ ✓ ✘ ✓ | ✓ ✓ ✓ ✓ | ✓ ✘ ✓ ✓ |
| `hint:3` | ✘ ✘ ✘ ✘ | ✓ ✓ ✓ ✓ | ✘ ✓ ✓ ✘ |
| `noise:3` | ✘ ✘ ✘ ✓ | ✓ ✓ ✓ ✓ | ✓ ✓ ✓ ✓ |

## Per-cell detail

### `stepk:1` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 196.5s, verify 0.3s, in=295, out=8594)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Iff.intro
· rintro ⟨g, rfl⟩
  obtain ⟨U, V, hU, hV, h_sub⟩ := mem_mul.1 (by simp)
  obtain ⟨a, ha⟩ := Filter.nonempty_of_mem hU
  use a
  ext x
  constructor
  · intro hx
    obtain ⟨v, hv⟩ := Filter.nonempty_of_mem hV
    have : x * v = 1 := h_sub ⟨hx, hv⟩
    have : a * v = 1 := h_sub ⟨ha, hv⟩
    exact (mul_right_inj v).mp (this.trans this.symm)
  · rintro rfl; exact ha
· rintro ⟨a, rfl⟩
  exact IsUnit.mk_of_mul_eq_one (pure a⁻¹) (by simp)
```

**lean_error:** tail step 2/15 ('· rintro ⟨g, rfl⟩'): unsolved goals

### `stepk:1` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 198.9s, verify 0.1s, in=295, out=8684)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
intro h
obtain ⟨g, hfg⟩ := h
have h1 : {1} ∈ f * g := hfg.symm ▸ mem_pure
obtain ⟨s, t, hs, ht, hst⟩ := mem_mul.1 h1
obtain ⟨y⟩ := ht.nonempty
have y_in_t : y ∈ t := y_witness
have s_eq : s = {y⁻¹}
{ ext x
  split
  { intro hx
    have : x * y = 1 := hst (mem_mul.mem_mul ⟨x, y, hx, y_in_t⟩)
    exact eq_inv_of_mul_eq_one this }
  { intro hx
    rwa [hx, inv_mul_self] } }
have : {y⁻¹} ∈ f := s_eq.symm ▸ hs
use y⁻¹
exact filter.ext_iff.2 fun S => ⟨fun hS => by { have := nonempty_inter_mem this hS, exact mem_singleton_iff.1 (subset_singleton_iff.1 this.1) }, fun h => mem_sets_of_superset this h⟩
rintro ⟨a, rfl⟩
apply is_unit_of_mul_eq_one
use pure a⁻¹
rw [←pure_mul, mul_inv_self, pure_one]
refl
```

**lean_error:** tail step 1/23 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 206.7s, verify 0.1s, in=295, out=8996)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· intro h
  obtain ⟨g, hfg⟩ := h.exists_left_inv
  obtain ⟨U, U_in_f, V, V_in_g, hUV⟩ := mem_mul_filter.1 (by rw [hfg]; exact mem_pure_self 1)
  obtain ⟨x, hx⟩ := nonempty_of_mem U_in_f
  obtain ⟨y, hy⟩ := nonempty_of_mem V_in_g
  have h_xy : x * y = 1 := hUV x hx y hy
  have hU : U = {x}
  · ext z
    split
    · intro hz
      have hz' : z * y = 1 := hUV z hz y hy
      rw [← mul_right_inj (y⁻¹), mul_assoc, hz', mul_one, h_xy, mul_assoc, mul_inv_right, mul_one]
    · rintro rfl; exact hx
  use x
  apply filter.ext
  intro s
  split
  · intro hs
    have := inter_mem hs (by rw [hU]; exact U_in_f)
    rw [inter_singleton] at this
    exact mem_pure.1 (nonempty_of_mem this).1
  · intro hs
    exact mem_of_superset (by rw [hU]; exact U_in_f) hs
· rintro ⟨a, rfl⟩
  apply is_unit_of_exists_inv (pure a⁻¹)
  rw [mul_pure_pure, pure_one, mul_right_inv, mul_pure_pure, pure_one, mul_left_inv]
```

**lean_error:** tail step 1/27 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 232.3s, verify 0.1s, in=295, out=10147)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
split
· rintro ⟨g, hfg⟩
  have h1 : {1} ∈ (f * g).sets := by rw [hfg]; exact mem_pure_self _
  obtain ⟨U, V, U_in, V_in, hUV⟩ := mem_mul_filter.mp h1
  obtain ⟨u, u_in⟩ := f.ne_bot U_in
  have hV : V ⊆ {u⁻¹} := λ v hv => inv_eq_iff_eq_inv_right.2 (hUV ⟨u_in, hv⟩)
  have hU : ∀ u' ∈ U, u' = u := λ u' hu' => eq_of_mul_eq_one_right (hUV ⟨hu', hV.mp (mem_singleton_self _)⟩)
  exact ⟨u, filter.ext (λ S, ⟨λ HS, hU _ (inter_mem U_in HS) ▸ mem_singleton_self _, λ hS => mem_of_superset U_in (λ x _, hS ▸ rfl)⟩)⟩
· rintro ⟨a, rfl⟩
  exact isUnit_pure a
```

**lean_error:** tail step 1/10 ('split'): tactic 'split' failed

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **incomplete**  (gen 1.5s, verify 0.1s, in=295, out=15)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsUnit, pure_mul_pure]
```

**final state (truncated):**
```
F : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
δ : Type u_5
ε : Type u_6
...
```

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 1.8s, verify 0.1s, in=295, out=17)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [← principalUnit_iff, ← principal_eq_principal]
```

**lean_error:** tail step 1/1 ('simp [← principalUnit_iff, ← principal_eq_principal]'): unknown identifier 'principalUnit_iff'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 1.8s, verify 0.1s, in=295, out=25)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [IsUnit, ← map_eq_pure_iff, ← map_inv, ← map_mul]
```

**lean_error:** tail step 1/1 ('simp [IsUnit, ← map_eq_pure_iff, ← map_inv, ← map_mul]'): unknown identifier 'map_eq_pure_iff'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.9s, verify 0.1s, in=295, out=31)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [← map_isUnit_iff m, map_pure, IsUnit.mem_pure_iff, exists_exists_eq_and]
```

**lean_error:** tail step 1/1 ('simp only [← map_isUnit_iff m, map_pure, IsUnit.mem_pure_iff, exists_exists_eq_and]'): unknown identifier 'map_isUnit_iff'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 3 → **lean_error**  (gen 5.1s, verify 0.1s, in=295, out=147)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp only [isUnit_iff_eq_pure]
```

**lean_error:** tail step 1/1 ('simp only [isUnit_iff_eq_pure]'): unknown identifier 'isUnit_iff_eq_pure'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 5.9s, verify 0.1s, in=295, out=164)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [isUnit_iff_principal]
```

**lean_error:** tail step 1/1 ('simp [isUnit_iff_principal]'): unknown identifier 'isUnit_iff_principal'

### `stepk:1` · qwen3-lean-cot-r128 · rollout 1 → **incomplete**  (gen 6.5s, verify 0.5s, in=295, out=183)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [isUnit_iff]
```

**final state (truncated):**
```
F : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
δ : Type u_5
ε : Type u_6
...
```

### `stepk:1` · qwen3-lean-cot-r128 · rollout 2 → **lean_error**  (gen 12.1s, verify 0.1s, in=295, out=364)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact (IsUnit.map m).trans <| exists_congr fun a ↦ ← map_pure m a
```

**lean_error:** tail step 1/1 ('exact (IsUnit.map m).trans <| exists_congr fun a ↦ ← map_pure m a'): invalid field notation, type is not of the form (C ...) where C is a constant

### `hint:2` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 75.1s, verify 0.1s, in=764, out=3309)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw Filter.isUnit_iff
apply exists_congr
intro a
rw and_iff_left (Group.isUnit a)
```

**lean_error:** tail step 1/4 ('rw Filter.isUnit_iff'): <stdin>:1:3: expected '['

### `hint:2` · qwen3-235b-a22b-base · rollout 1 → **success**  (gen 80.9s, verify 0.5s, in=764, out=3612)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Filter.isUnit_iff]
apply exists_congr
intro a
apply and_iff_left
exact Group.isUnit a
```

### `hint:2` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 100.8s, verify 0.1s, in=764, out=4620)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw Filter.isUnit_iff
apply exists_congr (fun a => and_iff_left (Group.isUnit a))
```

**lean_error:** tail step 1/2 ('rw Filter.isUnit_iff'): <stdin>:1:3: expected '['

### `hint:2` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 119.8s, verify 0.4s, in=764, out=5518)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Filter.isUnit_iff]
apply exists_congr
intro a
exact and_iff_left (Group.isUnit a)
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.0s, verify 0.1s, in=764, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [isUnit_iff, @Group.isUnit α _]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.1s, verify 0.1s, in=764, out=20)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [isUnit_iff, Group.isUnit, and_true_iff]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.1s, verify 0.1s, in=764, out=17)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [isUnit_iff, @Group.isUnit α]
```

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.2s, verify 0.1s, in=764, out=15)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [isUnit_iff, Group.isUnit]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 7.0s, verify 0.1s, in=764, out=192)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [isUnit_iff, Group.isUnit, and_true_iff]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 7.4s, verify 0.1s, in=764, out=220)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa [Group.isUnit] using Filter.isUnit_iff
```

**lean_error:** tail step 1/1 ('simpa [Group.isUnit] using Filter.isUnit_iff'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 9.7s, verify 0.1s, in=764, out=290)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Filter.isUnit_iff, Group.isUnit, and_true_iff]
```

### `hint:2` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 12.5s, verify 0.1s, in=764, out=385)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp only [Filter.isUnit_iff, Group.isUnit, and_true_iff]
```

### `hint:3` · qwen3-235b-a22b-base · rollout 0 → **lean_error**  (gen 108.0s, verify 0.1s, in=1389, out=4101)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Filter.isUnit_iff.trans (exists_congr fun a => and_congr_right fun _ => and_true_iff _)
```

**lean_error:** tail step 1/1 ('apply Filter.isUnit_iff.trans (exists_congr fun a => and_congr_right fun _ => and_true_iff _)'): type mismatch

### `hint:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 161.4s, verify 0.1s, in=1389, out=3598)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw isUnit_iff
apply Exists_congr
intro a
apply and_iff_left
exact Group.isUnit a
```

**lean_error:** tail step 1/5 ('rw isUnit_iff'): <stdin>:1:3: expected '['

### `hint:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 194.6s, verify 0.2s, in=1389, out=6531)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.isUnit_iff]
rw [exists_congr (λ a => and_iff_right (Group.isUnit a))]
```

**lean_error:** tail step 2/2 ('rw [exists_congr (λ a => and_iff_right (Group.isUnit a))]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 210.5s, verify 0.2s, in=1389, out=5827)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
apply Filter.isUnit_iff.trans
apply Exists_congr
intro a
split
· rintro ⟨eq, _⟩; exact eq
· intro eq; exact ⟨eq, Group.isUnit a⟩
```

**lean_error:** tail step 2/6 ('apply Exists_congr'): unknown identifier 'Exists_congr'

### `hint:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.9s, verify 0.1s, in=1389, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [isUnit_iff, Group.isUnit]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 2.0s, verify 0.1s, in=1389, out=15)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [isUnit_iff, Group.isUnit]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 2.1s, verify 0.1s, in=1389, out=17)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [isUnit_iff, @Group.isUnit α]
```

### `hint:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 2.2s, verify 0.8s, in=1389, out=18)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp [isUnit_iff, @Group.isUnit α _]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 0 → **lean_error**  (gen 12.0s, verify 0.1s, in=1389, out=210)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simpa only [Group.isUnit _, and_true_iff] using Filter.isUnit_iff
```

**lean_error:** tail step 1/1 ('simpa only [Group.isUnit _, and_true_iff] using Filter.isUnit_iff'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 13.9s, verify 0.1s, in=1389, out=238)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [isUnit_iff, Group.isUnit, and_true_iff]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 14.4s, verify 0.1s, in=1389, out=255)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
simp only [Filter.isUnit_iff, Group.isUnit, and_true_iff]
```

### `hint:3` · qwen3-lean-cot-r128 · rollout 1 → **lean_error**  (gen 15.2s, verify 0.1s, in=1389, out=296)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isUnit_iff, Group.isUnit, and_true_iff]
```

**lean_error:** tail step 1/1 ('rw [isUnit_iff, Group.isUnit, and_true_iff]'): tactic 'rewrite' failed, equality or iff proof expected

### `noise:3` · qwen3-235b-a22b-base · rollout 3 → **lean_error**  (gen 21.0s, verify 0.2s, in=1424, out=845)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.isUnit_iff]
apply Exists_congr
intro a
apply and_iff_left_iff.mpr
exact Group.isUnit a
```

**lean_error:** tail step 2/5 ('apply Exists_congr'): unknown identifier 'Exists_congr'

### `noise:3` · qwen3-235b-a22b-base · rollout 2 → **lean_error**  (gen 46.6s, verify 0.4s, in=1424, out=1982)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.isUnit_iff]
apply exists_congr
intro a
apply and_iff_right
apply Group.isUnit
```

**lean_error:** tail step 4/5 ('apply and_iff_right'): tactic 'apply' failed, failed to unify

### `noise:3` · qwen3-235b-a22b-base · rollout 1 → **lean_error**  (gen 91.4s, verify 0.2s, in=1424, out=4158)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.isUnit_iff]
apply Exists_congr
intro a
apply and_iff_left
exact Group.isUnit a
```

**lean_error:** tail step 2/5 ('apply Exists_congr'): unknown identifier 'Exists_congr'

### `noise:3` · qwen3-235b-a22b-base · rollout 0 → **success**  (gen 110.6s, verify 0.4s, in=1424, out=5106)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Filter.isUnit_iff]
apply exists_congr
intro a
exact and_iff_left (Group.isUnit a)
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 3 → **success**  (gen 1.3s, verify 0.1s, in=1424, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [isUnit_iff, Group.isUnit]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 1 → **success**  (gen 1.4s, verify 0.1s, in=1424, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [isUnit_iff, @Group.isUnit α _]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 0 → **success**  (gen 1.6s, verify 0.1s, in=1424, out=18)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [isUnit_iff, @Group.isUnit α _]
```

### `noise:3` · qwen3-lean-bare-r128 · rollout 2 → **success**  (gen 1.7s, verify 0.1s, in=1424, out=15)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [isUnit_iff, Group.isUnit]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 3 → **success**  (gen 7.1s, verify 0.1s, in=1424, out=200)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [isUnit_iff, Group.isUnit, and_true_iff]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 2 → **success**  (gen 7.3s, verify 0.1s, in=1424, out=215)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [isUnit_iff, and_true_iff, Group.isUnit]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 0 → **success**  (gen 8.1s, verify 0.1s, in=1424, out=242)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp [Filter.isUnit_iff, and_true_iff, Group.isUnit]
```

### `noise:3` · qwen3-lean-cot-r128 · rollout 1 → **success**  (gen 8.2s, verify 0.1s, in=1424, out=245)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
simp only [Filter.isUnit_iff, Group.isUnit, and_true_iff]
```
