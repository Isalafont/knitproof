# ADR 0021 — Table de référence des tailles d’aiguilles

Complète l’[ADR 0016](0016-tailles-d-aiguilles-sans-conversion.md), qui reste inchangée.

## Contexte

La question tricot 11 demande quelle table de correspondance des tailles d’aiguilles fait référence, et CLA-81 y ajoute la liste des tailles valides par système. Aucune table lue ne couvre les quatre systèmes avec une source solide : le Craft Yarn Council ne donne que mm et US. Une taille US peut aussi valoir plusieurs mm : le Council fait correspondre 4 et 4,25 mm à US 6, et dit de se fier aux mm de l’emballage.

## Décision

Décision d’Isabelle du 02/11/2026.

1. **Référence.** Une source par système, le mm comme pivot. Chaque ligne porte sa source et sa valeur en mm. Les tables restent séparées : deux tailles seulement voisines ne sont jamais présentées comme égales.
2. **Divergences.** Elles sont listées ci-dessous et marquées « À VÉRIFIER ».
3. **Usage.** La table alimente la liste des tailles valides et un texte d’information. Le moteur ne convertit rien : le mm reste saisi et `sizes_not_comparable` ne change pas. Un mm saisi prime ; une conversion reste une hypothèse avec sa provenance.
4. **Texte d’information.** Il donne toutes les valeurs de la source, sans choisir : « US 6 : 4 ou 4,25 mm selon le CYC, À VÉRIFIER sur l’emballage ».
5. **Taille absente de la liste.** Elle sera acceptée avec un `warning` « taille inconnue de la table », notation conservée. US 37 et JP 42 seront donc acceptées, avec ce `warning`.
6. **Liste par système.** Les listes US, UK et JP sont les tables ci-dessous. Le système `mm` n’a pas de liste : un mm est une mesure, tout décimal positif de forme valide (au plus 5 chiffres) vaut, sans `warning`.
7. **Forme.** En US et UK, elle s’ouvre aux décimales à point et aux fractions comme 10¾ et 2.5, et reste fermée : un texte qui n’est pas une taille est refusé, et le système n’est jamais deviné. La virgule reste refusée en US et UK, et acceptée en mm. En JP, 号 entiers seulement ; la table s’arrête à 15 ; une notation JP plus grande reste acceptée avec le `warning`, le mm reste préférable. Les fractions admises sont ½ et ¾ (10.75 chez KnitPro).
8. **Comparaison.** « 2.5 » et « 2½ » sont égaux pour la comparaison seulement, à l’intérieur du système US. La notation d’origine reste conservée telle quelle. « 00 » et « 000 » restent distincts de « 0 ».

### Table US

Source : [Craft Yarn Council](https://craftyarncouncil.com/standards/hooks-and-needles), lue le 02/11/2026.

| US | mm |
|---|---|
| 000 | 1,5 (À VÉRIFIER) |
| 00 | 1,75 (À VÉRIFIER) |
| 0 | 2 |
| 1 | 2,25 |
| 2 | 2,75 |
| 3 | 3,125 ou 3,25 (À VÉRIFIER) |
| 4 | 3,5 |
| 5 | 3,75 |
| 6 | 4 ou 4,25 (À VÉRIFIER) |
| 7 | 4,5 |
| 8 | 5 |
| 9 | 5,25 ou 5,5 (À VÉRIFIER) |
| 10 | 5,75 ou 6 (À VÉRIFIER) |
| 10½ | 6,5 |
| 11 | 8 |
| 13 | 9 |
| 15 | 10 |
| 17 | 12,5 ou 12,75 (À VÉRIFIER) |
| 19 | 15 (À VÉRIFIER) |
| 35 | 19 |
| 50 | 25 |
| 70 | 35 (À VÉRIFIER) |

### Table UK

Source : [Sheep and Stitch, mis à jour le 31/08/2021](https://sheepandstitch.com/library/knitting-needle-sizes-conversion-chart/), lue le 02/11/2026. C’est un site de tricot, pas un fabricant ni une norme.

| UK | mm |
|---|---|
| 14 | 2 |
| 13 | 2,25 |
| 12 | 2,75 |
| 11 | 3 |
| 10 | 3,25 |
| 9 | 3,75 |
| 8 | 4 |
| 7 | 4,5 |
| 6 | 5 |
| 5 | 5,5 |
| 4 | 6 |
| 3 | 6,5 |
| 2 | 7 |
| 1 | 7,5 |
| 0 | 8 |
| 00 | 9 (À VÉRIFIER) |
| 000 | 10 (À VÉRIFIER) |

### Table JP

Source : [fiches « 匠 » 2本針 de Clover](https://clover.co.jp/products/54200/), de `54200` (0号) à `54215` (15号), diamètre de l’aiguille, « 針軸の太さ(直径) », lues le 02/11/2026. Un seul fabricant, aucune norme lue : toute la table est marquée « À VÉRIFIER ». Une notice ou un emballage de fabricant remplacera ces valeurs dès qu’on en aura un.

| 号 | mm |
|---|---|
| 0 | 2,1 |
| 1 | 2,4 |
| 2 | 2,7 |
| 3 | 3 |
| 4 | 3,3 |
| 5 | 3,6 |
| 6 | 3,9 |
| 7 | 4,2 |
| 8 | 4,5 |
| 9 | 4,8 |
| 10 | 5,1 |
| 11 | 5,4 |
| 12 | 5,7 |
| 13 | 6 |
| 14 | 6,3 |
| 15 | 6,6 |

Sources secondaires concordantes, annoncées comme telles : [Sheep and Stitch](https://sheepandstitch.com/library/knitting-needle-sizes-conversion-chart/) ; [komarilab.jp](https://komarilab.jp/guides/knitting-needle-sizes/), sans ligne 14号.

### Divergences relevées (À VÉRIFIER)

| Taille | Table retenue | Autres sources |
|---|---|---|
| UK 00 et 000, 9 et 10 mm | 00 et 000 | [KnitPro](https://www.knitpro.eu/en/blog/knitting-needle-sizes-and-conversion-guide-us-uk-chart) : UK 0 pour 8, 9 et 10 mm ; [A Yarn Story](https://ayarnstory.co.uk/pages/knitting-needle-conversion-chart) : 00 et 000 |
| UK 15 et 17 | absentes | A Yarn Story : 1,75 et 1,5 mm |
| 3 mm | sans taille US | KnitPro, Sheep and Stitch : US 2,5 ; A Yarn Story : 2½, « not an official US size » |
| 2,5 mm | sans ligne | Sheep and Stitch : US 1,5 ; A Yarn Story : 1½, même note |
| 7 mm | sans taille US | KnitPro : US 10,75 |
| US 17 | 12,5 ou 12,75 mm | KnitPro : 12 ; Sheep and Stitch : 12 à 12,75 |
| US 19 | 15 mm | KnitPro : 16 ; Sheep and Stitch : 15 à 16 |
| US 36 | absente | Sheep and Stitch : 20 mm |
| US 000 et 00 | 1,5 et 1,75 mm | [comomonote.com](https://comomonote.com/knitting-needles-size/) : 1,25 et 1,5 mm |
| US 3, 6, 9 et 10 | 3,125 ou 3,25 ; 4 ou 4,25 ; 5,25 ou 5,5 ; 5,75 ou 6 mm | KnitPro, Sheep and Stitch : une seule valeur, 3,25 ; 4 ; 5,5 ; 6 mm |
| US 000, 00 et 70 | 1,5 ; 1,75 ; 35 mm | absentes de KnitPro et de Sheep and Stitch |

Les tailles absentes d’une table seront acceptées, avec le `warning` de la décision 5.

## Alternatives écartées

- Craft Yarn Council seul : ni UK ni JP.
- KnitPro pour tout : UK 0 pour trois diamètres, pas de JP.
- Une valeur « en général » pour une taille US à plusieurs mm : c’est choisir à la place de la source.
- Comparer les tailles par la table : US 6 peut valoir 4,25 mm, et le Council renvoie aux mm de l’emballage.
- Conversion partout, à la valeur la plus courante : valeur inventée.
- Refuser une taille absente : les fabricants varient, et US 2,5 figure chez KnitPro sans figurer au Council.
- Liste de mm : 3,6 mm existe chez Clover et manque au Council.
- JP hors bibliothèque : une fiche de fabricant existe.
- Simple note dans `docs/plan.md` : la règle touche la bibliothèque, le moteur et le domaine.

## Conséquences

- CLA-67 charge les trois tables, avec leurs sources et le marquage « À VÉRIFIER ». Il vaut 5 points et reçoit aussi la hauteur de CLA-79, le tour de tête de CLA-80 : il est à ré-estimer ou à découper.
- `NeedleSize` ne peut pas lire `library` : le `warning` et le texte d’information vivent au-dessus de `domain`, à l’endroit que fixera CLA-67. CLA-69 en rend les textes.
- CLA-67 ouvre aussi la forme de `NeedleSize` et sa comparaison (décisions 7 et 8), dans le lot aiguilles de son découpage.
