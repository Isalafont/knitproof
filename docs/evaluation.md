# Protocole d’évaluation

Ce protocole est écrit **avant** tout prompt, et figé avant la première mesure. Il sert deux buts :

1. **Prouver la thèse** : sur les mêmes demandes, un LLM seul se trompe sur le montage plus souvent que knitproof.
2. **Mesurer la lecture** : quand un modèle lit une étiquette ou comprend une demande, à quel point peut-on lui faire confiance, et à quel coût ?

Le calcul ne dépend d’aucun modèle : à entrée identique, le moteur donne le même résultat. Ce qui varie d’un modèle à l’autre, c’est la lecture, et c’est elle qu’on mesure.

Figé le 12/11/2026 ([ADR 0032](adr/0032-protocole-d-evaluation-fige.md)). Toute modification s’inscrit dans « Modifications », datée, avec son motif.

## Ce qu’on évalue

| Évaluation | Entrée | Sortie attendue |
|---|---|---|
| Ligne de base « LLM seul » | Demande complète de bonnet (tour de tête, échantillon, fil, bord) | Nombre de mailles à monter |
| knitproof | Même demande | Montage calculé par le moteur, après lecture par le modèle |
| Lecture d’étiquette | Photo d’étiquette | `YarnLabel` champ par champ |
| Compréhension de la demande | Demande en texte libre | `BeanieSpecification` champ par champ |
| Signal de désaccord | Plusieurs modèles ou plusieurs passages | Points marqués « À VÉRIFIER » |

## Jeux de données

- **Deux jeux séparés** : `dev` pour mettre au point les prompts, `test` réservé à la mesure finale et jamais consulté pendant la mise au point.
- **Sources** : photos d’étiquettes prises par Isabelle (métadonnées EXIF retirées), demandes rédigées pour l’occasion, patrons écrits pour le projet. Aucun patron du commerce ; les patrons gratuits de Ravelry restent en usage privé.
- **Mémorisation** : les patrons populaires ont pu être appris par les modèles. Les cas du jeu `test` sont écrits pour le projet.
- **Annotation** : chaque entrée du manifeste indique qui a annoté le cas et quand.
- **Manifeste versionné** : un hachage par cas, vérifié en CI. Toute modification d’une valeur attendue est consignée avec son motif. Une valeur attendue n’est jamais modifiée pour faire passer un résultat.
- **Taille** : 5 cas `dev` et 15 cas `test` par évaluation (ligne de base, étiquette, demande) ; résultats en k/N.
- **Emplacement** : `src/knitproof/evals/data/<split>/`, un cas par fichier YAML, un `manifest.yaml` par split.
- **Cas d’exemple** : l’`id` préfixé `exemple-` marque un cas d’exemple de format, jamais compté dans les 5 cas `dev` d’une évaluation réelle.

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
| Montage correct | Ligne de base et knitproof : le tour fini obtenu est à ±1 cm du tour visé (tête et aisance comprises) |
| Lecture juste | Par champ : exactement la valeur de la source ; nombres tels qu’imprimés, texte comparé sans casse ni espaces superflus ; aucune tolérance ; champ absent de la source : attendu vide (voir Abstention correcte) |
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
| `EvalManifest` | `version`, `split` (`dev` / `test`), et par entrée : `id` du cas, hachage SHA-256, annotatrice, date |
| `EvalCase` | `id`, `input`, `expected`, `injected_error`, `absent_fields` |
| `ModelRun` | modèle, version, prompt, température, mode de sortie structurée, jetons, coût, latence, date |
| `FieldScore`, `EvalResult` | exact, inventé, abstention ; erreur détectée et localisée |
| `BaselineRun` | réponse du LLM seul, comparée au moteur |

## Tableau publié

| Modèle | Montage correct (LLM seul) | Montage correct (knitproof) | Lecture juste | Champs inventés | Erreurs détectées | Fausses alertes | Stabilité | Coût et temps |
|---|---|---|---|---|---|---|---|---|
| à venir (M2) | | | | | | | | |

## Modifications

Aucune.
