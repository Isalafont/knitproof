# ADR 0033 — Anthropic et Mistral en direct

## Contexte

L’[ADR 0005](0005-acces-aux-modeles-via-pydanticai.md) ouvre la couche `llm` à pydanticAI sans fournisseur retenu. CLA-127 la branche pour de bon et doit tracer le modèle qui a lu une source.

## Décision

Décisions d’Isabelle du 12/11/2026.

| Point | Valeur |
|---|---|
| Fournisseurs | Anthropic dès CLA-127 ; Mistral en direct, accès souverain |
| Identifiant du modèle | figé, lu dans l’environnement ; `-latest` refusé |
| Température | facultative : absente, rien n’est envoyé |
| Relances | `KNITPROOF_LLM_RETRIES`, obligatoire, ne borne que la sortie |
| Trace | `Provenance.extracted_by` est un `ModelReading`, posé par le code |

## Alternatives écartées

- **Une seule variable de modèle** : le contrôle réel de chaque fournisseur obligerait à éditer `.env` entre deux appels.
- **Température obligatoire** : Sonnet 5.5 répond 400 si elle est posée.
- **`-latest`** : la version lue changerait sans trace.

## Conséquences

- `ModelReading` (fournisseur, modèle, version rendue par la réponse, prompt et son empreinte) est exigé pour `model_inference` ; la bibliothèque YAML le refuse.
- Les tests passent par `TestModel` et `FunctionModel`, requêtes réelles interdites ; un test `live` par fournisseur se lance à la main.
- Le comportement d’une température refusée par un modèle reste à trancher à la ligne de base.

## Sources

- pydanticAI, 12/11/2026 : https://pydantic.dev/docs/ai/models/anthropic/, https://pydantic.dev/docs/ai/models/mistral/, https://pydantic.dev/docs/ai/guides/testing/, https://pydantic.dev/docs/ai/core-concepts/output/, https://pydantic.dev/docs/ai/api/settings/.
- Anthropic, Sonnet 5.5 : https://platform.claude.com/docs/en/models/sonnet-5-5/overview.
