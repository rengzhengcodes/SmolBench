# Filter.isUnit_iff_singleton   (k=0, 1 tactics total)

file: `Mathlib/Order/Filter/Pointwise.lean`  

**Ground-truth tail (from k):**
```lean
simp only [isUnit_iff, Group.isUnit, and_true_iff]
```

**True premises at k:** `Filter.isUnit_iff`, `Group.isUnit`, `and_true_iff`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✓ |
| `hint:3` | ✘ | ✘ | ✘ |
| `noise:3` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 2.6s, verify 0.3s, in=323, out=76)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
  · rintro ⟨u, hu, v, hv, h⟩
    refine' ⟨u, _⟩
    change f = pure u
    ext x
    exact (h ▸ mul_eq_one_iff_eq_inv.mp (hu _)).symm
  · rintro ⟨u, rfl⟩
    exact isUnit_pure u
```

**lean_error:** tail step 2/8 ('· rintro ⟨u, hu, v, hv, h⟩'): unsolved goals

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 3.5s, verify 0.1s, in=295, out=68)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [IsUnit_iff_exists_inv]
constructor
intro h
rcases h with ⟨g, hg⟩
rw [← hg.1, ← hg.2]
use f * 1
rw [mul_one]
intro h
rcases h with ⟨a, rfl⟩
rw [IsUnit_pure]
```

**lean_error:** tail step 1/10 ('rw [IsUnit_iff_exists_inv]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.0s, verify 0.1s, in=312, out=44)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply Iff.toForall
intro
apply propext
split
intro h
existsi h.some
exact h.choose_spec
intro h
cases h
exact IsUnit.pure _
```

**lean_error:** tail step 1/10 ('apply Iff.toForall'): unknown constant 'Iff.toForall'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=794, out=19)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Filter.isUnit_iff],
simp only [and_true_iff, Group.isUnit]
```

**lean_error:** tail step 1/2 ('rw [Filter.isUnit_iff],'): <stdin>:1:22: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 2.3s, verify 1.2s, in=764, out=30)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isUnit_iff]
simp_rw [and_true_iff]
simp only [Group.isUnit]
exact exists_congr fun _ => eq_comm
```

**lean_error:** tail step 2/4 ('simp_rw [and_true_iff]'): simp made no progress

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **success**  (gen 0.6s, verify 0.2s, in=783, out=21)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [isUnit_iff]
simp [Group.isUnit, and_true_iff]
```

### `hint:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.4s, verify 1.0s, in=1427, out=26)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [Filter.isUnit_iff, and_true_iff]
apply Iff.rfl
intro a
exact Group.isUnit a
```

**lean_error:** tail step 1/4 ('rw [Filter.isUnit_iff, and_true_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 1.5s, verify 0.8s, in=1384, out=22)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isUnit_iff]
simp_rw [Group.isUnit a]
simp only [and_true_iff]
```

**lean_error:** tail step 2/3 ('simp_rw [Group.isUnit a]'): unknown identifier 'a'

### `hint:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=1416, out=21)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
rw [isUnit_iff, and_true_iff],
simp [Group.isUnit]
```

**lean_error:** tail step 1/2 ('rw [isUnit_iff, and_true_iff],'): <stdin>:1:29: expected end of input

### `noise:3` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1451, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isUnit_iff, and_true_iff]
exact fun a => ⟨Group.isUnit a⟩
```

**lean_error:** tail step 1/2 ('rw [isUnit_iff, and_true_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `noise:3` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.5s, in=1495, out=21)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isUnit_iff]
simp_rw [and_true_iff]
simp only [Group.isUnit]
```

**lean_error:** tail step 2/3 ('simp_rw [and_true_iff]'): simp made no progress

### `noise:3` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.1s, in=1440, out=43)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
rw [isUnit_iff, and_true_iff]
exact ⟨λ ⟨a, h⟩, ⟨a, h⟩, λ ⟨a, h⟩, ⟨a, h⟩⟩
```

**lean_error:** tail step 1/2 ('rw [isUnit_iff, and_true_iff]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression
