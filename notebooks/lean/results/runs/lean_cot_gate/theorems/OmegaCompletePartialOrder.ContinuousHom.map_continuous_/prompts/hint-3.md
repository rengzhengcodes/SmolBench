## Current goal
```
⊢ Continuous' fun x => pure ∘ f
```

## Full tactic state
```
α : Type u
α' : Type u_1
β✝ : Type v
β' : Type u_2
γ✝ : Type u_3
φ : Type u_4
inst✝⁵ : OmegaCompletePartialOrder α
inst✝⁴ : OmegaCompletePartialOrder β✝
inst✝³ : OmegaCompletePartialOrder γ✝
inst✝² : OmegaCompletePartialOrder φ
inst✝¹ : OmegaCompletePartialOrder α'
inst✝ : OmegaCompletePartialOrder β'
β γ : Type v
f : β → γ
g : α → Part β
hg : Continuous' g
⊢ Continuous' fun x => pure ∘ f
```

## Proof so far (2 tactics)
```lean
simp only [map_eq_bind_pure_comp]
apply bind_continuous' _ _ hg
```

## Theorem
`OmegaCompletePartialOrder.ContinuousHom.map_continuous'` in `Mathlib/Order/OmegaCompletePartialOrder.lean`

## Premises used in the next tactic
- `OmegaCompletePartialOrder.const_continuous'`

## Premise signatures
### `OmegaCompletePartialOrder.const_continuous'` (commanddeclaration)
```lean
theorem const_continuous' (x : β) : Continuous' (Function.const α x)
```

## Premise full source (with proof)
### `OmegaCompletePartialOrder.const_continuous'` (commanddeclaration) at `Mathlib/Order/OmegaCompletePartialOrder.lean`
```lean
theorem const_continuous' (x : β) : Continuous' (Function.const α x) :=
  Continuous.of_bundled' (OrderHom.const α x) (continuous_const x)
```

## Transitive premise context (1-hop, 4/4 premises, ≈570 tokens)
### `OmegaCompletePartialOrder.Continuous'` (commanddeclaration) at `Mathlib/Order/OmegaCompletePartialOrder.lean`
```lean
/-- `Continuous' f` asserts that `f` is both monotone and continuous. -/
def Continuous' (f : α → β) : Prop :=
  ∃ hf : Monotone f, Continuous ⟨f, hf⟩
```

### `Function.const` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
The constant function. If `a : α`, then `Function.const β a : β → α` is the
"constant function with value `a`", that is, `Function.const β a b = a`.
```
example (b : Bool) : Function.const Bool 10 b = 10 :=
  rfl

#check Function.const Bool 10
-- Bool → Nat
```
-/
@[inline] def Function.const {α : Sort u} (β : Sort v) (a : α) : β → α :=
  fun _ => a

/--
The encoding of `let_fun x := v; b` is `letFun v (fun x => b)`.
This is equal to `(fun x => b) v`, so the value of `x` is not accessible to `b`.
This is in contrast to `let x := v; b`, where the value of `x` is accessible to `b`.

There is special support for `letFun`.
Both WHNF and `simp` are aware of `letFun` and can reduce it when zeta reduction is enabled,
despite the fact it is marked `irreducible`.
For metaprogramming, the function `Lean.Expr.letFun?` can be used to recognize a `let_fun` expression
to extract its parts as if it were a `let` expression.
-/
```

### `OrderHom.const` (commanddeclaration) at `Mathlib/Order/Hom/Basic.lean`
```lean
/-- Constant function bundled as an `OrderHom`. -/
@[simps (config := .asFn)]
def const (α : Type*) [Preorder α] {β : Type*} [Preorder β] : β →o α →o β where
  toFun b := ⟨Function.const α b, fun _ _ _ => le_rfl⟩
  monotone' _ _ h _ := h
```

### `continuous_const` (commanddeclaration) at `Mathlib/Topology/Basic.lean`
```lean
@[continuity, fun_prop]
theorem continuous_const : Continuous fun _ : X => y :=
  continuous_iff_continuousAt.mpr fun _ => continuousAt_const
```
