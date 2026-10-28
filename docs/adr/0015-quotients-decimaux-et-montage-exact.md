# ADR 0015 — Quotients décimaux à précision fixe, montage décidé exactement

Complète l’[ADR 0007](0007-decimal-et-arrondis.md).

## Contexte

Le montage (CLA-65) convertit une largeur en mailles : un quotient, souvent non fini (92 m × 10,16 cm / 22 = 42,4872… cm). Le garde `tests/test_engine_no_float.py` refuse le jeton `/` dans `engine`, et un `Decimal` calculé sans contexte explicite arrondirait un long produit en silence. Il faut une précision connue, tracée, et une règle d’arrondi du montage qui n’en dépende pas.

## Décision

1. Les quotients (nombre brut, largeur finie, jauge pour 10 cm) sont des `Decimal` à 28 chiffres significatifs, arrondis `ROUND_HALF_EVEN`, pour la trace seulement. Ils passent par `DIVISION.divide(a, b)` et non par `/`. Le garde reste inchangé.
2. Les produits se calculent sous `EXACT`, un contexte qui lève `Inexact` ou `Rounded` plutôt que d’arrondir : un produit trop long échoue bruyamment.
3. Le montage se décide exactement, par produits croisés, sans passer par un quotient : on compare `|n × largeur_échantillon − largeur × mailles_échantillon|` pour les candidats voisins qui respectent le point (multiple et reste).
4. Cet arrondi des quotients n’est pas un second arrondi métier : c’est une limite de représentation, sans effet sur le montage, décidé exactement. L’[ADR 0007](0007-decimal-et-arrondis.md) (« un seul arrondi métier ») reste vraie.
5. `EXACT` et `DIVISION` vivent dans `domain` (`domain/measure.py`), parce que `Length.in_cm` et `stitches_per_10_cm` y calculent déjà, et que `engine` peut importer `domain`.
6. Le contournement de `/` par `DIVISION.divide` se justifie par le refus des `float` par `DIVISION` (`TypeError`), comportement que seul un essai confirme et que le test de `stitches_for_width` fige.

Décision d’Isabelle du 28/10/2026 (option a).

## Alternatives écartées

- `Fraction` : exacte, mais contraire à l’ADR 0007, incompatible avec `Decimal` et mal gérée par Pydantic.
- Arrondir le quotient brut pour choisir le montage : une égalité peut disparaître selon la précision.
- Affaiblir le garde pour tolérer `/` sur `Decimal` : contraire à `AGENTS.md`.

## Conséquences

- Le nombre brut et la largeur finie sont des valeurs de trace ; seule une porte arrondit pour l’affichage.
- Un entier absurde (plus de vingt chiffres) fait lever `decimal.Inexact` ; la porte d’entrée l’attrapera (CLA-69).
