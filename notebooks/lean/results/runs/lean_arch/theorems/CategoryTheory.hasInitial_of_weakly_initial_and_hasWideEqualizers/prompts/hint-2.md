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
