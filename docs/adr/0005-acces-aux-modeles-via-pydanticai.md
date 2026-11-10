# ADR 0005 — Accès aux modèles via pydanticAI

## Contexte

M2 compare plusieurs modèles, dont au moins un ouvert ou souverain (`evaluation.md`).

## Décision

La couche `llm` passe par pydanticAI, qui ouvre plusieurs fournisseurs :

- toute API compatible OpenAI, par `OpenAIChatModel` et `OpenAIProvider(base_url=…)` ([doc](https://pydantic.dev/docs/ai/models/compatible-apis/)). C’est la voie prévue pour OpenGateLLM, qui expose une API compatible OpenAI ([doc](https://docs.opengatellm.org)). La documentation de pydanticAI ne la cite pas explicitement : l’ADR la présente comme le moyen retenu, sans prétendre à un fournisseur dédié ;
- Mistral, par son modèle dédié `MistralModel` et `MistralProvider`, avec l’extra `pydantic-ai-slim[mistral]` ([doc](https://pydantic.dev/docs/ai/models/mistral/)), et non par l’API compatible OpenAI ;
- un modèle local, par `OllamaModel` et `OllamaProvider` ([doc](https://pydantic.dev/docs/ai/models/ollama/)), ou vLLM par `VLLMProvider`.

Les sorties sont validées contre des modèles Pydantic par `output_type` d’`Agent` ([doc](https://pydantic.dev/docs/ai/core-concepts/output/)).

Il n’y a pas de modèle par défaut : il sera choisi d’après l’évaluation M2, dont le protocole est figé avant toute mesure.

## Alternatives écartées

- Le SDK propre à chaque fournisseur : un adaptateur par fournisseur, et une comparaison plus coûteuse.
- LangChain : il offre lui aussi des sorties structurées validées par Pydantic (`response_format`, [doc](https://docs.langchain.com/oss/python/langchain/structured-output)). Il est écarté pour sa surface (chaînes, intégrations, abstractions bien au-delà du besoin) et pour son style moins proche de Pydantic, déjà au cœur de `domain` et de FastAPI ; ce n’est pas une question de capacité.
- Choisir un modèle par défaut maintenant : ce serait contraire au protocole, figé avant toute mesure.

## Conséquences

- Changer de modèle revient à changer de configuration.
- La provenance (`extracted_by` : modèle, version, prompt) est posée par l’adaptateur (architecture §7).
- Les tests d’adaptateur tournent sans réseau, grâce à `TestModel` et `FunctionModel`, avec `ALLOW_MODEL_REQUESTS=False` ([doc](https://pydantic.dev/docs/ai/guides/testing/)).
- Les identifiants restent dans `.env`.
- D’autres fournisseurs (OpenAI, Anthropic, Kimi, OpenRouter…) peuvent s’ajouter dans la seule couche `llm`, sans toucher au moteur ni au domaine ; voir CLA-62.
