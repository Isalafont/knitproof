# ADR 0026 — Grille de tailles du tour de tête, de la naissance à l’adulte

Amende l’ADR 0018 sur trois points : §6 (au-delà de 60 mois), l’alternative écartée « Enveloppe sur l’année d’âge », réservée ici aux tailles nommées, et l’alternative écartée « Champ de sexe ». Le reste de l’ADR 0018 ne change pas.

## Contexte

L’ADR 0018 donne une plage de tour de tête par âge, de 0 à 60 mois, d’après l’OMS. Au-delà, le tour de tête est demandé, sans plage (§6). Une personne qui tricote pour un grand enfant ou un adulte sans mesure n’a donc aucun repère. L’ADR 0018 a ouvert ce cadrage. Il cherchait une source publiée, par âge, avec méthode, effectif et percentiles (CLA-113).

Le 05/11/2026, Isabelle a recentré le besoin sur une grille de tailles nommées, comme dans les patrons : « 0-3 mois / 6 mois / 9 mois / 12 mois / 18 mois / 24 mois / -> 2/3 ans 4 ans », puis « 5-7 ans / 7-9 ans / 10-12 ans », « à partir de 14-16 ans on commence à presque avoir des tailles adultes », et « selon femme et hommes au moins quelques tailles comme S M L ».

L’OMS n’a pas de table de tour de tête après 5 ans : sa référence 5–19 ans couvre l’IMC, la taille et le poids (ADR 0018). Les courbes françaises de 2018 (AFPA, CRESS-Inserm) s’arrêtent aussi à 5 ans pour le tour de tête (communiqué AFPA du 5 mars 2018, <https://afpa.org/content/uploads/2018/03/2018_03_05_CP_Courbescroissance.pdf>, lu le 05/11/2026 : « courbes de périmètre crânien 0 et 5 ans »).

## Décision

Décidé par Isabelle le 05/11/2026 (CLA-113).

1. **Ce que décrit une taille.** Une tête, pas un bonnet. Une taille nommée a une plage de tour de tête et une valeur proposée. L’aisance reste à l’ADR 0024.
2. **Prématurés.** Hors périmètre : la grille commence à 0–3 mois, et l’âge corrigé n’est pas traité.
3. **De 0 à 4 ans : l’OMS.** Les mêmes tables que l’ADR 0018 (P3, P50, P97, filles et garçons, au mois).
4. **De 5–7 ans à 17 ans : KiGGS.** Neuhauser et al., *Reference percentiles for anthropometric measures and blood pressure based on KiGGS 2003–2006*, Robert Koch-Institut, 2016, doi 10.17886/RKI-GBE-2016-032, tables p. 80 (garçons) et 81 (filles), « Head circumference percentiles (in cm) for boys / girls aged 0 months to 18 years ».
   - Enquête allemande représentative de 2003 à 2006, complétée par des données périnatales de 1995 à 2000.
   - Mesure du tour occipito-frontal maximal, au mètre ruban non élastique, au 0,1 cm près.
   - Effectif : 8 601 garçons et 8 351 filles, de 0,25 à 17 ans (tableau 2).
   - Méthode LMS, P3 à P97 par sexe.
   - La table est à la demi-année après 2 ans : la ligne « 7.0 years » couvre de 6,75 à moins de 7,25 ans. L’ADR 0018 §8 fait saisir l’âge en années entières après 2 ans, et chaque année se lit sur sa ligne « N.0 years ».
5. **Une seule source par âge.** L’OMS fait foi jusqu’à 60 mois, KiGGS de 6 à 18 ans. La ligne « 5.0 years » de KiGGS n’est pas chargée. Une taille qui chevauche les deux sources (5–7 ans) lit chaque borne dans la source de son âge.
6. **Plage d’une taille.**
   - Taille à un âge (6 mois, 4 ans…) : plage du plus petit P3 au plus grand P97 des deux sexes, comme l’ADR 0018 §2.
   - Taille sur une tranche (0–3 mois, 2–3 ans, 5–7 ans…) : plage du plus petit P3 à la borne basse jusqu’au plus grand P97 à la borne haute.
   - C’est une enveloppe sur la tranche, que l’ADR 0018 §8 écarte pour l’entrée par âge. Ici, elle ne vaut que pour une taille nommée : l’entrée par âge exact reste celle de l’ADR 0018.
7. **Valeur proposée.**
   - Taille à un âge : milieu des deux médianes, comme l’ADR 0018 §3.
   - Taille sur une tranche : moyenne des quatre médianes (filles et garçons, aux deux bornes).
   - En `Decimal`, sans arrondi, toujours « À VÉRIFIER » et retenue seulement après une `Decision` (ADR 0018 §4).
8. **Adultes : femme et homme, S, M, L.** Source : la ligne « 18.0 years » de KiGGS, par sexe. Découpage :
   - S de P3 à P25, M de P25 à P75, L de P75 à P97 ;
   - valeurs proposées : P10, P50 et P90 ;
   - toutes ces valeurs sont publiées par la table, sans interpolation.
9. **Sexe.** Il n’entre que pour les adultes, là où la grille sépare femme et homme. Sans sexe saisi, les deux séries de tailles sont affichées, sans valeur proposée tant qu’une taille n’est pas choisie. Avant l’âge adulte, la plage reste tous sexes, comme dans l’ADR 0018.
10. **Âge ou taille hors de la grille.** Jusqu’à 60 mois, l’entrée par âge de l’ADR 0018 s’applique à tout âge. Après 60 mois, la grille n’a plus de trou en années entières : de 5 à 17 ans, chaque âge tombe dans au moins une taille (5–7, 7–9, 10–12, 12–14, 14–16 ans, 17 ans), et 18 ans ouvre les tailles adultes. Un âge sur une borne partagée (7, 12 ou 14 ans) propose la plus petite taille et montre la plus grande.
11. **Mesure saisie.** Elle prime toujours. Hors plage, elle donne un `warning`, jamais un refus (ADR 0018 §7).

### Grille

En cm. P3 et P97 sur les deux sexes, sauf pour les adultes.

| Taille | Âges lus | Source | Plage | Valeur proposée |
|---|---|---|---|---|
| 0–3 mois | 0 et 3 mois | OMS | 31,7–42,7 | 37,1 |
| 6 mois | 6 mois | OMS | 39,7–45,6 | 42,75 |
| 9 mois | 9 mois | OMS | 41,3–47,4 | 44,4 |
| 12 mois | 12 mois | OMS | 42,3–48,5 | 45,5 |
| 18 mois | 18 mois | OMS | 43,6–49,9 | 46,8 |
| 24 mois | 24 mois | OMS | 44,6–50,8 | 47,75 |
| 2–3 ans | 24 et 36 mois | OMS | 44,6–52,1 | 48,375 |
| 4 ans | 48 mois | OMS | 46,7–53,0 | 49,75 |
| 5–7 ans | 60 mois (OMS), 7 ans (KiGGS) | OMS et KiGGS | 47,2–55,30 | 51,1925 |
| 7–9 ans | 7 et 9 ans | KiGGS | 48,99–56,17 | 52,4675 |
| 10–12 ans | 10 et 12 ans | KiGGS | 50,12–57,24 | 53,69 |
| 12–14 ans | 12 et 14 ans | KiGGS | 51,07–58,39 | 54,5975 |
| 14–16 ans | 14 et 16 ans | KiGGS | 51,86–59,39 | 55,37 |
| 17 ans | 17 ans | KiGGS | 52,10–59,70 | 55,83 |
| Femme S | 18 ans | KiGGS | 52,19–54,01 | 53,09 |
| Femme M | 18 ans | KiGGS | 54,01–56,12 | 55,06 |
| Femme L | 18 ans | KiGGS | 56,12–58,08 | 57,10 |
| Homme S | 18 ans | KiGGS | 53,62–55,74 | 54,68 |
| Homme M | 18 ans | KiGGS | 55,74–57,98 | 56,87 |
| Homme L | 18 ans | KiGGS | 57,98–59,89 | 58,95 |

Valeurs lues, en cm (P3 / P50 / P97) :

| Âge | Filles | Garçons | Source |
|---|---|---|---|
| 0 mois | 31,7 / 33,9 / 36,1 | 32,1 / 34,5 / 36,9 | OMS |
| 3 mois | 37,2 / 39,5 / 41,9 | 38,3 / 40,5 / 42,7 | OMS |
| 6 mois | 39,7 / 42,2 / 44,6 | 41,0 / 43,3 / 45,6 | OMS |
| 9 mois | 41,3 / 43,8 / 46,3 | 42,6 / 45,0 / 47,4 | OMS |
| 12 mois | 42,3 / 44,9 / 47,5 | 43,6 / 46,1 / 48,5 | OMS |
| 18 mois | 43,6 / 46,2 / 48,8 | 44,9 / 47,4 / 49,9 | OMS |
| 24 mois | 44,6 / 47,2 / 49,8 | 45,7 / 48,3 / 50,8 | OMS |
| 36 mois | 45,9 / 48,5 / 51,2 | 46,8 / 49,5 / 52,1 | OMS |
| 48 mois | 46,7 / 49,3 / 52,0 | 47,5 / 50,2 / 53,0 | OMS |
| 60 mois | 47,2 / 49,9 / 52,6 | 47,9 / 50,7 / 53,5 | OMS |
| 7 ans | 48,99 / 51,65 / 54,49 | 49,73 / 52,52 / 55,30 | KiGGS |
| 9 ans | 49,66 / 52,36 / 55,24 | 50,47 / 53,34 / 56,17 | KiGGS |
| 10 ans | 50,12 / 52,85 / 55,76 | 50,77 / 53,68 / 56,53 | KiGGS |
| 12 ans | 51,07 / 53,87 / 56,83 | 51,38 / 54,36 / 57,24 | KiGGS |
| 14 ans | 51,86 / 54,71 / 57,71 | 52,35 / 55,45 / 58,39 | KiGGS |
| 16 ans | 52,07 / 54,93 / 57,94 | 53,19 / 56,39 / 59,39 | KiGGS |
| 17 ans | 52,10 / 54,97 / 57,98 | 53,45 / 56,69 / 59,70 | KiGGS |

Ligne 18 ans de KiGGS (P3 / P10 / P25 / P50 / P75 / P90 / P97) :
- filles : 52,19 / 53,09 / 54,01 / 55,06 / 56,12 / 57,10 / 58,08 ;
- garçons : 53,62 / 54,68 / 55,74 / 56,87 / 57,98 / 58,95 / 59,89.

Sources :
- OMS, Child Growth Standards, <https://www.who.int/tools/child-growth-standards/standards/head-circumference-for-age>, tables `tab_hcfa_girls_p_0_5.xlsx` et `tab_hcfa_boys_p_0_5.xlsx`, relues le 05/11/2026. Les valeurs de 12 à 60 mois sont celles de l’ADR 0018.
- KiGGS, <https://edoc.rki.de/handle/176904/3271>, PDF relu le 05/11/2026.

L’échantillon de KiGGS s’arrête à 17 ans : la ligne 18,0 ans (de 17,75 à 18,25 ans) est donc en partie extrapolée par le modèle. Sa vérification dans Schienkiewitz A. et al., « German head circumference references for infants, children and adolescents in comparison with currently used national and international references », *Acta Paediatr* 2011, 100(7):e28–33, est une condition du ticket de suite qui charge la grille. De 17,5 à 18 ans, la médiane ne gagne que 0,05 cm (filles) et 0,09 cm (garçons).

## Recoupement, sans effet sur la grille

**ANSUR II** (armée américaine, 2010–2012) : 1 986 femmes et 4 082 hommes de 17 à 58 ans, CSV publics, colonne `headcircumference` en mm. Source : <https://www.openlab.psu.edu/ansur2/>, lue le 05/11/2026. Centiles calculés sur les CSV, bruts et non pondérés, non confrontés au rapport NATICK/TR-15/007 : aucune de ces valeurs n’entre dans la grille.

| | P3 | P25 | P50 | P75 | P97 |
|---|---|---|---|---|---|
| Femmes | 52,8 | 54,8 | 56,0 | 57,3 | 60,2 |
| Hommes | 54,5 | 56,3 | 57,4 | 58,5 | 60,5 |

En cm. Les médianes dépassent celles de KiGGS à 18 ans de 0,9 cm (femmes) et 0,5 cm (hommes), et les P97 de 2,1 cm et 0,6 cm. Population militaire, non représentative, avec des adultes plus âgés : ce n’est pas la source.

**Oslo (PetiteKnit)**, en repère seulement. Tours de tête de ses sept tailles, cités par l’ADR 0024 : 47–48, 49–50, 51–52, 53–54, 55–56, 57–59, 60–63 cm. Le patron ne donne aucun âge et n’a pas de taille homme. Ses tailles femme sont plus grandes que la grille : sa plus grande taille (60–63) dépasse le P97 féminin de KiGGS (58,08) et d’ANSUR (60,2). Aucune valeur d’Oslo n’entre dans la grille.

## Alternatives écartées

- **Rester sans plage au-delà de 60 mois** (ADR 0018 §6) : une source européenne publiée, avec tables, effectif et méthode, existe.
- **Rollins et al. 2010** (*J Pediatr* 156(6):907–913, doi 10.1016/j.jpeds.2010.01.009) : aucune table trouvée, résumé seul.
- **Nellhaus 1968** (*Pediatrics* 41:106–114) : données compilées depuis 1948, moyenne ± 2 écarts-types, article non lu.
- **UK90** (Cole, Freeman et Preece 1998) : paramètres LMS seuls (paquet R `sitar`, <https://search.r-project.org/CRAN/refmans/sitar/html/uk90.html>), licence non indiquée, données de 1978 à 1990.
- **ANSUR II comme source adulte** : population militaire américaine. Gardé en recoupement.
- **DINED, SizeGERMANY, campagne IFTH 2006** :
  - DINED : tour de tête non confirmé, sous licence CC BY-NC 4.0, <https://data.4tu.nl/datasets/39fce1d9-72e3-4811-a66c-918fccf782f5> ;
  - SizeGERMANY : données réservées aux partenaires industriels ;
  - IFTH 2006 : aucune table publique trouvée.
- **Grille Oslo comme source** : un patron n’est pas une donnée anthropométrique publiée, et il ne donne ni âge ni taille homme.
- **Fenton 2013 pour les prématurés** (<https://pmc.ncbi.nlm.nih.gov/articles/3637477>) : hors périmètre, et ses paramètres LMS ne s’obtiennent que sur demande.
- **Sexe dès 6 ans** : l’écart des médianes reste sous 1 cm jusqu’à 12 ans (KiGGS : 0,49 cm à 12 ans), et la grille d’Isabelle ne sépare les sexes qu’à l’âge adulte.
- **Tiers égaux de la plage P3–P97 pour S, M, L** : des bornes calculées, alors que les percentiles P25 et P75 sont publiés.

## Conséquences

- L’ADR 0018 reçoit en tête la mention « Amendé par l’ADR 0026 (§6, champ de sexe) ». Le reste de son texte ne change pas.
- `docs/architecture.md` (l. 241), `docs/plan.md` (question 10) et le README (l. 56) sont alignés dans la PR du cadrage.
- Une valeur de la grille a la provenance `reference_measurement` et cite sa table, son âge et son sexe s’il y a lieu. La valeur retenue après la `Decision` porte `person_decision`.
- Droits :
  - OMS : CC BY-NC-SA 3.0 IGO (<https://www.who.int/about/policies/publishing/copyright>), fichier à part, comme l’ADR 0018 ;
  - KiGGS : aucune licence indiquée (« Keine Lizenzangabe » sur la page edoc du RKI) ;
  - ANSUR II : aucune licence indiquée sur la page de l’Open Lab.
  La décision vaut sous condition : chaque table n’entre dans la bibliothèque qu’une fois sa licence lue et compatible.
- Tickets de suite proposés :
  - Charger la grille dans la bibliothèque (sur le modèle de CLA-67), après lecture des licences de KiGGS et d’ANSUR II, et vérification de la ligne 18 ans dans Schienkiewitz 2011.
  - Ajouter à la spécification du bonnet un champ `size` (taille nommée) et un champ `sex` facultatif, réservé aux tailles adultes.
