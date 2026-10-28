# ADR 0016 — Tailles d’aiguilles sans conversion

## Contexte

Une taille d’aiguilles s’écrit dans quatre systèmes (mm, US, UK, japonais). Convertir d’un système à l’autre exige une table de correspondance sourcée, qui n’existe pas encore (CLA-81). Deviner le système d’après le texte ou tirer des mm d’une taille US serait une valeur inventée.

## Décision

1. Le système (`mm`, `us`, `uk`, `jp`) est un champ explicite de `NeedleSize`, jamais déduit du texte. La notation d’origine est conservée.
2. Le `mm` est saisi par la personne et jamais calculé ; pour le système `mm`, il est lu dans la notation, ce qui n’est pas une conversion.
3. Aucune conversion entre systèmes sans table sourcée (CLA-81).
4. Deux systèmes différents ne se comparent pas, sauf si leur taille en mm est connue des deux côtés (écrite en mm, ou saisie à côté d’une autre notation). Sinon, le moteur émet un `warning` (raison `sizes_not_comparable`), pas un `needs_review`.
5. `cable_length` est facultatif pour `circular`, et refusé pour `straight` et `double_pointed`.

## Alternatives écartées

- Déduire le système du texte : une saisie ambiguë (« 6 ») serait devinée.
- Convertir avec une table intégrée au code : valeur non sourcée.
- `needs_review` pour des systèmes non comparables : aucune question n’a de réponse tant que la table manque.

## Conséquences

- `domain` et `engine` portent le contrôle ; les textes français des raisons sont rendus aux portes (CLA-69).
- La liste des tailles valides par système viendra avec CLA-81.
