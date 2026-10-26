# ADR 0007 — Decimal et arrondi unique

## Contexte

`float` donne des erreurs d’arrondi binaires. Les demi-mailles sont courantes (22,5 m pour 10 cm). Confondre 4 in et 10 cm décale le montage d’environ 1,6 % (architecture §8).

## Décision

- `Decimal` pour les longueurs, les jauges et les mailles comptées sur un échantillon.
- Des entiers pour les comptes du patron.
- Chaque longueur garde son unité (1 in = 2,54 cm exactement).
- Un seul arrondi métier, celui du montage, avec une règle paramétrée et tracée dans `CastOnResult`.
- Aucun `float` dans `engine`.

## Alternatives écartées

- `float` : 0,1 + 0,2 ≠ 0,3, et des comparaisons fragiles.
- `Fraction` : exacte, mais peu lisible en rendu et lourde avec Pydantic.
- Des arrondis à chaque étape : les erreurs s’accumulent, et le résultat n’est plus traçable.

## Conséquences

- La règle d’`AGENTS.md` « Aucun `float` dans `engine` : `Decimal` » et le typage strict (mypy, [ADR 0001](0001-verifier-les-types-avec-mypy-strict.md)) la font respecter.
- Le rendu français (« 43,2 cm ») vit dans les portes, pas dans `domain`.
