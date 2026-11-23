# ADR 0039 — Répondre à une question par une décision

Complète l’[ADR 0029](0029-rapport-unique-du-moteur.md) (`Report.decisions`, annoncé « à venir »).

## Contexte

`calc` pose des questions en attente, mais on n’y répondait qu’en renommant une clé à la main : le choix, sa date et son motif étaient perdus. La `Decision` de l’architecture n’existait pas dans le code.

## Décision

Décisions d’Isabelle du 18/11/2026 (mécanisme générique) et du 23/11/2026 (seule la question du blocage, aux choix « après lavage » et « avant lavage »).

- **Forme** : `decisions:` dans la demande, une entrée `question`, `choice`, `decided_on`, `reason` facultatif.
- **Date** : `decided_on` est obligatoire et saisie, jamais lue sur l’horloge : « même entrée, même rapport » (ADR 0029, qui ne parle pas de l’horloge).
- **Application** : `app` passe les décisions à un registre ; chaque étape qui pose une question lui demande la décision de même code, qui est alors consommée. Le moteur reste pur.
- **Refus** : une option hors de celles de la question, ou une décision jamais consommée, est une erreur de saisie (code 3).
- **Provenance** : `DecidedBy.PERSON` (« votre choix ») est la provenance `person_decision` ; `Report.decisions` porte les décisions consommées.
- **Périmètre** : seule `gauge_blocking_unknown` se répond ainsi. Une autre question s’ajoute en déclarant son code et ses options, en l’ajoutant à `ANSWERABLE_QUESTIONS` (`app/decisions.py`) et en écrivant l’étape qui la consomme.

## Alternatives écartées

- **Décision hors de la demande** (base, session) : le rapport ne se rejouerait plus à l’identique.
- **Registre sans liste des codes répondables** : `cli` ne saurait pas quelles questions afficher avec leur code ; la liste explicite est le choix retenu.
- **Valeur libre dans une décision** : les questions sans options se règlent en remplissant le champ de la demande.

## Conséquences

- Le renommage de `unknown_blocking` en `after_blocking` ou `before_blocking` reste valide, au même résultat.
- `calc` affiche le code et les choix des seules questions qui se répondent par une décision.
- Les empreintes des cas d’évaluation sont inchangées : `decisions` vide n’est pas écrit.
