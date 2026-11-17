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

- **Deux jeux séparés** : `dev` pour mettre au point les prompts, `test` réservé à la mesure finale et jamais consulté pendant la mise au point. Un même `id`, ou un même contenu sous un autre `id`, dans les deux jeux est refusé au chargement.
- **Sources** : photos d’étiquettes prises par Isabelle (métadonnées EXIF retirées), demandes rédigées pour l’occasion, patrons écrits pour le projet. Aucun patron du commerce ; les patrons gratuits de Ravelry restent en usage privé.
- **Mémorisation** : les patrons populaires ont pu être appris par les modèles. Les cas du jeu `test` sont écrits pour le projet.
- **Annotation** : chaque entrée du manifeste indique qui a annoté le cas et quand.
- **Manifeste versionné** : un hachage par cas, vérifié en CI. Toute modification d’une valeur attendue est consignée avec son motif. Une valeur attendue n’est jamais modifiée pour faire passer un résultat.
- **Taille** : 5 cas `dev` et 15 cas `test` par évaluation (ligne de base, étiquette, demande) ; résultats en k/N.
- **Pièges de la ligne de base** : 7 cas `test` et 2 cas `dev` portent un piège, attendu tiré du moteur sans règle nouvelle : étiquette et échantillon bloqué (l’échantillon gagne), avant et après blocage (l’après gagne), tour fini donné au lieu de l’écart à la tête, jauge sur 5 cm, mesures en pouces avec une aisance en cm, étiquette seule (le moteur calcule sur l’étiquette). Un cas sans échantillon ni étiquette attend l’abstention. L’aisance s’y dit en mots (« ajusté », « serré ») et en cm, jamais en %.
- **Emplacement** : `src/knitproof/evals/data/<split>/`, un cas par fichier YAML, un `manifest.yaml` par split ; les résultats de mesure vont dans `evals/results/`, un YAML daté par mesure.
- **Cas d’exemple** : l’`id` préfixé `exemple-` marque un cas d’exemple de format, hors des 5 cas `dev` réels ; la ligne de base le mesure avec eux (6 cas, N = 18 sur `dev`).

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
- Température et nombre de passages fixés : 3 passages par cas, à température 0 ; une température non envoyée (Sonnet 5.5) est consignée « non envoyée ».
- Date de chaque passage.
- Au moins un modèle ouvert ou souverain, accessible en direct (modèle local à poids ouverts, Mistral en direct, OpenGateLLM ou API compatible OpenAI) ; un agrégateur ne compte pas.

## Exécution

- **Mesure en direct** : lancée à la main, datée, résultats versionnés.
- **CI** : vérifie le manifeste et rejoue les réponses de modèle enregistrées. Aucun appel payant.

## Modèles de données

| Modèle | Champs clés |
|---|---|
| `EvalManifest` | `version`, `split` (`dev` / `test`), et par entrée : `id` du cas, hachage SHA-256, annotatrice, date |
| `EvalCase` | `id`, `input`, `request` (demande au format de `knitproof calc`), `expected` (tour visé, et montage du moteur ou `abstain`), `injected_error`, `absent_fields` |
| `ModelRun` | modèle, version, prompt, température, mode de sortie structurée, jetons, latence, essais, date (le coût viendra avec le rejeu en CI) |
| `FieldScore`, `EvalResult` | exact, inventé, abstention ; erreur détectée et localisée |
| `BaselineRun` | réponse du LLM seul, comparée au moteur |

## Tableau publié

| Modèle | Montage correct (LLM seul) | Montage correct (knitproof) | Lecture juste | Champs inventés | Erreurs détectées | Fausses alertes | Stabilité | Coût et temps |
|---|---|---|---|---|---|---|---|---|
| à venir (M2) | | | | | | | | |

## Modifications

- 12/11/2026 — Mistral en direct ajouté comme accès souverain (CLA-127, ADR 0033) ; motif : aucune mesure faite.
- 13/11/2026 — Modèle local à poids ouverts (Ollama) retenu comme accès souverain appelé ; Mistral en direct possible, non requis (CLA-62, ADR 0034) ; motif : aucune mesure faite.
- 17/11/2026 — Forme du cas : `EvalCase` porte la demande structurée `request` et le montage attendu `cast_on_stitches`, recalculés par le moteur ; l’exemple est re-haché et re-signé (CLA-188, ADR 0035) ; motif : le verdict se juge sur le tour fini calculé, aucune mesure faite.
- 17/11/2026 — Passages et température : 3 passages par cas, température 0, ou « non envoyée » pour un modèle qui la refuse (CLA-188, ADR 0035) ; motif : aucune mesure faite.
- 17/11/2026 — Le coût est retiré du `ModelRun` jusqu’au rejeu en CI (CLA-188) ; motif : aucune grille de prix ni rejeu n’existent encore, aucune mesure faite.
- 17/11/2026 — Pièges et abstention attendue : 7 cas `test` et 2 cas `dev` de la ligne de base sont des pièges ; un cas sans jauge attend l’abstention, seul passage juste (CLA-188, ADR 0035) ; motif : des cas faciles ne prouvent rien, aucune mesure faite.
- 17/11/2026 — La ligne de base mesure aussi l’exemple sur `dev` (N = 18), décidé par Isabelle (CLA-188) ; motif : un cas de plus ne coûte rien, aucune mesure faite.
- 17/11/2026 — Kimi K3.1 Pro accepte la température 0 par OpenRouter (CLA-199, mesure 2026-11-17T1528) ; motif : la mesure réelle le prouve ; « par fournisseur » (ADR 0035) se lit « par entrée » ; correction factuelle, règle inchangée.
- 17/11/2026 — Le `ModelRun` porte `attempts`, le nombre d’essais HTTP du passage ; la latence est celle du seul essai qui répond ; `None` pour les mesures d’avant (CLA-197, ADR 0036) ; motif : une mesure doit dire qu’elle a traversé des erreurs passagères.
