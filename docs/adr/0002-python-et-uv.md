# ADR 0002 — Python et uv

## Contexte

knitproof mêle un moteur de calcul et des appels à des modèles. L’autrice vient de Rails et veut monter en compétence sur l’écosystème IA. Le projet doit aussi s’aligner sur un projet public de référence.

## Décision

Python 3.13 (`requires-python = ">=3.13"`), uv pour l’environnement, les dépendances, le verrouillage (`uv.lock`) et l’exécution ([uv](https://docs.astral.sh/uv/)), pytest et ruff.

L’outillage suit celui d’[OpenGateLLM](https://github.com/etalab-ia/OpenGateLLM) :

- ruff et pytest figurent dans son [`pyproject.toml`](https://raw.githubusercontent.com/etalab-ia/OpenGateLLM/main/pyproject.toml) ;
- le dépôt contient un `uv.lock`.

OpenGateLLM accepte Python 3.12 et plus ; knitproof prend 3.13, car l’alignement porte sur l’outillage, pas sur la version.

## Alternatives écartées

- Rails : écosystème IA plus mince (pydanticAI, Pydantic, évaluation), et aucune montée en compétence Python (source : ticket CLA-51).
- Poetry : un second outil à apprendre, alors qu’uv remplace pip et Poetry et couvre l’environnement, le verrouillage, la synchronisation et l’exécution ([uv](https://docs.astral.sh/uv/)).
- pip seul : uv est un seul outil qui remplace pip, pip-tools et virtualenv ([uv](https://docs.astral.sh/uv/)).

## Conséquences

- Toute commande passe par `uv run` (`AGENTS.md`).
- Un changement de `pyproject.toml` impose `uv lock`, faute de quoi le commit est refusé.
- Le passage à Python 3.14 se fera par un changement de `requires-python`.
