# CategoryTheory.OverPresheafAux.OverArrows.map_val   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Comma/Presheaf.lean`  

**Ground-truth tail (from k):**
```lean
simp only [unop_op, p.app_val]
```

**True premises at k:** `Opposite.unop_op`

## Verdict matrix

| rung | llama-31-405b-base | llama4-maverick-base | nemotron-ultra-253b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | ✘ |
| `hint:2` | ✘ | ✘ | ✘ |

## Per-cell detail

### `stepk:1` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 1.1s, verify 0.2s, in=307, out=29)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [←yonedaEquiv_naturality]
rw [←yonedaEquiv_apply]
simp only [OverArrows.val]
```

**lean_error:** tail step 1/3 ('rw [←yonedaEquiv_naturality]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `stepk:1` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=276, out=55)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rw [← yonedaEquiv_comp_val p]
simp only [yoneda.map_id, Category.comp_id]
rw [← yonedaEquiv_apply]
exact congr_fun (congr_arg NatTrans.app (OverArrows.condition p)) (𝟙 X)
```

**lean_error:** tail step 1/4 ('rw [← yonedaEquiv_comp_val p]'): tactic 'rewrite' failed, equality or iff proof expected

### `stepk:1` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 9.2s, verify 0.1s, in=296, out=569)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
apply yonedaEquiv_apply_eq
exact p
```

**lean_error:** tail step 1/2 ('apply yonedaEquiv_apply_eq'): unknown identifier 'yonedaEquiv_apply_eq'

### `hint:2` · llama-31-405b-base · rollout 0 → **lean_error**  (gen 0.8s, verify 0.1s, in=510, out=22)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Opposite.unop_op],
  exact yonedaEquiv_naturality _ _ s
```

**lean_error:** tail step 1/2 ('rw [Opposite.unop_op],'): <stdin>:1:21: expected end of input

### `hint:2` · llama4-maverick-base · rollout 0 → **lean_error**  (gen 0.6s, verify 0.2s, in=474, out=29)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [yoneda_map_app, ← p.condition]
simp only [Opposite.unop_op]
rw [OverArrows.val_apply]
```

**lean_error:** tail step 1/3 ('rw [yoneda_map_app, ← p.condition]'): tactic 'rewrite' failed, did not find instance of the pattern in the target expression

### `hint:2` · nemotron-ultra-253b-base · rollout 0 → **lean_error**  (gen 0.5s, verify 0.1s, in=499, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
rw [Opposite.unop_op],
  apply p.property
```

**lean_error:** tail step 1/2 ('rw [Opposite.unop_op],'): <stdin>:1:21: expected end of input
