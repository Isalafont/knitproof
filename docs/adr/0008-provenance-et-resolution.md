# ADR 0008 — Provenance et résolution par grandeur

## Contexte

Chaque valeur vient d’une source de fiabilité différente. Une valeur déduite d’un modèle est une hypothèse.

## Décision

Les trois règles de l’architecture §7 :

- La provenance est portée par l’objet d’entrée.
- Quand un modèle a lu la source, l’adaptateur pose `extracted_by` ; le modèle ne déclare jamais sa propre provenance.
- Une valeur manquante devient une `PendingQuestion`.

`Sourced[T]` est réservé aux paramètres résolus et aux constats. L’ordre de confiance est défini grandeur par grandeur (tableau du §7).

## Alternatives écartées

- `Sourced[T]` sur chaque champ : verbeux, et redondant avec l’objet d’entrée.
- Un ordre de confiance global entre sources : faux selon la grandeur (une étiquette vaut pour la composition, pas pour la jauge de la personne).
- Une estimation silencieuse des valeurs manquantes : contraire au principe « une valeur manquante est demandée ».

## Conséquences

- Effacer toutes les données d’une source est possible ([ADR 0011](0011-licence-api-ravelry.md)).
- Le `Report` liste les entrées résolues et leur provenance.
