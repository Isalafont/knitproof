# ADR 0009 — Découpage en couches

## Contexte

Le moteur doit rester testable sans modèle, et plusieurs portes (CLI, API, web) doivent partager un seul cœur.

## Décision

- Couches `domain`, `engine`, `library`, `llm`, `sources`, `app`, portes `cli`, `api`, `web`, et `evals`, selon le schéma et le tableau de l’architecture §5.
- Règle « deux portes, un seul cœur » : les portes n’atteignent le cœur que par `app`.
- Contrats vérifiés par import-linter (CLA-57), dans `[tool.importlinter]`, et prouvés par `tests/test_layer_contracts.py`.

## Alternatives écartées

- Un paquet unique : rien n’empêche `engine` d’importer `llm`.
- Une architecture hexagonale complète (ports et adaptateurs partout) : les couches et import-linter donnent déjà l’isolement du moteur ; des ports partout ajouteraient des interfaces sans second adaptateur à brancher.
- Des conventions documentées sans vérification : elles dérivent, surtout avec des agents de code.

## Conséquences

- Supprimer une couche oblige à modifier son contrat et l’architecture dans la même PR (`AGENTS.md`).
- Un contrat ne s’assouplit jamais pour faire passer un changement.
