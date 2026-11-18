# ADR 0036 — Réessai sur erreur passagère

Complète l’[ADR 0033](0033-anthropic-et-mistral-en-direct.md) et l’[ADR 0035](0035-ligne-de-base-llm-seul.md).

## Contexte

Une limite de débit passagère (429) ou une panne de fournisseur (5xx) arrêtait toute la mesure `eval`, sans résultat. Les SDK `openai` et `anthropic` réessaient déjà 2 fois en silence : le nombre d’essais réels était invisible dans la mesure.

## Décision

Décision d’Isabelle du 17/11/2026.

- **Quoi** : une réponse 429 ou 5xx est réessayée, au plus `KNITPROOF_LLM_HTTP_RETRIES` fois ; tout autre statut n’est appelé qu’une fois. Le tri se fait sur `ModelHTTPError.status_code`, jamais sur la classe.
- **Comment** : une boucle de `llm/extract.py` autour de l’appel, `sleep` et `clock` injectés, sans nouvelle dépendance.
- **Attente** : `KNITPROOF_LLM_HTTP_WAIT` × 2^(essai − 1), portée au `Retry-After` s’il est plus long, plafonnée à 60 s.
- **SDK** : `ModelSettings(max_retries=0)` est envoyé à chaque appel ; seule la boucle réessaie. Un test sans réseau compte les requêtes reçues par chaque fournisseur.
- **Trace** : `attempts` dans le `ModelRun` ; `None` pour les mesures d’avant ; la latence ne compte que l’essai qui répond.
- **Épuisement** : `TransientCallError` arrête la mesure, sans résultat partiel ; le journal des passages acquis permet de la reprendre ([ADR 0037](0037-reprise-d-une-mesure-interrompue.md)).

## Alternatives écartées

- **tenacity et `pydantic_ai.retries`** : un extra et de nouvelles dépendances pour quelques lignes.
- **`max_retries` des SDK relevé** : un réglage par SDK, Mistral à part, attente non injectable.
- **Réessai des erreurs réseau** : hors du besoin constaté ; à rouvrir sur un cas réel.

## Conséquences

- Les deux variables sont obligatoires : sans elles, `eval` refuse de démarrer.
- Pire cas par appel avec 3 réessais et 2 s : 2 + 4 + 8 = 14 s.

## Sources

- pydanticAI, `exceptions` et `settings` (`max_retries`), 17/11/2026 : https://pydantic.dev/docs/ai/api/pydantic-ai/exceptions/, https://pydantic.dev/docs/ai/api/pydantic-ai/settings/.
- SDK `openai` 3.50.0, `anthropic` 2.8.0, `mistralai` 3.7.0 : réessais par défaut lus dans le code installé, 17/11/2026.
