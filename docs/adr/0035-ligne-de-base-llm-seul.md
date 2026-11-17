# ADR 0035 — Ligne de base « LLM seul »

Précise l’[ADR 0032](0032-protocole-d-evaluation-fige.md) ; s’appuie sur les ADR [0033](0033-anthropic-et-mistral-en-direct.md) et [0034](0034-openai-openrouter-kimi-et-modele-local.md).

## Contexte

CLA-188 mesure la première preuve de la thèse : le nombre de mailles qu’un LLM seul propose pour un bonnet. Le protocole fixe la mesure ; il reste la forme des passages, la température et la place du code.

## Décision

Décisions d’Isabelle du 17/11/2026.

- **Passages** : 3 par cas et par fournisseur, à température 0, avec le prompt `baseline-cast-on-v1` (sha256 `dcdf725c3f1ef38cce49c1e045b1894cf7c4755926e44dc87a232d9c79f3e303`), figé avant toute mesure `test`.
- **Température** : `KNITPROOF_<P>_TEMPERATURE` prime sur la globale ; `eval` refuse toute valeur différente de 0 et tout fournisseur sans valeur explicite. `omit` n’envoie rien (Sonnet 5.5 et Kimi la refusent) et le `ModelRun` note « non envoyée ».
- **Résultat** : k/N sur cas et passages, avec l’intervalle de Wilson à 95 %. Une réponse `null` ou refusée après relances est une abstention, jamais juste.
- **Verdict** : le moteur calcule le tour fini du montage rendu ; juste à ±1 cm du tour visé.
- **Abstention attendue** : sans échantillon ni étiquette, le moteur pose la question `gauge_missing` et ne calcule rien ; `expected` porte alors `abstain` à la place du montage, s’abstenir est juste et un nombre est faux (jauge inventée).
- **Pièges** : sur 15 cas `test`, 7 pièges (étiquette et échantillon bloqué, avant et après blocage, tour fini donné, jauge sur 5 cm, pouces, étiquette seule, rien du tout) ; 2 sur 5 en `dev`. L’aisance s’y dit en mots et en cm, jamais en %, comme on le dit en tricot. L’attendu vient toujours du moteur.
- **Cas** : `EvalCase.request` porte la demande au format de `calc` ; le tour visé et le montage attendus sont recalculés par le moteur dans un test, en plus du hachage.
- **Place du code** : les modèles de cas et de manifeste vont dans `app/eval_cases.py`, car `BeanieRequest` vit dans `app`. `cli` résout le chemin des données (`evals/data/`) et le passe à `app` : `app` ne nomme jamais `evals`.
- **Résultats** : un YAML daté sous `evals/results/`, à la racine, jamais écrasé.

## Alternatives écartées

- **Modèles de cas dans `domain`** : ils ne peuvent pas importer `BeanieRequest`.
- **`app` lit `evals/data/` lui-même** : une couche du dessus, invisible pour import-linter.
- **Attendu seulement dérivé** : une dérive du moteur passerait inaperçue.

## Conséquences

- L’ajout de `request` et de `cast_on_stitches` change le hachage des 20 cas ; l’exemple est re-signé.
- Le coût en euros sort du `ModelRun` jusqu’au rejeu en CI (`evaluation.md`).
- OpenRouter et Ollama n’ont aucune doc qui garantisse la température 0 : seul l’appel réel le prouve.

## Sources

- pydanticAI, 17/11/2026 : https://pydantic.dev/docs/ai/api/pydantic-ai/usage/, https://pydantic.dev/docs/ai/core-concepts/output/, https://pydantic.dev/docs/ai/api/pydantic-ai/settings/.
- Kimi, 17/11/2026 : https://platform.kimi.ai/docs/guide/kimi-k3-quickstart.
