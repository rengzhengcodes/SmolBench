## Current goal
```
⊢ i ≫ h ≫ e ≫ i = i ≫ 𝟙 T
```

## Full tactic state
```
C : Type u
inst✝¹ : Category.{v, u} C
inst✝ : HasWideEqualizers C
T : C
hT : ∀ (X : C), Nonempty (T ⟶ X)
endos : Type v := T ⟶ T
i : wideEqualizer id ⟶ T := wideEqualizer.ι id
this : Nonempty endos
X : C
a : wideEqualizer id ⟶ X
E : C := equalizer a (i ≫ Classical.choice ⋯)
e : E ⟶ wideEqualizer id := equalizer.ι a (i ≫ Classical.choice ⋯)
h : T ⟶ E := Classical.choice ⋯
⊢ i ≫ h ≫ e ≫ i = i ≫ 𝟙 T
```

## Proof so far (16 tactics)
```lean
let endos := T ⟶ T
let i := wideEqualizer.ι (id : endos → endos)
haveI : Nonempty endos := ⟨𝟙 _⟩
have : ∀ X : C, Unique (wideEqualizer (id : endos → endos) ⟶ X) := by
  intro X
  refine' ⟨⟨i ≫ Classical.choice (hT X)⟩, fun a => _⟩
  let E := equalizer a (i ≫ Classical.choice (hT _))
  let e : E ⟶ wideEqualizer id := equalizer.ι _ _
  let h : T ⟶ E := Classical.choice (hT E)
  have : ((i ≫ h) ≫ e) ≫ i = i ≫ 𝟙 _ := by
    rw [Category.assoc, Category.assoc]
    apply wideEqualizer.condition (id : endos → endos) (h ≫ e ≫ i)
  rw [Category.comp_id, cancel_mono_id i] at this
  haveI : IsSplitEpi e := IsSplitEpi.mk' ⟨i ≫ h, this⟩
  rw [← cancel_epi e]
  apply equalizer.condition
exact hasInitial_of_unique (wideEqualizer (id : endos → endos))
intro X
refine' ⟨⟨i ≫ Classical.choice (hT X)⟩, fun a => _⟩
let E := equalizer a (i ≫ Classical.choice (hT _))
let e : E ⟶ wideEqualizer id := equalizer.ι _ _
let h : T ⟶ E := Classical.choice (hT E)
have : ((i ≫ h) ≫ e) ≫ i = i ≫ 𝟙 _ := by
  rw [Category.assoc, Category.assoc]
  apply wideEqualizer.condition (id : endos → endos) (h ≫ e ≫ i)
rw [Category.comp_id, cancel_mono_id i] at this
haveI : IsSplitEpi e := IsSplitEpi.mk' ⟨i ≫ h, this⟩
rw [← cancel_epi e]
apply equalizer.condition
rw [Category.assoc, Category.assoc]
```

## Theorem
`CategoryTheory.hasInitial_of_weakly_initial_and_hasWideEqualizers` in `Mathlib/CategoryTheory/Limits/Constructions/WeaklyInitial.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.wideEqualizer.condition`
- `id`

## Premise signatures
### `CategoryTheory.Limits.wideEqualizer.condition` (commanddeclaration)
```lean
@[reassoc]
theorem wideEqualizer.condition (j₁ j₂ : J) : wideEqualizer.ι f ≫ f j₁ = wideEqualizer.ι f ≫ f j₂
```

### `id` (commanddeclaration)
```lean
@[inline] def id {α : Sort u} (a : α) : α
```

## Premise full source (with proof)
### `CategoryTheory.Limits.wideEqualizer.condition` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/WideEqualizers.lean`
```lean
@[reassoc]
theorem wideEqualizer.condition (j₁ j₂ : J) : wideEqualizer.ι f ≫ f j₁ = wideEqualizer.ι f ≫ f j₂ :=
  Trident.condition j₁ j₂ <| limit.cone <| parallelFamily f
```

### `id` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
The identity function. `id` takes an implicit argument `α : Sort u`
(a type in any universe), and an argument `a : α`, and returns `a`.

Although this may look like a useless function, one application of the identity
function is to explicitly put a type on an expression. If `e` has type `T`,
and `T'` is definitionally equal to `T`, then `@id T' e` typechecks, and Lean
knows that this expression has type `T'` rather than `T`. This can make a
difference for typeclass inference, since `T` and `T'` may have different
typeclass instances on them. `show T' from e` is sugar for an `@id T' e`
expression.
-/
@[inline] def id {α : Sort u} (a : α) : α := a

/--
Function composition is the act of pipelining the result of one function, to the input of another, creating an entirely new function.
Example:
```
```

## Transitive premise context (1-hop, 8/8 premises, ≈800 tokens)
### `CategoryTheory.Limits.parallelFamily` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/WideEqualizers.lean`
```lean
/-- `parallelFamily f` is the diagram in `C` consisting of the given family of morphisms, each with
common domain and codomain.
-/
def parallelFamily : WalkingParallelFamily J ⥤ C where
  obj x := WalkingParallelFamily.casesOn x X Y
  map {x y} h :=
    match x, y, h with
    | _, _, Hom.id _ => 𝟙 _
    | _, _, line j => f j
  map_comp := by
    rintro _ _ _ ⟨⟩ ⟨⟩ <;>
      · aesop_cat
```

### `Lean.Parser.Term.argument` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Term.lean`
```lean
def argument       :=
  checkWsBefore "expected space" >>
  checkColGt "expected to be indented" >>
  (namedArgument <|> ellipsis <|> termParser argPrec)
-- `app` precedence is `lead` (cannot be used as argument)
-- `lhs` precedence is `max` (i.e. does not accept `arg` precedence)
-- argument precedence is `arg` (i.e. does not accept `lead` precedence)
```

### `Lean.Parser.Command.universe` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Command.lean`
```lean
@[builtin_command_parser] def «universe»     := leading_parser
  "universe" >> many1 (ppSpace >> ident)
```

### `Module.Free.function` (commanddeclaration) at `Mathlib/LinearAlgebra/FreeModule/Basic.lean`
```lean
/-- The product of finitely many free modules is free (non-dependent version to help with typeclass
search). -/
instance function [Finite ι] : Module.Free R (ι → M) :=
  Free.pi _ _
```

### `inline` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
/--
`inline (f x)` is an indication to the compiler to inline the definition of `f`
at the application site itself (by comparison to the `@[inline]` attribute,
which applies to all applications of the function).
-/
@[simp] def inline {α : Sort u} (a : α) : α := a
```

### `Stream'.composition` (commanddeclaration) at `Mathlib/Data/Stream/Init.lean`
```lean
theorem composition (g : Stream' (β → δ)) (f : Stream' (α → β)) (s : Stream' α) :
    pure comp ⊛ g ⊛ f ⊛ s = g ⊛ (f ⊛ s) :=
  rfl
```

### `IO.Promise.result` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/System/Promise.lean`
```lean
/--
The result task of a `Promise`.

The task blocks until `Promise.resolve` is called.
-/
@[extern "lean_io_promise_result"]
opaque Promise.result (promise : Promise α) : Task α :=
  have : Nonempty α := promise.h
  Classical.choice inferInstance
```

### `Lean.Meta.Match.Example` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Meta/Match/Basic.lean`
```lean
inductive Example where
  | var        : FVarId → Example
  | underscore : Example
  | ctor       : Name → List Example → Example
  | val        : Expr → Example
  | arrayLit   : List Example → Example
```
