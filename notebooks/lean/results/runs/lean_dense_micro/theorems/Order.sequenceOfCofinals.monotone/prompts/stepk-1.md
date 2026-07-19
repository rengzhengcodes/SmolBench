## Current goal
```
⊢ sequenceOfCofinals p 𝒟 n ≤
    match some val✝ with
    | none => sequenceOfCofinals p 𝒟 n
    | some i => Cofinal.above (𝒟 i) (sequenceOfCofinals p 𝒟 n)
```

## Full tactic state
```
case hf.some
P : Type u_1
inst✝¹ : Preorder P
p : P
ι : Type u_2
inst✝ : Encodable ι
𝒟 : ι → Cofinal P
n : ℕ
val✝ : ι
⊢ sequenceOfCofinals p 𝒟 n ≤
    match some val✝ with
    | none => sequenceOfCofinals p 𝒟 n
    | some i => Cofinal.above (𝒟 i) (sequenceOfCofinals p 𝒟 n)
```
