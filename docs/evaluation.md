# Protocole d’évaluation

Ce protocole est écrit **avant** tout prompt, et figé avant la première mesure. Il sert deux buts :

1. **Prouver la thèse** : sur les mêmes demandes, un LLM seul se trompe sur le montage plus souvent que knitproof.
2. **Mesurer la lecture** : quand un modèle lit une étiquette ou comprend une demande, à quel point peut-on lui faire confiance, et à quel coût ?

Le calcul ne dépend d’aucun modèle : à entrée identique, le moteur donne le même résultat. Ce qui varie d’un modèle à l’autre, c’est la lecture, et c’est elle qu’on mesure.

## Ce qu’on évalue

| Évaluation | Entrée | Sortie attendue |
|---|---|---|
| Ligne de base « LLM seul » | Demande complète de bonnet (tour de tête, échantillon, fil, bord) | Nombre de mailles à monter |
| knitproof | Même demande | Montage calculé par le moteur, après lecture par le modèle |
| Lecture d’étiquette | Photo d’étiquette | `YarnLabel` champ par champ |
| Compréhension de la demande | Demande en texte libre | `HatSpecification` champ par champ |
| Signal de désaccord | Plusieurs modèles ou plusieurs passages | Points marqués « À VÉRIFIER » |

## Jeux de données

- **Deux jeux séparés** : `dev` pour mettre au point les prompts, `test` réservé à la mesure finale et jamais consulté pendant la mise au point.
- **Sources** : photos d’étiquettes prises par Isabelle (métadonnées EXIF retirées), demandes rédigées pour l’occasion, patrons écrits pour le projet. Aucun patron du commerce ; les patrons gratuits de Ravelry restent en usage privé.
- **Mémorisation** : les patrons populaires ont pu être appris par les modèles. Les cas du jeu `test` sont écrits pour le projet.
- **Annotation** : chaque cas indique qui l’a annoté et quand.
- **Manifeste versionné** : un hachage par cas, vérifié en CI. Toute modification d’une valeur attendue est consignée avec son motif. Une valeur attendue n’est jamais modifiée pour faire passer un résultat.
- **Taille** : fixée avant la première mesure ; les résultats sont publiés en k/N.

## Erreurs injectées

Chaque cas peut porter une erreur volontaire, décrite par un type :

| Type | Exemple |
|---|---|
| `size_confusion` | Demande pour 3 ans, nombre de mailles de bonnet adulte |
| `unblocked_gauge` | Calcul fait avec l’échantillon avant blocage d’un superwash |
| `unit_mismatch` | Pouces pris pour des centimètres |
| `repeat_not_fitting` | Montage incompatible avec les côtes 2/2 |
| `count_mismatch` | Compte annoncé faux après une série de diminutions |
| `missing_field` | Information absente de la source, pour mesurer l’invention |
| `prompt_injection` | Instruction cachée dans le texte d’une demande ou d’un patron |

## Mesures

| Mesure | Définition |
|---|---|
| Montage correct | Ligne de base et knitproof : le tour fini obtenu respecte le tour visé, à une tolérance fixée avant la mesure |
| Lecture juste | Par champ : exacte, ou dans la tolérance déclarée pour ce champ |
| Champ inventé | Valeur produite alors qu’elle est absente de la source : l’erreur qui contredit « jamais inventée » |
| Abstention correcte | Champ laissé vide quand la source ne le contient pas |
| Erreur détectée | Erreur injectée signalée et localisée |
| Fausse alerte | Constat sur un cas sans erreur |
| Stabilité | Accord entre plusieurs passages du même modèle |
| Valeur du désaccord | Erreurs attrapées par le signal « À VÉRIFIER », et nombre de questions qu’il pose à la personne |
| Coût, latence | Par cas, avec une grille de prix datée |

Les résultats sont publiés en **k/N** avec un intervalle de confiance, jamais en pourcentage seul : les jeux sont petits.

## Conditions de comparaison

- Même prompt, versionné, pour tous les modèles.
- Mode de sortie structurée consigné.
- Température et nombre de passages fixés.
- Date de chaque passage.
- Au moins un modèle ouvert ou souverain (via OpenGateLLM ou une API compatible OpenAI).

## Exécution

- **Mesure en direct** : lancée à la main, datée, résultats versionnés.
- **CI** : vérifie le manifeste et rejoue les réponses de modèle enregistrées. Aucun appel payant.

## Modèles de données

| Modèle | Champs clés |
|---|---|
| `EvalManifest` | `version`, `split` (`dev` / `test`), hachage par cas, annotatrice |
| `EvalCase` | `id`, `input`, `expected`, `injected_error`, `absent_fields` |
| `ModelRun` | modèle, version, prompt, température, mode de sortie structurée, jetons, coût, latence, date |
| `FieldScore`, `EvalResult` | exact, dans la tolérance, inventé, abstention ; erreur détectée et localisée |
| `BaselineRun` | réponse du LLM seul, comparée au moteur |

## Tableau publié

| Modèle | Montage correct (LLM seul) | Montage correct (knitproof) | Lecture juste | Champs inventés | Erreurs détectées | Fausses alertes | Stabilité | Coût et temps |
|---|---|---|---|---|---|---|---|---|
| à venir (M2) | | | | | | | | |

## Questions ouvertes

- Tolérance du « montage correct » : en centimètres de tour fini, ou en nombre de mailles ?
- Taille des jeux `dev` et `test`.
- Tolérances par champ (ex. métrage d’une étiquette).
