# ADR 0004 — Moteur de calcul déterministe sans LLM

## Contexte

La thèse du projet est « le modèle propose, le moteur prouve, la personne arbitre » (architecture §1 et §2).

## Décision

- `engine` est du Python pur, sans fichier, réseau ni modèle : même entrée, même rapport (`Report` déterministe).
- Le modèle ne produit que des structures, jamais un nombre de mailles ni un verdict.
- Tout nombre proposé par un modèle passe par le moteur, qui l’accepte ou le rejette.

## Alternatives écartées

- Un LLM qui calcule, avec ou sans vérification a posteriori : il est non déterministe et invente des nombres plausibles.
- Un LLM avec outil de calcul (function calling) : le calcul serait juste, mais le choix des paramètres resterait opaque et sans provenance.

## Conséquences

- Le contrat import-linter interdit `engine` → `llm` ([ADR 0009](0009-decoupage-en-couches.md)).
- Les tests du moteur tournent sans réseau.
- L’évaluation mesure la lecture, pas le calcul (`evaluation.md`).
- Une injection de prompt ne peut pas changer un compte (architecture §10).
