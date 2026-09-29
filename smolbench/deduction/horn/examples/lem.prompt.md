Prove the goal from the facts using the library rules. The goal is always provable from the facts and the library rules.

## Facts
desu(leb)
gapor(leb)
pari(leb)
buzef(leb)
pebad(leb)
dudi(leb)
ruma(leb)

## Library
sedu(x) ∧ pari(x) → fogan(x)
gidu(x) ∧ desu(x) → rarep(x)
lige(x) ∧ sobeg(x) → ketu(x)
koze(x) → sedu(x)
rarep(x) ∧ gapor(x) → gipe(x)
gidu(x) → pigi(x)
gipe(x) → sobeg(x)
dudi(x) ∧ koze(x) → sedu(x)
ketu(x) → gari(x)
pigi(x) → gipe(x)
dudi(x) → kuvep(x)
sobeg(x) ∧ ruma(x) → minu(x)
lige(x) ∧ pari(x) → gari(x)
gidu(x) ∧ koze(x) → kedu(x)
rarep(x) → minu(x)
rarep(x) ∧ pebad(x) → sobeg(x)
rarep(x) ∧ ruma(x) → minu(x)
sedu(x) ∧ pari(x) → dozu(x)
desu(x) → koze(x)
minu(x) ∧ dudi(x) → fozip(x)
fogan(x) → gidu(x)
kuvep(x) → sedu(x)
vapo(x) → kedu(x)
sobeg(x) → minu(x)
kana(x) → gidu(x)
pebad(x) → sate(x)
sate(x) → sedu(x)
dudi(x) ∧ pebad(x) → sedu(x)
sedu(x) → vapo(x)
sedu(x) ∧ gapor(x) → gidu(x)
kedu(x) → rarep(x)
dozu(x) ∧ sedu(x) → kana(x)
fozip(x) → lige(x)
vapo(x) → gidu(x)
minu(x) ∧ buzef(x) → lige(x)
dozu(x) → vapo(x)

## Goal
gari(leb)

## Answer format
One step per line, nothing else:
derive <atom> from <atom>[, <atom>]
A step applies one library rule with x set to one constant. The atoms after `from` are exactly that rule's body atoms for that constant, each a fact or an atom derived on an earlier line. The atom after `derive` is the rule's head for the same constant. Write every atom as predicate(constant). The last line derives the goal.
