# ADR 0003 — Format intermédiaire typé avant tout calcul

## Contexte

Un modèle de langage propose des nombres plausibles sans les calculer (journal de cadrage : 3 ans contre adulte). Tout ce qui entre dans le moteur doit donc être une structure validée, et non du texte.

## Décision

- Toute entrée du moteur est un modèle Pydantic de `domain` : `BeanieSpecification` pour une demande, `Pattern` pour un patron. Ces modèles sont validés avant tout calcul.
- Le nom `BeanieSpecification` vient de la portée : en anglais, « hat » regroupe béret, cloche, earflap… alors que knitproof ne vise que les beanies (bonnets ajustés).

## Alternatives écartées

- Texte libre ou dictionnaires non typés : aucune validation, et une erreur découverte trop tard.
- `PatternSpecification` (nom initial du ticket) : il confond la demande et le patron, qui sont deux structures distinctes (architecture §6).
- `HatSpecification` : nom trop large pour la portée réelle.

## Conséquences

- Le prochain vêtement (béret, pull…) aura sa propre spécification typée, pas une variante de `BeanieSpecification`.
- Le modèle de langage (M2) produit ces structures et rien d’autre ([ADR 0004](0004-moteur-deterministe-sans-llm.md)).
- `BeaniePlan`, `ResolvedBeanieInputs`, `resolve_beanie_inputs` et `plan_beanie` suivent le même nom.
- Aucun code n’utilise encore ces noms ; ils naissent avec leurs tests en M1.
