# knitproof — guide de développement

## Commandes

- Installer : `uv sync`, puis `uv run pre-commit install`
- Tests : `uv run pytest`
- Lint : `uv run ruff check .` et `uv run ruff format --check .` (corriger : `uv run ruff check --fix .`, formater : `uv run ruff format .`)
- Contrats de couches : `uv run lint-imports`
- Types : `uv run mypy`
- Les hooks pre-commit et la CI lancent ces outils en `uv run --locked` : après un changement de dépendances dans `pyproject.toml`, lancer `uv lock`, sinon le commit est refusé ; après tout autre changement de `pyproject.toml`, `uv lock --check` le confirme.

## Principes d’architecture

- Le cœur de calcul et les validateurs sont du Python pur, testables sans appel à un modèle.
- Le LLM ne produit que des structures typées (Pydantic), jamais de nombres non vérifiés.
- Une valeur déduite d’un modèle ou d’une photo est une hypothèse, avec sa provenance.

## Couches

Détail et schéma dans `docs/architecture.md`, section 5. Les contrats vivent dans `[tool.importlinter]` de `pyproject.toml`.

| Couche | Rôle |
|---|---|
| `domain` | Modèles de données et invariants, aucune dépendance interne |
| `engine` | Calculs purs, ni fichier, ni réseau, ni modèle |
| `library` | Bibliothèques YAML sourcées |
| `llm` | Extraction par les modèles, jamais importé par `engine` |
| `sources` | Données externes (Ravelry), optionnelles |
| `app` | Cas d’usage, seul point d’entrée des portes |
| `cli`, `api`, `web` | Portes d’entrée, sans logique métier |
| `evals` | Jeux d’évaluation et mesures |

- Une couche dépend de celles du dessous, jamais de celles du dessus ni de ses voisines de même niveau.
- `cli`, `api`, `web` et `evals` peuvent importer `domain`. Ils n’atteignent `engine`, `library`, `llm` et `sources` que par `app` (et `llm` pour `evals`).
- Supprimer le paquet d’une couche casse volontairement le contrat : mettre à jour le contrat et l’architecture dans la même PR.

## Typage

- Annotations partout, tests compris ; `mypy --strict` sur `src` et `tests` (voir les ADR 0001 et 0012).
- Aucun `float` dans `engine` : `Decimal`.

## Code Python

Ce que ruff et mypy ne vérifient pas :

- Dans une classe : méthodes spéciales, puis publiques, puis privées ; l’appelant au-dessus de l’appelé ; jamais d’ordre alphabétique.
- Données métier : un modèle Pydantic, pas un `dict`.

## Tests

- TDD : un test qui échoue avant chaque comportement, avec pytest.
- Hypothesis pour les invariants du moteur.
- Les adaptateurs LLM se testent sans réseau.
- `tests/test_layer_contracts.py` prouve que les contrats mordent : ne jamais l’affaiblir.
- `tests/` n’a pas d’`__init__.py` : deux fichiers de test de même nom font échouer mypy (« Duplicate module »), donc des noms uniques.

## Règles pour tous les agents

- Ne jamais modifier une valeur attendue d’un test ou d’une évaluation pour faire passer un résultat.
- Toute valeur de bibliothèque est sourcée.
- Aucun nombre venu d’un modèle sans passage par le moteur.
- Ne jamais assouplir un contrat import-linter ou une option mypy pour faire passer un changement.
- Dans `.claude/`, seuls `skills/` et `settings.json` sont versionnés ; jamais `.claude/plans/`.
- `.claude/settings.json` pré-autorise les lectures, les cinq contrôles, les commandes git locales, le push d’une branche de travail et les PR vers `develop`.
- L’agent commite sans validation, pousse et ouvre une PR prête (pas de brouillon) vers `develop`. Il la merge dès qu’Isabelle a lancé le test de la PR et dit « ok », CI verte. Avant le merge, les cases producteur du ticket sont cochées dans Linear ; les cases testeur et la DOD le sont après le « ok » d’Isabelle (voir `implement-slice`).
- Écrire dans Linear demande toujours un accord.
- Commits sans mention d’un agent de code (Claude, Codex…).

## Branches

- `main` est la production, `develop` l’intégration déployée sur la sandbox.
- Chaque ticket a sa branche, créée depuis `develop` et nommée comme la branche du ticket Linear.
- Une branche de travail revient sur `develop` par une PR ; `develop` passe sur `main` par une PR.
- Jamais de commit ni de push direct sur `main` ou `develop` : un ruleset GitHub le refuse.
- GitHub supprime la branche distante au merge ; en local, `git fetch -p` puis `git branch -d <branche>`.
- Une PR ne merge que si la CI (`.github/workflows/ci.yml`) est verte ; `main` n’accepte que des PR depuis `develop`.
- Vérifier la branche courante (`git branch --show-current`) juste avant chaque commit.

## Conventions

- Code et identifiants en anglais ; documentation et commits en français.
- Apostrophe typographique (’) et guillemets français (« ») dans tout texte.
- Commits courts, à l’impératif, 72 caractères maximum.
- Décisions structurantes : un ADR dans `docs/adr/`.
- Chaque PR met à jour le README et `docs/` quand elle change un comportement, une commande, une installation, un process ou une décision. Une doc en retard sur le code est un bug.
