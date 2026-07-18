# covBy_sup_of_inf_covBy_of_inf_covBy_right   (k=1, 2 tactics total)

file: `Mathlib/Order/ModularLattice.lean`  

**Ground-truth tail (from k):**
```lean
exact fun ha hb => covBy_sup_of_inf_covBy_of_inf_covBy_left hb ha
```

**True premises at k:** `covBy_sup_of_inf_covBy_of_inf_covBy_left`

## Verdict matrix

| rung | qwen3-lean-bare-r128 |
| --- | --- |
| `stepk:1` | ✘ ✘ ✘ ✘ |
| `hint:2` | ✘ ✘ ✘ ✘ |

## Per-cell detail

### `stepk:1` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.7s, verify 0.1s, in=254, out=16)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IsWeakUpperModularLattice.wulm
```

**lean_error:** tail step 1/1 ('exact IsWeakUpperModularLattice.wulm'): unknown constant 'IsWeakUpperModularLattice.wulm'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.8s, verify 0.1s, in=254, out=19)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IsWeakUpperModularLattice.strongLowerToStrongUpper
```

**lean_error:** tail step 1/1 ('exact IsWeakUpperModularLattice.strongLowerToStrongUpper'): unknown constant 'IsWeakUpperModularLattice.strongLowerToStrongUpper'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 1.1s, verify 0.1s, in=254, out=22)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IsWeakUpperModularLattice.covby_sup_of_inf_covby_sup
```

**lean_error:** tail step 1/1 ('exact IsWeakUpperModularLattice.covby_sup_of_inf_covby_sup'): unknown constant 'IsWeakUpperModularLattice.covby_sup_of_inf_covby_sup'

### `stepk:1` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 77.8s, verify 0.1s, in=254, out=23)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
exact IsWeakUpperModularLattice.covby_sup_of_inf_covby_covby
```

**lean_error:** tail step 1/1 ('exact IsWeakUpperModularLattice.covby_sup_of_inf_covby_covby'): unknown constant 'IsWeakUpperModularLattice.covby_sup_of_inf_covby_covby'

### `hint:2` · qwen3-lean-bare-r128 · rollout 3 → **lean_error**  (gen 0.6s, verify 0.1s, in=508, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact covBy_sup_of_inf_covBy_of_inf_covBy_left
```

**lean_error:** tail step 1/1 ('exact covBy_sup_of_inf_covBy_of_inf_covBy_left'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · qwen3-lean-bare-r128 · rollout 2 → **lean_error**  (gen 0.7s, verify 0.1s, in=508, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact covBy_sup_of_inf_covBy_of_inf_covBy_left
```

**lean_error:** tail step 1/1 ('exact covBy_sup_of_inf_covBy_of_inf_covBy_left'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · qwen3-lean-bare-r128 · rollout 0 → **lean_error**  (gen 0.9s, verify 0.1s, in=508, out=18)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact covBy_sup_of_inf_covBy_of_inf_covBy_left
```

**lean_error:** tail step 1/1 ('exact covBy_sup_of_inf_covBy_of_inf_covBy_left'): typeclass instance problem is stuck, it is often due to metavariables

### `hint:2` · qwen3-lean-bare-r128 · rollout 1 → **lean_error**  (gen 1.0s, verify 0.1s, in=508, out=23)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
exact IsWeakUpperModularLattice.covBy_sup_of_inf_covBy_covBy
```

**lean_error:** tail step 1/1 ('exact IsWeakUpperModularLattice.covBy_sup_of_inf_covBy_covBy'): typeclass instance problem is stuck, it is often due to metavariables
