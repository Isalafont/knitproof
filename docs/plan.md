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
| 0. Outillage | Pydantic, PyYAML (`types-PyYAML` en développement) ; plugin `pydantic.mypy` activé (ADR 0001), avec `[tool.pydantic-mypy]` ; `examples/bonnet-erreur-rang-33.yaml` et `examples/bonnet-3-ans.yaml`, formats provisoires ; deux tests d’acceptation qui lancent la commande `knitproof`, en `xfail(raises=FileNotFoundError, strict=True)` ; `xfail_strict = true` | — |
| 1. Vérifier | `Op`, `Repeat`, `Round`, `Pattern`, `simulate`, `verify` ; format YAML figé, `examples/synthetiques/bonnets/bonnet-synthetique.yaml` ; exemple « erreur au rang 33 » et cas « répétition qui ne tombe pas juste » | aucune question métier |
| 2. Montage, valeurs saisies | CLA-65 : `Length` (cm et pouces), `SwatchMeasurement` (demi-mailles admises), `StitchMultiple`, `stitches_for_width`, `cast_on` à un seul point (multiple et reste), contrôle d’un nombre proposé ; tests de propriétés (multiple respecté, monotonie, aucun `float`). CLA-104 (livré) : `NeedleSize` (système explicite, `mm` saisi), `Needle`, matière, méthode, `check_needles` (`swatch_needle_mismatch`) ; CLA-103 (livré) : `Transition`, `build_transition` (rang d’ajustement réparti selon l’ADR 0019 et vérifié par le moteur), refus typé au-delà d’un rang, ADR 0025 | question 4 |
| 3. Échantillon et résolution (livrée, CLA-66) | `Swatch` avant et après blocage, table de résolution par grandeur, constat « échantillon non bloqué » (96 m contre 88 m), constat `gauge_differs_from_label` (échantillon comparé à la jauge de l’étiquette), questions en attente | questions 2, 3, 7, 9, 14 |
| 4. Bibliothèque | Chargeur YAML typé par registre (CLA-67), `StitchPattern`, `ReferenceMeasurement`, table de correspondance des aiguilles ; chaque valeur sourcée et validée ; bibliothèque versionnée | questions 1, 10, 11 |
| 5. Hauteur et calotte (livrée, CLA-68) | `SwatchMeasurement` avec jauge en rangs, `rounds_for_height` et `knitted_rows` (arrondi tracé), `crown_plan` en rond et à plat, `needle_change` dans la calotte, `beanie_plan` (bord, corps, calotte, `verify`), `plan_beanie` (hauteur saisie ou Knit Picks, questions en attente), exemple 3 ans ; bonnet à plat avec lisières, ADR 0028 | questions 5, 6, 12 |
| 6. Rendu et CLI (livrée, CLA-69) | `Report` unique (ADR 0029), `calc_beanie`, `knitproof calc` et `knitproof verify`, fichiers de sortie de référence, test qui empêche le README de dériver | — |

**Critère de fin**

- [x] `uv run knitproof verify examples/bonnet-erreur-rang-33.yaml` sort en code 1 avec un constat `count_mismatch` au rang 33 (attendu 90, annoncé 89).
- [x] `uv run knitproof calc examples/bonnet-3-ans.yaml` (aisance et hauteur saisies) donne la sortie de référence : 88 m, alerte à 96 m, rejet de 120 m, plan complet du bonnet.
- [x] `uv run pytest`, `uv run ruff check .`, `uv run lint-imports` et `uv run mypy` passent.

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
| 1 | ~~L’aisance dépend-elle d’abord de l’ajustement voulu et du point, la fibre ne faisant que la moduler ? En % ou en cm ? Quelles sources ?~~ **Tranché le 05/11/2026 par Isabelle** (tranché en partie le 26/10/2026 : l’aisance dépend du point, de la fibre, des aiguilles et de l’ajustement voulu) : unité en % pour les valeurs de référence, en % ou cm pour une saisie ; chiffre issu d’une table par couple (ajustement, point), la fibre ne donnant que des avertissements ; bonnet ajusté en jersey −15,6 % (Oslo), ample en côtes 2/2 −17,7 % (Rosebud), ajusté en côtes 2/2 sans source. Voir [ADR 0024](adr/0024-aisance-du-bonnet.md). (cadrage : CLA-77) | — |
| 2 | ~~Bord en côtes : échantillon en côtes obligatoire, ou même montage que le corps avec un avertissement ?~~ **Tranché le 27/10/2026 par Isabelle** : échantillon en côtes facultatif ; s’il est donné, il sert au bord (rang d’ajustement possible) ; sinon le bord prend le montage du corps, marqué « À VÉRIFIER : les côtes resserrent le bord ». | — |
| 3 | ~~Échantillon tricoté à plat, bonnet tricoté en rond : un écart à prendre en compte ?~~ **Tranché le 27/10/2026 par Isabelle** : échantillon à plat pour un ouvrage en rond : avertissement « À VÉRIFIER », sans correction du calcul. | — |
| 4 | ~~Arrondi du montage : au plus proche, en dessous ou au-dessus ? Rang d’ajustement entre bord et corps accepté ?~~ **Tranché le 27/10/2026 par Isabelle** : montage arrondi au multiple le plus proche, en dessous en cas d’égalité ; rang d’ajustement entre bord et corps accepté, calculé et vérifié par le moteur. | — |
| 5 | ~~Calotte : nombre de secteurs, rythme des diminutions, profondeur ; comment la mesurer ?~~ **Tranché le 02/11/2026 par Isabelle** : 8 diminutions par rang, sauf le dernier rang, soit 4 secteurs à 2 diminutions ; un rang sur deux, les 3 dernières à chaque rang ; dernier rang en `k2tog` partout sous 24 m, fermeture déclarée ; profondeur calculée, rangs de la calotte × 10 / rangs pour 10 cm, jauge après blocage (décision d’Isabelle, modifiable, sans source ; Oslo en comparaison) ([ADR 0019](adr/0019-calotte-du-bonnet.md)). | — |
| 6 | ~~Hauteur par âge et bord replié : quelles sources ?~~ **Tranché le 02/11/2026 par Isabelle** : hauteur finie, du bord porté au sommet, calotte incluse, revers replié. La saisie prime ; sinon table Knit Picks par âge, avec source et « À VÉRIFIER », lue comme hauteur finie par hypothèse ; un âge à deux valeurs donne la plage et une question, sans milieu. Bord replié : tricoté = finie + revers, revers saisi, sinon question en attente. Bord doublé traité à part ([ADR 0020](adr/0020-hauteur-finie-et-bord-replie.md)). | — |
| 7 | ~~Échantillon non bloqué sur une fibre à forte détente : refuser, ou estimer et marquer « À VÉRIFIER » ?~~ **Tranché le 27/10/2026 par Isabelle** : jauge après blocage estimée seulement avec un coefficient de détente sourcé, cité avec sa source ; résultat toujours « À VÉRIFIER », avec le rappel qu’un échantillon doit être bloqué (lavé) avant d’être mesuré ; sans coefficient sourcé, calcul sur l’échantillon non bloqué, « À VÉRIFIER ». Quand un échantillon est mesuré avant et après blocage, le moteur en déduit la détente réelle du fil, qui prime sur la bibliothèque. **Précisé le 12/11/2026 par Isabelle** : la fibre ne porte aucun coefficient, la détente vient de l’échantillon de la laine ([ADR 0030](adr/0030-laines-de-reference.md)). | — |
| 8 | ~~Mélanges de fibres : pondérer selon la composition, ou retenir la fibre dominante ?~~ **Tranché le 26/10/2026 par Isabelle** : pondérer selon la composition ([ADR 0010](adr/0010-melanges-de-fibres.md)) ; **précisé le 12/11/2026 par Isabelle** : la fibre n’est plus qu’un vocabulaire, une laine porte sa composition et ses échantillons, sans moyenne de profils ([ADR 0030](adr/0030-laines-de-reference.md)). | — |
| 9 | ~~Jauge de l’étiquette : toujours « À VÉRIFIER », faute de savoir si l’échantillon du fabricant est bloqué ?~~ **Tranché le 27/10/2026 par Isabelle** : sans échantillon, la jauge de l’étiquette est utilisée, marquée « À VÉRIFIER : jauge du fabricant, état de blocage inconnu », avec le conseil de faire puis bloquer un échantillon ; un échantillon de la personne prime toujours, l’étiquette ne sert alors qu’à la comparaison. | — |
| 10 | ~~Plage plausible d’un tour de tête par âge, et conduite à tenir quand les tableaux divergent (41–46 cm contre 48 cm à 3 ans)~~ **Tranché le 02/11/2026 par Isabelle** : plage OMS P3–P97 tous sexes de 0 à 5 ans, au mois ; valeur proposée au milieu des deux médianes, « À VÉRIFIER », retenue seulement après une `Decision` ; la question en attente propose d’abord de mesurer la tête, et la valeur « À VÉRIFIER » reste le choix à défaut ; l’OMS fait foi, une seule source par âge ; au-delà, tour de tête demandé ; une mesure hors plage donne un signal à vérifier, pas un refus ([ADR 0018](adr/0018-tour-de-tete-par-age.md)). Complété le 05/11/2026 par Isabelle : grille de tailles nommées jusqu’à l’adulte ([ADR 0026](adr/0026-grille-de-tailles-du-tour-de-tete.md)). Complété le 09/11/2026 par Isabelle : le tour de tête par âge vient des patrons et, dès 15 ans, du Craft Yarn Council, en plage sans valeur proposée ([ADR 0027](adr/0027-tour-de-tete-par-age-d-apres-les-patrons.md)). | — |
| 11 | ~~Quelle table de correspondance des tailles d’aiguilles (mm, US, UK, japonaises) fait référence ?~~ **Tranché le 02/11/2026 par Isabelle** ([ADR 0021](adr/0021-table-de-reference-des-tailles-d-aiguilles.md)). | — |
| 12 | ~~Aiguilles circulaires : quelle longueur de câble pour quelle circonférence, et à partir de quand passer aux aiguilles double pointe ou au magic loop dans la calotte ?~~ **Tranché le 05/11/2026 par Isabelle** ([ADR 0023](adr/0023-longueur-des-aiguilles-circulaires-et-magic-loop.md)). | — |
| 13 | ~~Aiguilles du projet différentes de celles de l’échantillon : un changement de matière seul mérite-t-il un avertissement ?~~ **Tranché le 25/10/2026 par Isabelle** : oui, la matière joue sur la tension et sur la glisse du fil. Un changement de taille **ou** de matière déclenche l’avertissement. | — |
| 14 | ~~Échantillon de la personne comparé à la jauge de l’étiquette : à partir de quel écart avertir (en mailles, en %, selon la fibre) ? Faut-il alors suggérer une taille d’aiguilles au-dessus ou en dessous ?~~ **Tranché le 27/10/2026 par Isabelle** : avertissement à partir de 5 % d’écart entre l’échantillon et l’étiquette (décision d’Isabelle, modifiable) ; seulement le sens de correction (trop de mailles : aiguilles plus grosses ; pas assez : plus fines), jamais de taille précise. | — |

## Risques

- **Périmètre** : rien d’autre que le bonnet avant la fin de M1 ; M2 limité à l’étiquette, à la demande et à Ravelry.
- **Exactitude métier** : aucune valeur de bibliothèque sans source ni validation.
- **Questions bloquantes** : la tranche « vérifier » avance sans elles.
- **Fuite d’évaluation** : le jeu `test` ne sert jamais à mettre au point les prompts.
- **Droits et données** : pas de patron du commerce dans le dépôt ; photos sans EXIF ; patrons Ravelry en usage privé ; patrons réels (Oslo Hue, DROPS) transcrits seulement dans `local-patterns/`, ignoré par git, pour des essais privés, vérifiables à la demande par `KNITPROOF_PATTERNS` (README, « Vérifier un patron YAML ») : la CI n’en dépend pas, et un échec dû à une opération hors périmètre ne prouve pas une erreur de calcul.
- **Sur-modélisation** : chaque modèle naît d’un test qui échoue.
