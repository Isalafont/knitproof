# ADR 0010 — Mélanges de fibres

## Contexte

Un fil est souvent un mélange (par exemple 80 % mérinos, 20 % polyamide, d’après le journal de cadrage). La bibliothèque décrit des fibres pures (`FiberProfile`).

## Décision

- Le comportement d’un mélange (détente au blocage, modulation de l’aisance) est la moyenne des profils de ses fibres, pondérée par la part de chacune (`FiberComposition`, somme = 100).
- Le calcul se fait en `Decimal` dans `engine`.
- Une fibre absente de la bibliothèque viole l’invariant « fibres connues » de `FiberComposition` (architecture §6) ; une fibre non validée rend le résultat `needs_review`.
- L’ADR fixe la règle, pas les nombres : les profils et leurs sources arrivent à la tranche 4 de M1.

## Alternatives écartées

- La fibre dominante : elle ignore une part minoritaire qui change le comportement (un polyamide qui limite la détente, par exemple), et le seuil de dominance est arbitraire.
- Des profils sourcés par mélange : combinaisons trop nombreuses, sources rares.

## Conséquences

- Le principe d’[architecture §11, « Limites assumées »](../architecture.md#11-limites-assumées) s’applique : « Aucun calcul ne remplace un tricot-test : le tombé, le confort, la tenue et l’esthétique restent à juger par une personne ». Un tricot-test juge le résultat d’un mélange.
- La question 8 de `plan.md` est tranchée.
