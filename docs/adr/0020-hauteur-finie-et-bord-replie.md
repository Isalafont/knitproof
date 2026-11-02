# ADR 0020 — Hauteur finie du bonnet et bord replié

Complète l’[ADR 0008](0008-provenance-et-resolution.md).

## Contexte

La question tricot 6 demande quelles sources retenir pour la hauteur d’un bonnet par âge, et comment compter un bord replié. CLA-68 en a besoin pour `rounds_for_height`. Les sources ne mesurent pas la même chose, et certaines ne disent pas ce qu’elles mesurent.

## Décision

Décision d’Isabelle du 02/11/2026.

1. **Grandeur.** La hauteur finie va du bord porté au sommet, calotte incluse, revers replié. C’est le sens de `total_height_cm` et de `finished_height_cm`.
2. **Sources.** Chaque source garde ce qu’elle mesure réellement : on ne la convertit pas sans le dire, et une mesure non définie reste une hypothèse.
3. **Résolution.** La saisie prime. Sans saisie, le moteur prend la table Knit Picks par âge, avec sa source et « À VÉRIFIER », lue comme hauteur finie par hypothèse puisque sa mesure n’est pas définie.
4. **Âge à deux valeurs.** Le moteur donne la plage et pose la question, sans calculer de milieu. C’est le cas à 6 mois, 12 mois et 3 ans.
5. **Grain d’âge.** L’âge suit la décision de CLA-80 (ADR 0018) : en mois avant 2 ans, en années ensuite ; un âge en années vaut le mois exact (3 ans = 36 mois). Les lignes sans âge chiffré (préma, « Newborn », « Pre-teens and Teens », « Adult Woman », « Adult Man ») gardent leur libellé d’origine, et 10 ans reste ambigu entre « Child » et « Pre-teens ». Si l’âge ne désigne pas une seule ligne, question en attente. La limite de 60 mois de l’ADR 0018 vaut pour la table OMS ; la hauteur prend les années entières.
6. **Statut.** Une valeur de la table prise sans saisie donne un `warning`. Un âge à deux valeurs ou sans ligne donne un `needs_review` et une `PendingQuestion`. L’écart avec le tour de tête est voulu : une hauteur sourcée se rattrape au tricot, alors qu’un tour de tête proposé donne un `needs_review` (CLA-80, ADR 0018) parce qu’il détermine le montage, et donc tout le bonnet.
7. **Bord replié.** Si `folded_brim` est vrai, la hauteur finie ne change pas et tricoté = finie + revers. `brim_height_cm` désigne la hauteur visible du revers replié. Le revers est saisi, sinon question en attente, sans coefficient inventé.
8. **Bord non replié.** `brim_height_cm` reste la hauteur du bord, déjà comprise dans la hauteur finie.
9. **Lien avec la calotte.** L’ADR 0019 (CLA-78) pose corps = hauteur finie − profondeur de calotte, bord compris. Avec un revers, cette formule donne la longueur portée ; la longueur tricotée avant la calotte est hauteur finie − profondeur + revers. Cette seconde formule découle de la règle du revers d’Isabelle (décision 7, tricoté = finie + revers), validée par elle ; ce n’est pas une décision directe.
10. **Exemple 3 ans.** `examples/bonnet-3-ans.yaml` portera une hauteur saisie, signalée comme telle. Sa valeur reste une question ouverte pour CLA-68 : elle n’est pas choisie ici.

### Table retenue

Relue le 02/11/2026.

Source : [Knit Picks, « Hat Size Charts », 17/12/2009](https://tutorials.knitpicks.com/hat-size-charts/). Hauteurs telles que publiées, en pouces ; conversion exacte, 1 in = 2,54 cm. La page présente ses tableaux comme « a rough idea for project planning purposes », et ne définit pas la mesure. Toutes ces valeurs sont des hypothèses.

| Ligne | Hauteur | En cm |
|---|---|---|
| Preemie (1-2 lbs) | 3,5 in | 8,89 |
| Preemie (3-4 lbs) | 4 in | 10,16 |
| Preemie (4-5 lbs) | 4,5 in | 11,43 |
| Preemie (5.5-6 lbs) | 5 in | 12,7 |
| Newborn | 6 in | 15,24 |
| Baby – 3 to 6 months | 7 in | 17,78 |
| Baby 6 to 12 months | 7,5 in | 19,05 |
| Toddler – preschooler (12 months – 3 years) | 8 in | 20,32 |
| Child (3 – 10 years) | 8,5 in | 21,59 |
| Pre-teens and Teens | 10 in | 25,4 |
| Adult Woman | 11 in | 27,94 |
| Adult Man | 11,5 in | 29,21 |

La [page Knit Picks que citait le README](https://www.knitpicks.com/learning-center/hat-size-chart) n’a pas pu être lue (403) : rien ne dit qu’elle porte les mêmes valeurs, et cette table ne vient pas d’elle.

### Hors de cette règle

- **Bord doublé (type Oslo).** Il ne suit pas la formule du revers. Sa déduction reste à confirmer, il se traitera à part quand un cas le demandera.
- **Mélèze.** Mesures introuvables : rien n’en est déduit.
- **Patrons publiés.** Ils ne servent pas de table et ne sont pas convertis : `docs/architecture.md` §10 pour les droits, et leur hauteur ne se compare pas à une hauteur totale.

## Alternatives écartées

- Hauteur avant diminutions : ne se compare pas à une hauteur totale.
- Hauteur tricotée totale : change avec le revers.
- Plage de plusieurs sources, hauteur toujours demandée : oblige à répondre même quand une valeur sourcée existe.
- Pas de table, question systématique : CLA-67 n’aurait rien à charger pour la hauteur.
- Milieu entre deux valeurs d’un même âge : une valeur que personne n’a publiée.
- Hauteur saisie revers compris, sans calcul : le fini n’est plus garanti.
- Valeurs distinctes avec et sans revers : aucune source lue ne les donne.
- Craft Yarn Council : [sa page](https://craftyarncouncil.com/node/39) donne le tour de tête, aucune hauteur.
- Nouveau ticket pour la table : `ReferenceMeasurement` est déjà dans CLA-67.
- Simple note dans `docs/plan.md` : trop léger, la règle touche la résolution et les modèles.

## Conséquences

- `docs/architecture.md` §6 et §7 portent le sens des champs et la résolution.
- CLA-67 charge la table, avec sa source. Proposition soumise à l’accord d’Isabelle, en commentaire.
- CLA-68 applique la résolution, la règle du revers et la formule du corps, et ajoute la hauteur saisie à l’exemple 3 ans. Proposition soumise à l’accord d’Isabelle, en commentaire.
- Aucun nouveau ticket : CLA-67 et CLA-68 portent la suite.
- Renvoyé à CLA-68 : A. part du bord dans le tricoté avec repli (`brim_rounds` et `body_rounds`) ; B. hauteur finie « portée » et profondeur « à plat », la soustraction mêle deux états, le tombé reste au tricot-test ; C. deuxième arrondi pour le corps, et corps nul ou négatif sur les petites tailles. Valeur de l’exemple 3 ans : décision 10.
