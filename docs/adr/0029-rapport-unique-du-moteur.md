# ADR 0029 — Rapport unique du moteur

Complète l’[ADR 0013](0013-format-yaml-fige-et-poursuite-sur-le-compte-calcule.md) ; ferme le rapprochement annoncé par l’[ADR 0021](0021-table-de-reference-des-tailles-d-aiguilles.md).

## Contexte

Quatre types disent ce que le moteur constate : `Finding` (erreur prouvée), `Notice` (avis), `CastOnCheck` (montage proposé) et `NeedleCheck` (aiguilles). `calc` et `verify` doivent rendre la même chose, sans que chaque porte réécrive les textes.

## Décision

Décision d’Isabelle du 09/11/2026.

1. **`ReportEntry` commun.** Statut (`error`, `warning`, `needs_review`, `rejected`), code, rang, lignes de texte et `decided_by` (`engine`, `entered`, `library`).
2. **Construit depuis les types d’origine**, qui restent tels quels : `from_finding`, `from_notice`, `from_cast_on_check`, `from_needle_check` (`engine/report.py`).
3. **`Report`.** Entrées dans l’ordre d’arrivée, sans tri par statut ; questions en attente ; plan s’il existe. Même entrée, même rapport.
4. **Texte dans `engine`, mise en colonnes dans `cli`.** La porte ne décide d’aucun texte.

## Alternatives écartées

- Fusionner `Notice` dans `Finding` : refonte de tout le moteur, hors besoin.

## Conséquences

- `verify` et `calc` rendent un `Report` ; la sortie de `verify` ne change pas.
- `inputs`, `decisions` et les versions du moteur et de la bibliothèque restent à venir.
