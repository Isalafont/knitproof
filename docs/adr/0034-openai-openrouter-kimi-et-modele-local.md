# ADR 0034 — OpenAI, OpenRouter, Kimi et modèle local

Amende les ADR [0005](0005-acces-aux-modeles-via-pydanticai.md) et [0033](0033-anthropic-et-mistral-en-direct.md).

## Contexte

Mistral en direct est payant et l’évaluation exige un modèle ouvert ou souverain accessible sans agrégateur. CLA-62 élargit la couche `llm` au même patron que CLA-127.

## Décision

Décisions d’Isabelle du 13/11/2026.

| Fournisseur | Accès |
|---|---|
| OpenAI | `OpenAIResponsesModel`, la voie recommandée par la doc |
| OpenRouter | `OpenRouterModel` ; un seul hébergeur (`only`), sans repli (`allow_fallbacks` à faux) ; l’hébergeur rendu par la réponse est noté dans `ModelReading.host`, refus s’il manque |
| Kimi | en direct, `OpenAIChatModel` et `MoonshotAIProvider`, adresse toujours passée explicitement |
| Local | Ollama, `OllamaModel` ; nom avec étiquette explicite, `:latest` refusé |

- L’agrégateur sert à comparer, pas à prouver la souveraineté ; le modèle local est l’accès souverain appelé.
- Mistral en direct reste possible, non requis. Les appels `live` restent à la main.

## Alternatives écartées

- **`OpenAIChatModel` pour OpenRouter** : routage non typé, hébergeur non lu.
- **`OpenAIChatModel` pour OpenAI** : présenté comme « legacy » par la doc.
- **Kimi par OpenRouter seul** : ce n’est pas un accès en direct.
- **Payer Mistral** : un modèle local suffit pour l’accès souverain.
- **OpenGateLLM** (API générique compatible OpenAI) : reporté, aucun appel réel ni consommateur.

## Conséquences

- `ModelReading` gagne `host` ; le format de l’hébergeur rendu par OpenRouter est à prouver par l’appel `live`.
- Les extras `openai` et `openrouter` de pydanticAI entrent dans les dépendances.

## Sources

- pydanticAI, 13/11/2026 : https://pydantic.dev/docs/ai/models/openai/, https://pydantic.dev/docs/ai/models/openrouter/, https://pydantic.dev/docs/ai/models/overview/, https://pydantic.dev/docs/ai/models/ollama/, https://pydantic.dev/docs/ai/models/moonshotai/.
- OpenRouter et Ollama, 13/11/2026 : https://openrouter.ai/docs/features/provider-routing, https://docs.ollama.com/api/openai-compatibility, https://docs.ollama.com/modelfile.
- Kimi, 13/11/2026 : https://platform.kimi.ai/docs/guide/start-using-kimi-api, https://platform.kimi.ai/docs/guide/use-json-mode-feature-of-kimi-api, https://platform.kimi.ai/docs/models.
