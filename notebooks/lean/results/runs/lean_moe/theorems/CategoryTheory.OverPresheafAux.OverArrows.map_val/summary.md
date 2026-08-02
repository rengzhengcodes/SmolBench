# CategoryTheory.OverPresheafAux.OverArrows.map_val   (k=1, 2 tactics total)

file: `Mathlib/CategoryTheory/Comma/Presheaf.lean`  

**Ground-truth tail (from k):**
```lean
simp only [unop_op, p.app_val]
```

**True premises at k:** `Opposite.unop_op`

## Verdict matrix

| rung | gpt-oss-120b-base | nemotron-3-super-120b-a12b-base | qwen3.5-397b-a17b-base |
| --- | --- | --- | --- |
| `stepk:1` | ✘ | ✘ | · |
| `hint:2` | ✘ | ✘ | · |

## Per-cell detail

### `stepk:1` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 8.7s, verify 0.2s, in=344, out=2018)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
rcases p with ⟨val, h⟩
simpa using h
```

**lean_error:** tail step 2/2 ('simpa using h'): type mismatch

### `stepk:1` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 258.9s, verify 0.1s, in=291, out=32768)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
η.app W ∘ (yoneda.obj Y).map f = A.map f ∘ η.app Z
```

**lean_error:** tail step 1/1 ('η.app W ∘ (yoneda.obj Y).map f = A.map f ∘ η.app Z'): <stdin>:1:1: unknown tactic

### `stepk:1` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 4.1s, verify 0.1s, in=291, out=477)

prompt: [`prompts/stepk-1.md`](prompts/stepk-1.md)

**candidate:**
```lean
simp [yonedaEquiv]
```

**final state (truncated):**
```
C : Type u
inst✝ : Category.{v, u} C
A : Cᵒᵖ ⥤ Type v
Y : C
η : yoneda.obj Y ⟶ A
X : C
...
```

### `hint:2` · gpt-oss-120b-base · rollout 0 → **lean_error**  (gen 14.8s, verify 0.1s, in=549, out=3229)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simpa using congrArg yonedaEquiv p.fac
```

**lean_error:** tail step 1/1 ('simpa using congrArg yonedaEquiv p.fac'): type mismatch

### `hint:2` · nemotron-3-super-120b-a12b-base · rollout 0 → **lean_error**  (gen 226.3s, verify 0.1s, in=510, out=28596)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
have h₁ : (op (op X).unop : Cᵒᵖ) = X := by
  simp [Opposite.unop_op]
  <;>
  aesop
rw [h₁]
have h₂ : η.app X (val p) = s.app X (1_X) := p.property
rw [h₂]
rfl
```

**lean_error:** tail step 1/8 ('have h₁ : (op (op X).unop : Cᵒᵖ) = X := by'): <stdin>:1:42: unexpected end of input; expected '{'

### `hint:2` · qwen3.5-397b-a17b-base · rollout 0 → **incomplete**  (gen 3.4s, verify 0.1s, in=504, out=380)

prompt: [`prompts/hint-2.md`](prompts/hint-2.md)

**candidate:**
```lean
simp [Opposite.unop_op]
```

**final state (truncated):**
```
C : Type u
inst✝ : Category.{v, u} C
A : Cᵒᵖ ⥤ Type v
Y : C
η : yoneda.obj Y ⟶ A
X : C
...
```
