# Monotone.biUnion_Ico_Ioc_map_succ   (k=8, 9 tactics total)

file: `Mathlib/Order/SuccPred/IntervalSucc.lean`  

**Ground-truth tail (from k):**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

**True premises at k:** `Order.Ico_succ_right_eq_insert_of_not_isMax`, `Set.biUnion_insert`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✓ | ✘ | ✓ |
| `noise:3` | ✓ | ✓ | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 13.6s, verify 0.5s, in=488, out=3176)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext x
  constructor
  · intro hx
    rcases mem_iUnion₂.1 hx with ⟨i, hi, hxi⟩
    have hle : i ≤ k := (lt_succ_iff).1 hi.2
    by_cases h_eq : i = k
    · left
      simpa [h_eq] using hxi
    · right
      have hi' : i ∈ Ico m k := by
        have hlt : i < k := lt_of_le_of_ne hle h_eq
        exact ⟨hi.1, hlt⟩
      exact mem_iUnion₂.2 ⟨i, hi', hxi⟩
  · intro hx
    rcases hx with hx | hx
    · left
      have hk_mem : k ∈ Ico m (succ k) := by
        have hlt : k < succ k := (lt_succ_iff).2 (le_rfl)
        exact ⟨hmk, hlt⟩
      exact mem_iUnion₂.2 ⟨k, hk_mem, hx⟩
    · rcases mem_iUnion₂.1 hx with ⟨i, hi, hxi⟩
      have hi' : i ∈ Ico m (succ k) := by
        have hlt : i < succ k := (lt_succ_iff).2 (le_of_lt hi.2)
        exact ⟨hi.1, hlt⟩
      exact mem_iUnion₂.2 ⟨i, hi', hxi⟩
```

**lean_error:** tail step 3/25 ('· intro hx'): unsolved goals

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 51.2s, verify 0.1s, in=447, out=7725)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
</think>
rfl
```

**lean_error:** tail step 1/2 ('</think>'): <stdin>:1:0: expected tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **lean_error**  (gen 8.2s, verify 0.1s, in=435, out=806)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [Ico_succ_right]
rw [Set.biUnion_union]
<;> simp [Set.mem_Ico, hmk, hk]
<;> aesop
```

**lean_error:** tail step 1/4 ('rw [Ico_succ_right]'): failed to synthesize instance

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 5.7s, verify 0.1s, in=1062, out=1280)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have hIco : Ico m (succ k) = insert k (Ico m k) :=
    Ico_succ_right_eq_insert_of_not_isMax hmk hk
  rw [hIco, Set.biUnion_insert]
  rfl
```

**lean_error:** tail step 1/4 ('have hIco : Ico m (succ k) = insert k (Ico m k) :='): <stdin>:1:50: unexpected end of input

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 20.2s, verify 0.1s, in=1043, out=2725)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
theorem Monotone.biUnion_Ico_Ioc_map_succ {α : Type u_1} {β : Type u_2} [LinearOrder α] [SuccOrder α] [IsSuccArchimedean α] [LinearOrder β] {f : α → β} (hf : Monotone f) (m n : α) (hmn : m ≤ n) (k : α) (hmk : m ≤ k) (ihk : ⋃ i ∈ Ico m k, Ioc (f i) (f (succ i)) = Ioc (f m) (f k)) (hk : ¬IsMax k) :
    ⋃ i ∈ Ico m (succ k), Ioc (f i) (f (succ i)) = Ioc (f k) (f (succ k)) ∪ ⋃ i ∈ Ico m k, Ioc (f i) (f (succ i)) := by
  have h_main : ⋃ i ∈ Ico m (succ k), Ioc (f i) (f (succ i)) = Ioc (f k) (f (succ k)) ∪ ⋃ i ∈ Ico m k, Ioc (f i) (f (succ i)) := by
    have h₁ : Ico m (succ k) = insert k (Ico m k) := by
      apply Ico_succ_right_eq_insert_of_not_isMax
      · exact hmk
      · exact hk
    rw [h₁]
    rw [Set.biUnion_insert]
    <;> rfl
  
  exact h_main
```

**lean_error:** tail step 1/11 ('theorem Monotone.biUnion_Ico_Ioc_map_succ {α : Type u_1} {β : Type u_2} [LinearOrder α] [SuccOrder α] [IsSuccArchimedean α] [LinearOrder β] {f : α → β} (hf : Monotone f) (m n : α) (hmn : m ≤ n) (k : α) (hmk : m ≤ k) (ihk : ⋃ i ∈ Ico m k, Ioc (f i) (f (succ i)) = Ioc (f m) (f k)) (hk

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 6.0s, verify 0.1s, in=1006, out=564)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `hint:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.8s, verify 0.1s, in=1352, out=1228)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert]
    rfl
```

### `hint:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 19.7s, verify 0.1s, in=1341, out=2653)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h₁ : Ico m (succ k) = insert k (Ico m k) := by
  apply Order.Ico_succ_right_eq_insert_of_not_isMax
  <;> assumption
rw [h₁, Set.biUnion_insert]
<;> rfl
```

**lean_error:** tail step 1/5 ('have h₁ : Ico m (succ k) = insert k (Ico m k) := by'): <stdin>:1:51: unexpected end of input; expected '{'

### `hint:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 5.8s, verify 0.1s, in=1293, out=560)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, biUnion_insert]
```

### `noise:3` · gpt-oss-120b-base · rollout 0 → **success**  (gen 5.6s, verify 0.1s, in=1339, out=1180)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk, Set.biUnion_insert]
  rfl
```

### `noise:3` · nemotron-3-super-120b-a12b-base · rollout 0 → **success**  (gen 12.3s, verify 0.2s, in=1401, out=1647)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have h₁ : Ico m (succ k) = insert k (Ico m k) := Ico_succ_right_eq_insert_of_not_isMax hmk hk
rw [h₁, Set.biUnion_insert]
<;> rfl
```

### `noise:3` · qwen3.5-397b-a17b-base · rollout 0 → **success**  (gen 42.2s, verify 0.3s, in=1312, out=4687)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [Ico_succ_right_eq_insert_of_not_isMax hmk hk]
rw [biUnion_insert]
```
