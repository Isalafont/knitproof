# ADR 0014 — « Rang » plutôt que « tour » dans les textes

Remplace l’[ADR 0013](0013-format-yaml-fige-et-poursuite-sur-le-compte-calcule.md) sur la terminologie seulement.

## Contexte

L’ADR 0013 écrit « tour » pour un `Round`. Les patrons français disent « rang » (`architecture.md`, section 9), et le rapport de `knitproof verify` s’adresse à une personne qui tricote d’après un patron.

## Décision

1. Dans le texte en français (rapport, messages de validation, docstrings, tests, documentation), « rang » désigne un `Round`, y compris « rang d’ajustement ».
2. Le code garde `Round` et `adjustment_round`.
3. Une mesure garde « tour » : « tour de tête », « tour visé », « tour fini » sont des circonférences.

## Alternatives écartées

- Garder « tour » partout : le rapport ne parlerait pas comme les patrons.
- Renommer `Round` : le code est en anglais, et l’identifiant n’est pas en cause.

## Conséquences

- Les décisions de l’ADR 0013 ne changent pas ; seul son vocabulaire est amendé.
- Les assertions de libellé suivent le nouveau mot, sans changer aucune valeur numérique.
