# Architecture de knitproof

> **Le modèle propose, le moteur prouve, la personne arbitre.**

Ce document décrit comment knitproof est construit : qui décide quoi, par où passent les données, comment le code est découpé et pourquoi. Le plan de réalisation est dans [`plan.md`](plan.md), le protocole d’évaluation dans [`evaluation.md`](evaluation.md).

## Sommaire

1. [Vue d’ensemble](#1-vue-densemble)
2. [Qui décide quoi](#2-qui-décide-quoi)
3. [Parcours « vérifier un patron »](#3-parcours--vérifier-un-patron-)
4. [Parcours « calculer un bonnet »](#4-parcours--calculer-un-bonnet-)
5. [Couches](#5-couches)
6. [Modèles de données](#6-modèles-de-données)
7. [Provenance et résolution des sources](#7-provenance-et-résolution-des-sources)
8. [Nombres et arrondis](#8-nombres-et-arrondis)
9. [Représentation d’un patron](#9-représentation-dun-patron)
10. [Sécurité et données](#10-sécurité-et-données)
11. [Limites assumées](#11-limites-assumées)
12. [Décisions à documenter](#12-décisions-à-documenter)
13. [Projets proches](#13-projets-proches)

## 1. Vue d’ensemble

```mermaid
flowchart LR
    PDF["Demande<br/>ou patron existant"]:::data
    EXT["MODÈLE<br/>comprend la demande<br/>ou lit le patron"]:::model
    SPEC[("Structure typée<br/>+ provenance de<br/>chaque valeur")]:::data
    SWA[("Vos échantillons<br/>avant et après blocage<br/>+ étiquettes des fils")]:::data
    FIB[("Bibliothèque de fibres<br/>et mesures de référence")]:::data
    LIB[("Bibliothèque<br/>de points")]:::data
    CALC["MOTEUR<br/>calcule les mailles<br/>de chaque rang"]:::engine
    VAL["MOTEUR<br/>vérifie les invariants"]:::engine
    DEC{"Résultat"}:::engine
    OK["Patron<br/>calculé ou vérifié"]:::data
    ERR["Rapport<br/>erreur prouvée et localisée"]:::data
    HUM["PERSONNE<br/>arbitre l’ambiguïté"]:::human

    PDF --> EXT --> SPEC --> CALC --> VAL --> DEC
    SWA --> CALC
    FIB --> CALC
    LIB --> VAL
    DEC -- "cohérent" --> OK
    DEC -- "incohérent" --> ERR
    DEC -- "incertain" --> HUM --> OK

    classDef model fill:#EDE7F6,stroke:#5E35B1,stroke-width:2px,color:#1A1A1A
    classDef engine fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1A1A1A
    classDef human fill:#FFF3E0,stroke:#E65100,stroke-width:2px,color:#1A1A1A
    classDef data fill:#F5F5F5,stroke:#616161,color:#1A1A1A
```

Trois acteurs, trois responsabilités qui ne se recouvrent pas :

- le **modèle** (violet) transforme du texte ou une image en structure typée ; il ne produit jamais un nombre de mailles ni un verdict ;
- le **moteur** (vert) est du Python pur, sans IA : il résout les sources, calcule, simule et vérifie ;
- la **personne** (orange) tranche ce qu’aucun calcul ne peut prouver, et sa décision est enregistrée.

## 2. Qui décide quoi

| Étape | Modèle | Moteur | Personne |
|---|---|---|---|
| Comprendre une demande, lire une étiquette (M2) | propose une structure | valide le schéma, pose la provenance | corrige si besoin |
| Résoudre les paramètres (échantillon, tour de tête, aisance, hauteur) | — | applique la table de résolution | répond aux questions en attente |
| Calculer montage, hauteur, calotte | — | calcule | — |
| Vérifier un patron | — | simule rang par rang, compare | — |
| Contrôler un nombre proposé par un LLM | — | accepte ou rejette, avec le calcul | — |
| Trancher une ambiguïté | — | signale `needs_review` | décide ; la `Decision` est tracée |
| Juger tombé, confort, esthétique | — | — | tricot-test |

## 3. Parcours « vérifier un patron »

En M1, le patron est saisi en YAML ; la lecture d’un patron par un modèle vient après M3.

```mermaid
sequenceDiagram
    actor P as Personne
    participant CLI as cli
    participant APP as app
    participant ENG as engine
    P->>CLI: knitproof verify patron.yaml
    CLI->>APP: verify_pattern(chemin)
    APP->>APP: lit le fichier, valide le patron (Pydantic)
    APP->>ENG: verify(pattern)
    ENG->>ENG: simule chaque rang : mailles consommées et produites
    ENG-->>APP: constats (count_mismatch, repeat_not_fitting…)
    APP-->>CLI: constats
    CLI-->>P: rapport localisé, code 1 si constat, 3 si fichier invalide
```

## 4. Parcours « calculer un bonnet »

```mermaid
sequenceDiagram
    actor P as Personne
    participant LLM as llm (M2)
    participant APP as app
    participant LIB as library
    participant ENG as engine
    P->>APP: demande (YAML en M1, texte libre en M2)
    opt Texte libre ou photo d’étiquette (M2)
        APP->>LLM: extraction structurée
        LLM-->>APP: objet d’extraction + extraits sources
        APP->>APP: conversion vers le domaine, provenance model_inference
    end
    APP->>LIB: fibres, points, mesures de référence
    APP->>ENG: resolve_beanie_inputs(spec, échantillons, fil, bibliothèque)
    ENG-->>APP: paramètres résolus + questions en attente
    alt Une question bloque le calcul
        APP-->>P: question (ex. « échantillon non bloqué sur un superwash »)
        P->>APP: Decision
    end
    APP->>ENG: plan_beanie(paramètres)
    ENG-->>APP: montage, rangs, calotte, constats
    APP-->>P: rapport
```

## 5. Couches

```mermaid
flowchart BT
    domain["domain<br/>modèles Pydantic"]
    engine["engine<br/>calculs purs"]
    library["library<br/>YAML sourcés"]
    llm["llm<br/>extraction (M2)"]
    sources["sources<br/>Ravelry (M2)"]
    app["app<br/>cas d’usage"]
    cli["cli"]
    api["api (M3)"]
    web["web (M3)"]
    evals["evals (M2)"]

    engine --> domain
    library --> domain
    llm --> domain
    sources --> domain
    app --> engine & library & llm & sources
    cli --> app
    api --> app
    web --> app
    evals --> app & llm
```

Une flèche signifie « dépend de ».

| Couche | Rôle | Règles |
|---|---|---|
| `domain` | Modèles de données et invariants | Aucune dépendance interne |
| `engine` | Résolution, calculs, simulation, vérification | Python pur ; aucune lecture de fichier, aucun réseau, aucun appel à un modèle |
| `library` | Chargement des bibliothèques YAML sourcées | Toute valeur a une source |
| `llm` | Objets d’extraction, appels aux modèles, conversion vers `domain` | Jamais importé par `engine` |
| `sources` | Données externes (API Ravelry) | Optionnel : knitproof fonctionne sans |
| `app` | Cas d’usage : `verify_pattern`, `plan_beanie` | Seul point d’entrée pour `cli`, `api` et `web` |
| `cli`, `api`, `web` | Portes d’entrée | Aucune logique métier ; rendu uniquement |
| `evals` | Jeux d’évaluation et mesures | Voir [`evaluation.md`](evaluation.md) |

Les dépendances entre couches sont vérifiées par import-linter (CLA-57) ; les contrats sont dans `[tool.importlinter]` de `pyproject.toml`. `cli`, `api`, `web` et `evals` peuvent importer `domain` pour typer ce qu’ils affichent ; ils n’atteignent `engine`, `library`, `llm` et `sources` qu’en passant par `app` (et `llm` pour `evals`). L’API JSON et l’interface web sont deux portes vers le même cœur : l’interface React s’ajoute sans toucher au moteur ([ADR 0006](adr/0006-portes-http-fastapi-et-react-aria.md)).

## 6. Modèles de données

Modèles Pydantic dans `domain/`. Chacun naît d’un test qui échoue : la liste ci-dessous est une cible, pas un préalable.

### Provenance

| Modèle | Champs clés | Invariants |
|---|---|---|
| `SourceKind` | `user_swatch`, `user_measurement`, `user_input`, `yarn_label`, `ravelry`, `fiber_library`, `reference_measurement`, `model_inference`, `person_decision`, `engine` | pas d’ordre global (voir section 7) |
| `SourceLocation` | `page`, `line` (tranche 1) ; à venir : `document`, `round` | au moins un champ renseigné |
| `Provenance` | `kind`, `reference`, `location`, `extracted_by` (modèle, version, prompt), `note` | `reference` obligatoire pour `fiber_library`, `reference_measurement`, `yarn_label`, `ravelry` |
| `Sourced[T]` | `value`, `provenance` | réservé aux paramètres résolus et aux constats |

### Mesures, fil, fibres

| Modèle | Champs clés | Invariants |
|---|---|---|
| `Range` | `min`, `max` | `min ≤ max` |
| `ReferenceMeasurement` | `quantity` (tour, hauteur), `age_or_size`, `range_cm`, `source` | source obligatoire ; divergence entre sources signalée |
| `FiberComposition` | parts (`fiber_id`, `percent`) | somme = 100 ; fibres connues |
| `YarnLabel` | composition, `needle: Range[NeedleSize]`, `gauge` (fourchette, unité d’origine, état inconnu), `length_m`, `weight_g`, `care`, `superwash` | provenance au niveau de l’objet |
| `Yarn` | `id`, `name`, `brand`, `composition`, `superwash`, `label` | — |
| `FiberProfile` | `fiber_id`, `names`, `blocking_change` (largeur, hauteur), `ease_modifier`, `sources`, `validated_by` | au moins une source ; non validé ⇒ `needs_review` |

### Échantillon et points

| Modèle | Champs clés | Invariants |
|---|---|---|
| `Length` | `value: Decimal`, `unit` (`cm` / `in`) | `value` > 0, au plus 5 chiffres en écriture décimale (zéros finaux retirés), `float` refusé en entrée ; conversion exacte : 1 in = 2,54 cm |
| `NeedleSize` | `original` (ex. « US 6 », « 4 mm », taille UK ou japonaise), `system` (`mm`, `us`, `uk`, `jp`), `mm: Decimal` | `mm` calculé par la table de correspondance sourcée ; correspondance ambiguë ⇒ `needs_review` |
| `Needle` | `size: NeedleSize`, `kind` (`straight`, `circular`, `double_pointed`), `cable_length: Length` (aiguilles circulaires), `material` (optionnel : métal, bois, bambou…) | `cable_length` obligatoire pour `circular`, absent sinon ; la matière n’entre dans aucun calcul |
| `SwatchMeasurement` | `stitches: Decimal`, `width: Length` ; à venir, CLA-68 : `rows`, `height` | valeurs > 0, `float` refusé en entrée ; demi-mailles admises (ex. 22,5 m pour 10 cm, 22 m pour 4 in) ; jauge pour 10 cm dérivée |
| `Swatch` | `id`, `yarn_id`, `needle: Needle`, `stitch_pattern_id`, `worked` (`round` / `flat`), `before`, `after`, `blocking_method` | aiguilles et point identiques avant et après, par construction |
| `StitchMultiple` | `repeat_multiple`, `repeat_offset` | `multiple ≥ 1`, `0 ≤ offset < multiple` ; `accepts(n)` ; le point saisi pour le montage (CLA-65), sans `id` ni `names` |
| `StitchPattern` | `id`, `names`, `repeat_multiple`, `repeat_offset` | `0 ≤ offset < multiple` ; le couple de `StitchMultiple` (CLA-65) y sera rattaché par CLA-67 |

### Spécification, patron, résultats

| Modèle | Champs clés | Invariants |
|---|---|---|
| `BeanieSpecification` | `head_cm`, `age_years`, `yarn_id`, `body_swatch_id`, `brim_swatch_id`, `ease`, `brim_pattern_id`, `body_pattern_id`, `brim_height_cm`, `folded_brim`, `total_height_cm`, `crown_sectors`, `worked` (`round` en V0), `needles: list[Needle]` | `head_cm` > 0 ; hauteur du bord < hauteur totale ; les aiguilles permettent la méthode (`round` ⇒ circulaires ou double pointe) |
| `Ease` | `value`, `unit` (% ou cm) | — |
| `ResolvedBeanieInputs` | tête, jauge, aisance, hauteurs, chacun `Sourced` | seule entrée du calcul |
| `Op` | `work(n)`, `k2tog`, `m1` (tranche 1) ; à venir : `ssk`, `k3tog`, `sk2p`, `finish` ; `consumes` et `produces` dérivés | `n ≥ 1`, `consumes ≥ 0`, `produces ≥ 1` |
| `Repeat` | `body`, `times` (entier ; `to_end` à venir) | `body` non vide, `times ≥ 1` |
| `Round` | `start`, `end`, `ops`, `stated_count`, `location` (`section` à venir) | `start ≤ end` ; le moteur vérifie que les opérations consomment les mailles du rang précédent (section 9) |
| `Pattern` | `cast_on`, `rounds` (`provenance` à venir) | rangs contigus et croissants depuis le rang 1 |
| `CastOnResult` | `target: Length`, `raw_stitches`, `stitches`, `rounding_rule`, `finished_cm` ; `adjustment_round` à venir, CLA-103 | `stitches` respecte le multiple et le reste du point (`StitchMultiple`) ; le plus proche du nombre brut, en dessous en cas d’égalité ; rang d’ajustement entre multiples différents : CLA-103 |
| `CastOnCheck` | `proposed`, `expected`, `reasons` (`stitch_multiple_not_respected`, `differs_from_calculation`), `proposed_finished_cm` ; `accepted` dérivé | `proposed` ≥ 1 ; « point non respecté » implique toujours « diffère du calcul » ; pas de tolérance (cadrage CLA-105) |
| `CrownPlan` | `sectors`, `rounds`, `depth_cm` | fin à 0 maille ou fermeture déclarée |
| `BeaniePlan` | `cast_on`, `brim_rounds`, `body_rounds`, `crown`, `finished_circumference_cm`, `finished_height_cm` | hauteurs calculées avec la jauge en rangs après blocage |
| `Finding` | `status` (`error` en tranche 1 ; `warning`, `ok`, `needs_review` à venir), `code`, `round`, `expected`, `actual`, `location` ; à venir : `message`, `decided_by`, `provenance` | `error` ⇒ moteur ; `needs_review` ⇒ une question en attente |
| `PendingQuestion`, `Decision` | question, options ; choix, date, motif | toute décision répond à une question |
| `Report` | `findings`, `inputs`, `decisions`, `result`, `engine_version`, `library_version` | déterministe : même entrée, même rapport |

Les modèles d’évaluation (`EvalManifest`, `EvalCase`, `ModelRun`, `FieldScore`, `BaselineRun`) sont décrits dans [`evaluation.md`](evaluation.md).

**Repoussés** : profil de la personne au-delà de l’âge, autres vêtements, élasticité et mémoire des fibres (non consommées par le calcul), quantité de fil, persistance des échantillons (fichiers YAML en M1), tricot à plat, lecture de patrons PDF.

## 7. Provenance et résolution des sources

Trois règles :

1. La provenance est portée par l’objet d’entrée : un `Swatch` vient par nature de l’utilisatrice, un `YarnLabel` de l’étiquette.
2. Quand un modèle a lu la source, la provenance garde la trace de la lecture (`extracted_by`). Elle est posée par le code de l’adaptateur, **jamais déclarée par le modèle**.
3. Une valeur manquante devient une `PendingQuestion`. Elle n’est jamais estimée en silence.

L’ordre de confiance dépend de la grandeur :

| Grandeur | Ordre de confiance | Si rien n’est disponible |
|---|---|---|
| Échantillon | échantillon bloqué > échantillon non bloqué (règle à trancher) > étiquette ou fiche Ravelry (`needs_review`) | question en attente |
| Tour de tête | mesure > mesure de référence par âge (`needs_review` si les sources divergent) | question en attente |
| Aisance | saisie > bibliothèque de fibres validée | question en attente |
| Hauteur | saisie > mesure de référence par âge | question en attente |

Une étiquette et une fiche Ravelry qui divergent produisent un constat `needs_review`.

Quand l’échantillon de la personne et la jauge de l’étiquette coexistent, le calcul suit toujours l’échantillon : la jauge de l’étiquette est celle de la marque, pas celle de la personne. Le moteur compare tout de même les deux et produit un constat `gauge_differs_from_label`. Sous un seuil à trancher, ce constat est `ok` et note seulement l’écart, normal selon la tension de chacune. Au-dessus, il devient `warning` : erreur de mesure, échantillon non bloqué ou autres aiguilles sont possibles. Si l’échantillon a été tricoté avec les aiguilles de l’étiquette, le constat suggère d’en changer la taille pour retrouver la jauge visée. Le moteur ne fait que suggérer : c’est la personne qui décide.

La provenance permet aussi d’effacer sur demande toutes les données venues d’une source, comme l’exige la licence de l’API Ravelry.

## 8. Nombres et arrondis

- Les comptes du patron (mailles sur l’aiguille, numéros de rangs) sont des entiers : on monte 88 mailles, pas 88,5. Ce sont des entiers stricts : seul un entier YAML nu est accepté ; un `bool` (`true`), une chaîne (`"10"`) ou un nombre à virgule (`10.0`) est refusé, jamais converti (CLA-108).
- Les mesures sont des `Decimal`, y compris les mailles et rangs comptés sur un échantillon, où les demi-mailles sont courantes (22,5 m pour 10 cm). Aucun `float` dans `engine`.
- Chaque longueur garde son unité d’origine. Un échantillon « 22 m pour 4 in » se mesure sur 10,16 cm, pas 10 cm : confondre les deux décale le montage d’environ 1,6 %.
- Les tailles d’aiguilles gardent leur notation d’origine (mm, US, UK, japonaise) ; la valeur en mm vient d’une table de correspondance sourcée dans la bibliothèque. Une correspondance ambiguë devient un constat `needs_review`.
- L’outil et la méthode sont distincts : des circulaires servent à plat comme en rond, des aiguilles droites seulement à plat. La méthode (`worked`) se renseigne sur l’échantillon et sur le projet ; le moteur vérifie que les aiguilles la permettent.
- La matière des aiguilles (métal, bois, bambou…) joue sur la tension et sur la glisse du fil, mais n’entre dans aucun calcul : aucun coefficient inventé. Si les aiguilles du projet diffèrent de celles de l’échantillon, en taille ou en matière, le moteur produit un avertissement `swatch_needle_mismatch` qui invite à refaire l’échantillon.
- Le type d’aiguilles compte pour le tricot en rond : un câble de circulaire trop long pour la circonférence du tricot ne permet pas de tricoter. Le moteur signale le rang de la calotte à partir duquel il faut passer aux aiguilles double pointe ou au magic loop (constat `needle_change`), selon une règle à valider.
- Un seul arrondi métier : celui du montage, avec une règle paramétrée et tracée dans le résultat.
- Les quotients (nombre brut de mailles, largeur finie, jauge pour 10 cm) sont des `Decimal` à 28 chiffres significatifs, `ROUND_HALF_EVEN`, calculés par `DIVISION.divide` et non par `/` ; ils ne servent qu’à la trace, le montage se décidant exactement par produits croisés ([ADR 0015](adr/0015-quotients-decimaux-et-montage-exact.md)).
- La mise en forme française (« 43,2 cm ») relève du rendu, pas du domaine.

## 9. Représentation d’un patron

Chaque opération déclare les mailles qu’elle consomme et produit : `k2tog` consomme 2 mailles et en produit 1. Une répétition indique son nombre de passages (`to_end` viendra plus tard). Un rang peut couvrir une plage (« côtes 2/2 sur 20 rangs ») et porte sa localisation dans le document source.

Invariant central, vérifié par le moteur et non par Pydantic (les comptes dépendent du contexte d’exécution) : les opérations d’un rang consomment exactement les mailles produites par le rang précédent. Sinon, le moteur produit un constat `repeat_not_fitting` au rang fautif et arrête la simulation. Un compte annoncé qui diffère de la simulation produit un constat `count_mismatch` ; la simulation continue alors sur le compte calculé, pas sur l’annoncé (ADR 0013). Un compte annoncé situé après l’arrêt n’est pas comparé.

Une plage de rangs répète les mêmes opérations à chaque rang ; le compte annoncé porte sur le dernier rang de la plage. Une plage dont les opérations changent le nombre de mailles échoue donc dès son deuxième rang.

Format YAML (figé par CLA-64), chargé par `yaml.safe_load` puis `Pattern.model_validate` ; `k2tog` et `m1` s’écrivent nus. Les exemples vivent dans [`examples/`](../examples/) ; les patrons synthétiques justes, dans `examples/synthetiques/`, que la CI parcourt récursivement. Pour vérifier un fichier, voir la section « Vérifier un patron YAML » du README.

Les comptes (`cast_on`, `work`, `times`, `start`, `end`, `stated_count`) sont des entiers nus ; une chaîne, un nombre à virgule ou un booléen rend le patron invalide (code 3).

```yaml
cast_on: 108
rounds:
  - {start: 1, end: 30, ops: [{work: 108}]}
  - start: 31
    ops: [{repeat: {body: [{work: 10}, k2tog], times: 9}}]
    stated_count: 99
  - {start: 32, ops: [{work: 99}]}
  - start: 33
    ops: [{repeat: {body: [{work: 9}, k2tog], times: 9}}]
    stated_count: 89
    location: {page: 2, line: 14}
```

Opérations prises en charge. `k2tog`, `m1` et `p2tog` suivent la [liste standard du Craft Yarn Council](https://www.craftyarncouncil.com/standards/knitting-abbreviations) (lue le 27/10/2026 : « knit 2 stitches together; single right-leaning decrease », « make one stitch knitwise; single knit increase », « purl 2 stitches together; single decrease ») ; `work n` est propre à knitproof :

| Opération | Anglais | En français | Consomme | Produit |
|---|---|---|---|---|
| `work n` | work n stitches | tricoter n mailles comme elles se présentent | n | n |
| `k2tog` | knit 2 together | 2 mailles ensemble à l’endroit | 2 | 1 |
| `m1` | make 1 | 1 augmentation intercalaire | 0 | 1 |

À venir, sans comptes pour l’instant : `p2tog` (purl 2 together, 2 mailles ensemble à l’envers), `ssk`, `k3tog`, `sk2p`…

En V0, le bonnet se tricote en rond : `Round` suffit. Le texte en français dit « rang », comme les patrons ; le code garde `Round`.

## 10. Sécurité et données

- Le modèle ne produit que des structures validées par Pydantic. Un texte injecté dans un patron ou une demande ne peut pas changer un compte : le calcul ne dépend que du moteur.
- Les mesures d’un enfant sont enregistrées sans nom.
- Les photos d’étiquettes sont débarrassées de leurs métadonnées EXIF (localisation).
- Stockage local en V0.
- Aucun patron du commerce dans le dépôt ; les patrons gratuits ne sont pas libres de droits.
- Les identifiants d’API (Ravelry, modèles) restent dans un `.env` local, jamais dans le dépôt.

## 11. Limites assumées

Aucun calcul ne remplace un tricot-test : le tombé, le confort, la tenue et l’esthétique restent à juger par une personne. knitproof garantit la cohérence des nombres, pas la réussite du vêtement.

## 12. Décisions d’architecture

Les décisions structurantes font l’objet d’un ADR dans [adr/](adr/) :

- [ADR 0001 — Vérifier les types avec mypy strict](adr/0001-verifier-les-types-avec-mypy-strict.md)
- [ADR 0002 — Python et uv](adr/0002-python-et-uv.md)
- [ADR 0003 — Format intermédiaire typé avant tout calcul](adr/0003-format-intermediaire-type.md)
- [ADR 0004 — Moteur de calcul déterministe sans LLM](adr/0004-moteur-deterministe-sans-llm.md)
- [ADR 0005 — Accès aux modèles via pydanticAI](adr/0005-acces-aux-modeles-via-pydanticai.md)
- [ADR 0006 — Portes HTTP : FastAPI, React et React Aria Components](adr/0006-portes-http-fastapi-et-react-aria.md)
- [ADR 0007 — Decimal et arrondi unique](adr/0007-decimal-et-arrondis.md)
- [ADR 0008 — Provenance et résolution par grandeur](adr/0008-provenance-et-resolution.md)
- [ADR 0009 — Découpage en couches](adr/0009-decoupage-en-couches.md)
- [ADR 0010 — Mélanges de fibres](adr/0010-melanges-de-fibres.md)
- [ADR 0011 — Licence de l’API Ravelry](adr/0011-licence-api-ravelry.md)
- [ADR 0012 — Interdire `Any` avec mypy](adr/0012-interdire-any-avec-mypy.md)
- [ADR 0013 — Format YAML figé et poursuite sur le compte calculé](adr/0013-format-yaml-fige-et-poursuite-sur-le-compte-calcule.md)
- [ADR 0014 — « Rang » plutôt que « tour » dans les textes](adr/0014-rang-plutot-que-tour-dans-les-textes.md)
- [ADR 0015 — Quotients décimaux à précision fixe, montage décidé exactement](adr/0015-quotients-decimaux-et-montage-exact.md)

## 13. Projets proches

- [StitchCheck](https://github.com/KingHaim/stitchcheck) vérifie les mailles rang par rang, avec un mode LLM optionnel.
- [knitcheck](https://github.com/jarhodes314/knitcheck) traite le patron comme un programme typé, en Rust.

knitproof part de l’échantillon réel et du comportement des fibres, trace la provenance de chaque valeur, mesure sa fiabilité par modèle et renvoie l’incertain à une personne.
