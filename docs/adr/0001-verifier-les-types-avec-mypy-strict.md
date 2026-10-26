# ADR 0001 — Vérifier les types avec mypy strict

## Contexte

Les conventions du projet sont vérifiées automatiquement, pour des contributeurs humains comme pour des agents de code. Le typage en fait partie : le moteur déterministe doit rester prévisible, et les structures échangées avec les modèles de langage doivent être explicites.

## Décision

mypy `--strict` vérifie `src` et `tests`, en pre-commit et dans le job `tests` de la CI. La configuration vit dans `[tool.mypy]` de `pyproject.toml`.

## Alternatives écartées

- pyright : il dépend de Node, et son paquet PyPI le télécharge au premier lancement.
- Les vérificateurs plus récents (ty, pyrefly) : à réévaluer plus tard.

## Conséquences

- Toute fonction est annotée, tests compris.
- Le plugin `pydantic.mypy` sera activé à la tranche 0 de M1, avec Pydantic (`plugins = ["pydantic.mypy"]`).
- Un changement de configuration mypy qui assouplit la vérification demande un nouvel ADR.
