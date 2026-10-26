# knitproof — guide de développement

## Commandes

- Installer : `uv sync`
- Tests : `uv run pytest`
- Lint : `uv run ruff check .` (corriger : `uv run ruff check --fix .`, formater : `uv run ruff format .`)

## Principes d’architecture

- Le cœur de calcul et les validateurs sont du Python pur, testables sans appel à un modèle.
- Le LLM ne produit que des structures typées (Pydantic), jamais de nombres non vérifiés.
- Une valeur déduite d’un modèle ou d’une photo est une hypothèse, avec sa provenance.
- Ne jamais modifier une valeur attendue d’un test ou d’une évaluation pour faire passer un résultat.

## Branches

- `main` est la production, `develop` l’intégration déployée sur la sandbox.
- Chaque ticket a sa branche, créée depuis `develop` et nommée comme la branche du ticket Linear.
- Une branche de travail revient sur `develop` par une PR ; `develop` passe sur `main` par une PR.
- Jamais de commit ni de push direct sur `main` ou `develop`.
- Vérifier la branche courante (`git branch --show-current`) juste avant chaque commit.

## Conventions

- TDD : un test qui échoue avant chaque comportement.
- Code et identifiants en anglais ; documentation et commits en français.
- Apostrophe typographique (’) et guillemets français (« ») dans tout texte.
- Commits courts, à l’impératif, 72 caractères maximum, sans mention de Claude.
- Décisions structurantes : un ADR dans `docs/adr/`.
