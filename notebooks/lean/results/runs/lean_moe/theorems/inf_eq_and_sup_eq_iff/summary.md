# inf_eq_and_sup_eq_iff   (k=4, 5 tactics total)

file: `Mathlib/Order/Lattice.lean`  

**Ground-truth tail (from k):**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```

**True premises at k:** `inf_idem`, `sup_idem`

## Verdict matrix

| rung | gpt-oss-120b-base |
| --- | --- |
| `stepk:1` | ✘ |
| `hint:2` | ✓ |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 1.6s, verify 0.2s, in=294, out=371)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
constructor
· exact inf_idem
· exact sup_idem
```

**lean_error:** tail step 2/3 ('· exact inf_idem'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · gpt-oss-120b-base · rollout 0 → **success**  (gen 11.7s, verify 0.1s, in=591, out=1893)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact ⟨inf_idem _, sup_idem _⟩
```
