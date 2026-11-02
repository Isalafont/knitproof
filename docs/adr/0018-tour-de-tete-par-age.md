# ADR 0018 — Tour de tête par âge

## Contexte

Une personne n’a pas toujours de mesure : tête absente, cadeau. Le moteur a besoin d’une valeur unique, et les tableaux du tricot divergent. Le « 41 à 46 cm contre 48 cm à 3 ans » du cadrage vient surtout d’une lecture : la page du Craft Yarn Council ne donne aucun âge, et celle de Knit Picks place 3 ans dans deux lignes (voir « Comparaison »).

## Décision

Décidé par Isabelle le 02/11/2026 (CLA-80, question tricot 10).

1. **Ce que décrit la plage.** Une tête, pas un bonnet. L’aisance reste à CLA-77.
2. **Source.** Standards de croissance de l’OMS, tables « Head circumference-for-age, Birth to 5 years (percentiles) », garçons et filles. La plage va du plus petit P3 au plus grand P97 des deux tables, au mois.
3. **Valeur proposée.** Le milieu des deux médianes : (P50 filles + P50 garçons) / 2, en `Decimal`, sans arrondi. Elle est toujours marquée « À VÉRIFIER », avec sa provenance.
4. **Sans mesure, âge couvert.** Une question en attente affiche la plage et propose la valeur (`needs_review`). Elle propose d’abord de mesurer la tête, et la valeur « À VÉRIFIER » reste le choix à défaut. Le calcul ne part qu’après la `Decision`.
5. **Divergence.** Hiérarchie fixe : l’OMS fait foi et une seule source est chargée par âge. Les divergences sont documentées ici, sans calcul à l’exécution.
6. **Au-delà de 60 mois.** Aucune autre source ne prend la place de l’OMS par défaut, et aucune plage n’est inventée : le tour de tête est demandé, par une question en attente.
7. **Mesure saisie.** Elle prime toujours. Hors plage, elle donne un signal à vérifier (`warning`), jamais un refus.
8. **Grain d’âge.** La table se charge au mois. L’âge se saisit en mois avant 2 ans, en années entières ensuite. Un âge en années vaut le mois exact : 3 ans = 36 mois, sans enveloppe sur l’année.

| Âge | Plage retenue | Valeur proposée |
|---|---|---|
| 12 mois | 42,3–48,5 | 45,5 |
| 24 mois | 44,6–50,8 | 47,75 |
| 36 mois | 45,9–52,1 | 49,0 |
| 48 mois | 46,7–53,0 | 49,75 |
| 60 mois | 47,2–53,5 | 50,3 |

Détail à 36 mois :

| Sexe | P3 | P50 | P97 |
|---|---|---|---|
| Filles | 45,9 | 48,5 | 51,2 |
| Garçons | 46,8 | 49,5 | 52,1 |

En cm. Exemples de lecture ; la table complète, de 0 à 60 mois, entrera dans la bibliothèque avec CLA-67. Source : OMS, Child Growth Standards, <https://www.who.int/tools/child-growth-standards/standards/head-circumference-for-age>, tables `tab_hcfa_boys_p_0_5.xlsx` et `tab_hcfa_girls_p_0_5.xlsx`, lues le 02/11/2026. Publications de l’OMS sous CC BY-NC-SA 3.0 IGO (<https://www.who.int/about/policies/publishing/copyright>) ; licence propre à ces fichiers non lue.

Au-delà de 5 ans, l’OMS n’a pas de table de tour de tête : sa référence 5–19 ans (<https://www.who.int/tools/growth-reference-data-for-5to19-years>) couvre l’IMC, la taille et le poids.

## Comparaison, sans effet sur la plage

| Source | Ce qu’elle donne | Lecture |
|---|---|---|
| [Craft Yarn Council](https://craftyarncouncil.com/node/39) | « Toddler » 16–18 in / 40,5–46 cm, « Child » 18–20 in / 45,5–51 cm, sans âge ni méthode | Lu comme 3 ans, « Toddler » tombe presque entièrement sous la plage OMS (0,1 cm commun) |
| [Knit Picks](https://tutorials.knitpicks.com/hat-size-charts/) (17 décembre 2009) | « 12 mois à 3 ans » 19 in, « 3 à 10 ans » 20 in, en pouces seulement (conversion : environ 48 et 51 cm) ; origine non indiquée | 3 ans figure dans deux lignes, toutes deux dans la plage OMS |

Pages relues par Isabelle le 02/11/2026. Le lien Knit Picks que citait le README (<https://www.knitpicks.com/learning-center/hat-size-chart>) répond 403 : page non lue.

## Recoupement par des patrons publiés

Six tailles de quatre patrons, pour recouper seulement : aucun ne modifie la plage, et aucun tour de tête n’est tiré d’un patron dont l’aisance est inconnue. Un patron n’est comparé à la plage que si sa mesure de tête et l’âge sont confirmés par une relecture, sinon « non comparé ». Les tableaux des patrons ne sont pas repris. Valeurs lues via des résumés, non relues.

| Patron | Taille | Ce qu’il mesure | Valeur | OMS au même âge | Lecture |
|---|---|---|---|---|---|
| DROPS Children 41-27 | 2 ans | non dit par la source lue | 48/50 cm | 44,6–50,8 | non comparé |
| DROPS Children 41-27 | 3/5 ans | non dit par la source lue | 50/52 cm | 45,9–52,1 (36 mois) ; 47,2–53,5 (60 mois) | non comparé |
| [PetiteKnit, Oslo](https://www.petiteknit.com/en/products/oslo-hue) | bébé | « head circumference » ; aisance non dite par la source lue | 47–48 cm (édition plus ancienne : 47–50 cm) | non comparé : aucun âge lu | sert de repère seulement |
| [DROPS 0-906](https://www.ravelry.com/patterns/library/0-906-childs-hat) | 3/5 ans | « To fit head measure: 48/50 » (page Ravelry) | 48/50 cm | 45,9–52,1 (36 mois) ; 47,2–53,5 (60 mois) | non comparé ; différent du 41-27 pour la même taille |
| [Easy Knit Baby Pixie Bonnet](https://www.ravelry.com/patterns/library/easy-knit-baby-pixie-bonnet) | 6–12 mois | « head circumference » (page Ravelry) ; aisance non dite | 44–47 cm | 42,3–48,5 (à 12 mois) | non comparé |
| [Easy Knit Baby Pixie Bonnet](https://www.ravelry.com/patterns/library/easy-knit-baby-pixie-bonnet) | 1–2 ans | « head circumference » (page Ravelry) ; aisance non dite | 48–50 cm | 44,6–50,8 (à 24 mois) | non comparé |

Seul patron trouvé qui annonce une mesure de tête avant 2 ans : le Pixie Bonnet ; l’extrait ci-dessus ne donne, pour les âges de ce patron, que 12 et 24 mois, d’où deux tailles seulement. Aucun second patron n’a été ajouté dans la timebox.

DROPS Children 41-27 : valeurs d’un résumé de recherche citant la page garnstudio id=10598 ; `garnstudio.com` répond 403, page non lue.

## Alternatives écartées

- Mesure obligatoire : contredit l’ordre de confiance du §7 et prive d’un calcul la personne qui n’a pas la tête sous la main.
- Valeur appliquée d’office, avec un constat : c’est une estimation sans arbitrage.
- Enveloppe de toutes les sources : 40,5–52,1 cm à 3 ans ne contrôle plus rien.
- Tableaux tricot seuls : sans âge chez le Craft Yarn Council, sans méthode ni origine publiées.
- Plusieurs sources par âge et `needs_review` calculé selon un seuil : exige une correspondance âge ↔ catégorie inventée.
- Pas de valeur dès que les sources divergent : plus aucune valeur à 3 ans.
- Champ de sexe dans la spécification : le profil au-delà de l’âge est repoussé, et l’écart entre médianes ne dépasse pas 1,2 cm.
- Enveloppe sur l’année d’âge : élargirait la plage sans source, alors que la table est au mois.
- Tableaux tricot au-delà de 5 ans : ils prendraient la place de l’OMS par défaut.

## Conséquences

- Mesure demandée d’abord : la question en attente propose d’abord de mesurer la tête, et la valeur « À VÉRIFIER » reste le choix à défaut.
- Une valeur issue de cette table a la provenance `reference_measurement` et cite la table et le mois. La valeur retenue après la `Decision` porte `person_decision`.
- L’architecture (§6, §7) est alignée dans le même cadrage.
- Suite retenue : la ligne « Une source de référence » du ticket (table sourcée dans CLA-67), avec la valeur « À VÉRIFIER » de la ligne « Plage qui englobe les sources » ; l’OMS n’englobe pas les sources. Les tickets :
  - CLA-67 charge la table au mois, après avoir lu la licence des xlsx ; modification de son CA3 proposée à Isabelle.
  - Le champ `age` se définit dans un nouveau ticket, qui créera `BeanieSpecification` avec `age`, `head_cm` facultatif, sans `crown_sectors` (CLA-78) et le sens de `brim_height_cm` (CLA-79).
  - Un nouveau cadrage cherche une source pour les grands enfants et les adultes : publiée, par âge, avec méthode, effectif et percentiles. Pistes, une ligne par source, à lire en premier pour les enfants :
    - CDC/Rollins 2010 (J Pediatr, naissance à 21 ans ; titre vu seulement).
    - Nellhaus 1968 (Pediatrics 41(1):106–114, naissance à 18 ans, études depuis 1948).
    - ANSUR II, pour les adultes (armée américaine ; <https://ph.health.mil/topics/workplacehealth/ergo/Pages/Anthropometric-Database.aspx>, non ouverte).

    Pistes non lues en entier, aucune n’est retenue ici.
- CLA-97 et CLA-102 citent ce tour de tête de référence dans leur propre texte.
- Droits : la licence de l’OMS (non commerciale, partage à l’identique) n’est pas celle du dépôt (MIT). La table OMS se charge dans un fichier à part, sous la licence OMS, avec citation et l’avertissement d’adaptation demandé par l’OMS ; cet avertissement couvre le milieu des médianes. La licence des xlsx est lue au début de CLA-67.
