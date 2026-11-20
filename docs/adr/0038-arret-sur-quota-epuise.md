# ADR 0038 — Arrêt sur quota épuisé

Précise l’[ADR 0036](0036-reessai-sur-erreur-passagere.md) (« Épuisement ») et complète l’[ADR 0037](0037-reprise-d-une-mesure-interrompue.md).

## Contexte

Quand le plafond de dépense mensuel d’Anthropic est atteint, l’API rend un 429 `rate_limit_error` sans `retry-after`. L’ADR 0036 le réessayait pour rien, comme une limite de débit, avant d’arrêter la mesure.

## Décision

Décision d’Isabelle du 20/11/2026.

- **Quoi** : un 429 d’Anthropic dont `error.details.error_code` vaut `enforced_spend_limit_reached` n’est pas réessayé ; `extract` lève `QuotaExhaustedError`, la cause est `__cause__`.
- **Tri** : sur ce champ, lu dans `ModelHTTPError.body`, seul code que la doc désigne pour le distinguer d’une limite de débit. Pour Anthropic seul.
- **Arrêt** : `eval` s’arrête sans résultat (code 3) sur « anthropic : quota épuisé », et le journal permet la reprise ([ADR 0037](0037-reprise-d-une-mesure-interrompue.md)). Le message ne promet pas de reprise à minuit : le plafond est mensuel.

## Alternatives écartées

- **Catégorie `ModelQuotaExceededError` de pydanticAI** : elle ne reconnaît pas ce 429, rangé en limite de débit.
- **Absence de `retry-after`** : non documenté comme critère.
- **Texte du message** : la doc demande de trier sur le code.

## Conséquences

- OpenRouter et les fournisseurs sans champ documenté restent réessayés comme un 429 de débit.
- Un 429 `ramp_limit_exceeded` ou sans `details` reste réessayé.

## Sources

Lues le 20/11/2026.

- https://platform.claude.com/docs/en/api/rate-limits#reaching-your-spend-cap
- https://platform.claude.com/docs/en/api/errors
- OpenRouter, sans champ distinctif : https://openrouter.ai/docs/api-reference/errors, https://openrouter.ai/docs/api-reference/limits
