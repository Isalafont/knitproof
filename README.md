# knitproof

> Generate, verify and validate knitting patterns with AI — the model proposes, the engine proves.

knitproof vérifie des patrons de tricot. Un LLM extrait du patron une structure typée ; un moteur de calcul déterministe recalcule chaque section et signale les incohérences (« rang 31 : 87 mailles annoncées, 89 attendues »), avec leur provenance. Les cas ambigus reviennent à une personne.

**Statut : cadrage (M0).** Le plan détaillé et le schéma d’architecture sont en cours de rédaction dans [`docs/architecture.md`](docs/architecture.md).

## Principes

1. Signaux déterministes d’abord : ne pas demander à un LLM de juger ce qu’un calcul sait prouver.
2. Un format intermédiaire typé avant toute prose.
3. Évaluations dès le départ, reproductibles et protégées contre les optimisations artificielles.
4. Traçabilité : entrées, modèles, règles, coûts et corrections.
5. Le LLM propose, le moteur calcule et contrôle, l’humain arbitre ce qui ne se mesure pas.

## Feuille de route

| Jalon | Livrable |
|---|---|
| M0 — Cadrage | Plan détaillé, schéma d’architecture, décisions d’architecture (ADR) |
| M1 — Cœur déterministe | Calculateur et validateurs (bonnet), bibliothèque de points réduite, tests |
| M2 — Extraction et évaluation | Patron PDF → structure typée, jeu d’erreurs injectées, mesures |
| M3 — Industrialisation | API FastAPI, Docker, CI, mesures publiées |

Plus tard : reconnaissance des points par photo, bibliothèque de points complète et RAG, génération de patrons, constructions multiples, raglan, gradation multi-tailles.

## Développement

```sh
uv sync
uv run pytest
uv run ruff check .
```

## Licence

MIT
