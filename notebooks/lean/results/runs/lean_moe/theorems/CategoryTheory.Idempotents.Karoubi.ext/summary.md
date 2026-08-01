# CategoryTheory.Idempotents.Karoubi.ext   (k=4, 5 tactics total)

file: `Mathlib/CategoryTheory/Idempotents/Karoubi.lean`  

**Ground-truth tail (from k):**
```lean
simpa only [mk.injEq, heq_eq_eq, true_and, eqToHom_refl, comp_id, id_comp] using h_p
```

**True premises at k:** `heq_eq_eq`, `true_and`, `CategoryTheory.eqToHom_refl`, `CategoryTheory.Category.comp_id`, `CategoryTheory.Category.id_comp`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✘ |
| `hint:3` | ✘ |
| `noise:3` | ✘ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 3.9s, verify 0.1s, in=438, out=943)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
ext
· rfl
· simpa using h_p
· apply Subsingleton.elim
```

**lean_error:** tail step 1/4 ('ext'): no applicable extensionality theorem found for

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.4s, verify 0.1s, in=1008, out=2159)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
cases h_p
cases idem✝¹
cases idem✝
rfl
```

**lean_error:** tail step 1/4 ('cases h_p'): dependent elimination failed, failed to solve equation

### `hint:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.7s, verify 0.1s, in=2186, out=1653)

prompt: [`prompts/hint-3.md`](prompts/hint-3.md)

**candidate:**
```lean
have h_pp : p✝¹ = p✝ := by
  simpa using h_p
cases h_pp
apply Subsingleton.elim
```

**lean_error:** tail step 1/4 ('have h_pp : p✝¹ = p✝ := by'): <stdin>:1:13: expected token

### `noise:3` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 6.4s, verify 0.1s, in=2070, out=1562)

prompt: [`prompts/noise-3.md`](prompts/noise-3.md)

**candidate:**
```lean
have hp_eq : p✝¹ = p✝ := by
  simpa using h_p
cases hp_eq
have h_idem : idem✝¹ = idem✝ := Subsingleton.elim _ _
cases h_idem
rfl
```

**lean_error:** tail step 1/6 ('have hp_eq : p✝¹ = p✝ := by'): <stdin>:1:14: expected token
