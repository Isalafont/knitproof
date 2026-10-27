# ADR 0012 — Interdire `Any` avec mypy

Complète l’[ADR 0001](0001-verifier-les-types-avec-mypy-strict.md).

## Contexte

`mypy --strict` laisse passer un `Any` écrit explicitement. Or un `Any` efface le typage là où le moteur et les structures échangées avec les modèles doivent rester explicites. Une règle « pas de `Any` » seulement écrite dérive, surtout avec des agents de code.

## Décision

Deux options s’ajoutent à `[tool.mypy]` de `pyproject.toml`, car aucune n’est incluse dans `--strict` :

- `disallow_any_explicit = true` : toute annotation `Any` explicite est refusée, dans `src` comme dans `tests`.
- `disallow_any_unimported = true` : mypy signale un type devenu `Any` parce qu’il n’a pas pu suivre son import, par exemple une sous-classe de `requests.Session` sans stubs, ou une annotation qui renvoie à ce type. `--strict` ne pose pas `ignore_missing_imports` : un import sans stubs échoue déjà avec `import-untyped`, et l’option fait doublon aujourd’hui. Elle servira le jour où un `[[tool.mypy.overrides]]` ajoutera `ignore_missing_imports = true` : les types de la bibliothèque deviendraient des `Any`, et l’option les ferait remonter.

Limite : une bibliothèque avec stubs qui renvoie `Any` est couverte en partie par `warn_return_any` (déjà dans `--strict`) et par `disallow_any_explicit`. Aucune option ne la couvre entièrement, sauf `disallow_any_expr`.

## Alternatives écartées

- La règle ruff `ANN401` : elle ne couvre que les annotations des paramètres et des retours.
- Une règle seulement écrite dans `AGENTS.md` : rien ne la vérifie.
- `disallow_any_expr` : trop bruyant.

## Conséquences

- `AGENTS.md` n’écrit pas « pas de `Any` » : le message de mypy suffit à orienter un agent.
- `tests/test_code_rules.py` prouve que les deux options mordent.
- Retirer l’une de ces options assouplit la vérification et demande un nouvel ADR (ADR 0001).
