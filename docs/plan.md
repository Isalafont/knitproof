# Plan de réalisation

Ce plan découpe knitproof en jalons, puis en tranches verticales : chaque tranche part d’un test d’acceptation et livre un comportement utilisable. L’architecture est décrite dans [`architecture.md`](architecture.md).

## M0 — Cadrage

- Architecture, plan et protocole d’évaluation (ce document et ses voisins).
- Décisions d’architecture (ADR).
- Conventions Python et d’architecture, vérifiées automatiquement.
- Flow de branches : `main` (production), `develop` (sandbox), branches de travail depuis `develop`, une pull request à chaque étape.
- Intégration continue : tests, ruff, typage (mypy strict) et contrats de couches sur chaque pull request ; `main` et `develop` protégées. Le déploiement continu (`develop` vers la sandbox, `main` vers la production) arrive en M3, avec l’image Docker.

## M1 — Moteur, sans IA

| Tranche | Contenu | Dépend de |
|---|---|---|
| 0. Outillage | Pydantic, PyYAML ; plugin mypy Pydantic (`plugins = ["pydantic.mypy"]`) ; deux tests d’acceptation (exemples du README) en `xfail(strict=True)` | — |
| 1. Vérifier | `Op`, `Repeat`, `Round`, `Pattern`, `simulate`, `verify` ; exemple « erreur au rang 33 » et cas « répétition qui ne tombe pas juste » | aucune question métier |
| 2. Montage, valeurs saisies | `Length` (cm et pouces), `NeedleSize`, `Needle` (droites, circulaires avec longueur de câble, double pointe ; matière optionnelle), méthode à plat ou en rond distincte de l’outil, avertissement `swatch_needle_mismatch`, `SwatchMeasurement` (demi-mailles admises), `stitches_for_width`, `cast_on` avec multiples combinés, contrôle d’un nombre proposé ; tests de propriétés (multiple respecté, monotonie, aucun `float`) | question 4 |
| 3. Échantillon et résolution | `Swatch` avant et après blocage, table de résolution par grandeur, constat « échantillon non bloqué » (96 m contre 88 m), constat `gauge_differs_from_label` (échantillon comparé à la jauge de l’étiquette), questions en attente | questions 2, 3, 7, 9, 14 |
| 4. Bibliothèque | Chargeur YAML, `FiberProfile`, `StitchPattern`, `ReferenceMeasurement`, table de correspondance des aiguilles ; chaque valeur sourcée et validée ; bibliothèque versionnée | questions 1, 8, 10 |
| 5. Hauteur et calotte | `rounds_for_height`, `crown_plan`, `BeaniePlan`, changement d’aiguilles dans la calotte (`needle_change`) | questions 5, 6, 12 |
| 6. Rendu et CLI | `knitproof calc` et `knitproof verify`, fichiers de sortie de référence, test qui empêche le README de dériver | — |

**Critère de fin**

- `uv run knitproof verify examples/bonnet-erreur-rang-33.yaml` sort en code 1 avec un constat `count_mismatch` au tour 33 (attendu 90, annoncé 89).
- `uv run knitproof calc examples/bonnet-3-ans.yaml` (aisance saisie) donne la sortie de référence : 88 m, alerte à 96 m, rejet de 120 m, plan complet du bonnet.
- `uv run pytest`, `uv run ruff check .`, `uv run lint-imports` et `uv run mypy` passent.

## M2 — Lecture et évaluation

1. Protocole d’évaluation ([`evaluation.md`](evaluation.md)) figé avant tout prompt.
2. Adaptateur `llm` sur pydanticAI ([ADR 0005](adr/0005-acces-aux-modeles-via-pydanticai.md)), dont au moins un modèle ouvert ou souverain.
3. Ligne de base « LLM seul » sur les demandes de bonnet.
4. Étiquette en photo → `YarnLabel` (photos personnelles, sans EXIF).
5. Demande en texte → `BeanieSpecification`.
6. Source Ravelry : recherche d’un fil, fiche pré-remplie, divergence avec l’étiquette signalée.
7. Plusieurs modèles, plusieurs passages ; désaccord ⇒ « À VÉRIFIER », avec mesure de ce que ce signal attrape.
8. Cas d’injection de prompt.

**Critère de fin** : `uv run knitproof eval --split test --models a,b,c` produit le tableau du README ; la CI vérifie le manifeste et rejoue les réponses enregistrées.

## M3 — Démo

1. API JSON (FastAPI, OpenAPI) au-dessus de `app`.
2. Interface accessible en React et React Aria Components ([ADR 0006](adr/0006-portes-http-fastapi-et-react-aria.md)).
3. Docker ; déploiement continu de `develop` sur la sandbox et de `main` en production ; la CI ajoute le manifeste et le rejeu de l’évaluation, sans appel payant.
4. Audit RGAA publié ; axe-core en CI.

**Critère de fin** : URL publique ; `docker run` démarre l’API ; CI verte ; audit RGAA sans non-conformité bloquante sur le parcours de calcul.

## Après M3

Lecture de patrons texte et PDF libres de droits, bibliothèque de points complète et RAG, reconnaissance des points par photo, génération de patrons et constructions multiples, raglan, gradation multi-tailles.

## Questions d’expertise tricot

Ces questions ne sont pas tranchées par le code : chacune bloque une tranche jusqu’à sa réponse.

| # | Question | Bloque |
|---|---|---|
| 1 | L’aisance dépend-elle d’abord de l’ajustement voulu et du point, la fibre ne faisant que la moduler ? En % ou en cm ? Quelles sources ? | tranche 4 |
| 2 | Bord en côtes : échantillon en côtes obligatoire, ou même montage que le corps avec un avertissement ? | tranche 3 |
| 3 | Échantillon tricoté à plat, bonnet tricoté en rond : un écart à prendre en compte ? | tranche 3 |
| 4 | Arrondi du montage : au plus proche, en dessous ou au-dessus ? Tour d’ajustement entre bord et corps accepté ? | tranche 2 |
| 5 | Calotte : nombre de secteurs, rythme des diminutions, profondeur ; comment la mesurer ? | tranche 5 |
| 6 | Hauteur par âge et bord replié : quelles sources ? | tranche 5 |
| 7 | Échantillon non bloqué sur une fibre à forte détente : refuser, ou estimer et marquer « À VÉRIFIER » ? | tranche 3 |
| 8 | Mélanges de fibres : pondérer selon la composition, ou retenir la fibre dominante ? | tranche 4 |
| 9 | Jauge de l’étiquette : toujours « À VÉRIFIER », faute de savoir si l’échantillon du fabricant est bloqué ? | tranche 3 |
| 10 | Plage plausible d’un tour de tête par âge, et conduite à tenir quand les tableaux divergent (41–46 cm contre 48 cm à 3 ans) | tranche 4 |
| 11 | Quelle table de correspondance des tailles d’aiguilles (mm, US, UK, japonaises) fait référence ? | tranche 4 |
| 12 | Aiguilles circulaires : quelle longueur de câble pour quelle circonférence, et à partir de quand passer aux aiguilles double pointe ou au magic loop dans la calotte ? | tranche 5 |
| 13 | ~~Aiguilles du projet différentes de celles de l’échantillon : un changement de matière seul mérite-t-il un avertissement ?~~ **Tranché le 25/10/2026 par Isabelle** : oui, la matière joue sur la tension et sur la glisse du fil. Un changement de taille **ou** de matière déclenche l’avertissement. | — |
| 14 | Échantillon de la personne comparé à la jauge de l’étiquette : à partir de quel écart avertir (en mailles, en %, selon la fibre) ? Faut-il alors suggérer une taille d’aiguilles au-dessus ou en dessous ? | tranche 3 |

## Risques

- **Périmètre** : rien d’autre que le bonnet avant la fin de M1 ; M2 limité à l’étiquette, à la demande et à Ravelry.
- **Exactitude métier** : aucune valeur de bibliothèque sans source ni validation.
- **Questions bloquantes** : la tranche « vérifier » avance sans elles.
- **Fuite d’évaluation** : le jeu `test` ne sert jamais à mettre au point les prompts.
- **Droits et données** : pas de patron du commerce dans le dépôt ; photos sans EXIF ; patrons Ravelry en usage privé.
- **Sur-modélisation** : chaque modèle naît d’un test qui échoue.
