# ADR 0024 — Aisance du bonnet

Amendé par l’[ADR 0031](0031-aisance-d-apres-les-patrons-et-la-laine.md) (points 3 et 5).

## Contexte

L’aisance est l’écart entre le tour du bonnet fini et le tour de tête. Elle est négative quand le bonnet est plus petit que la tête : c’est ce qui le fait tenir. Le moteur s’en sert pour passer du tour de tête au tour visé, puis au montage (ADR 0015).

Le 26/10/2026, Isabelle a tranché en partie la question tricot 1 de `docs/plan.md` : l’aisance dépend du point, de la fibre, des aiguilles et de l’ajustement voulu (ajusté ou ample), et la fibre n’est pas une simple modulation. Restaient ouverts l’unité, la règle de combinaison et les sources. La bibliothèque de CLA-67 ne peut porter aucune valeur d’aisance sans elles.

L’ADR 0010 dit encore qu’un mélange de fibres « module » l’aisance, et `docs/architecture.md` prévoit un champ `ease_modifier` dans `FiberProfile`. Les deux contredisent la décision du 26/10.

## Décision

Décidé par Isabelle le 05/11/2026 (CLA-77, question tricot 1).

1. **Où se mesure l’aisance.** Au bord, sur le tour qui tient le bonnet sur la tête. Le point retenu est celui du bord.
2. **Unité.** Une valeur de référence est en %. Une saisie de la personne est en % ou en cm, et garde son unité d’origine (architecture §8). Le modèle `Ease` prévu (architecture §6) porte déjà les deux unités.
3. **Règle de combinaison.** Le chiffre vient d’une table en % par couple (ajustement, point). La fibre et les aiguilles ne changent pas ce chiffre : elles donnent des avertissements qualitatifs sourcés. Sans source, pas d’avertissement.
4. **Couple sourcé.** Le moteur propose la valeur de la table, marquée « À VÉRIFIER » avec sa source. Elle n’est retenue qu’après une `Decision` de la personne, comme le tour de tête de l’ADR 0018.
5. **Couple sans source, ou point inconnu.** Aucune valeur n’est proposée. L’aisance est demandée par une question en attente, qui affiche les repères sourcés de la table.
6. **Saisie.** Une aisance saisie prime toujours sur la table.
7. **Calcul des valeurs.** La bibliothèque stocke les données brutes de chaque source : montage, échantillon et plage de tête par taille. Le moteur en déduit le %, en `Decimal`. Une taille donne l’aisance au milieu de sa plage de tête. Pour plusieurs tailles, la valeur proposée est la médiane des tailles, et la plage va de la plus faible à la plus forte. Les pourcentages arrondis ci-dessous ne servent qu’à la lecture.
8. **Suite prévue.** L’étirement mesuré sur l’échantillon de la personne primera sur la table (ticket de suite). L’élasticité des côtes dépend de la laine : seul un échantillon par laine la mesure (Isabelle, 05/11/2026).

## Valeurs retenues

| Ajustement | Point du bord | Valeur proposée | Plage de la source | Source |
|---|---|---|---|---|
| ajusté | jersey | −15,6 % | −15,2 à −16,0 % (7 tailles) | Oslo |
| ample | côtes 2/2 | −17,7 % | −10,0 à −24,2 % (une taille de bord) | Rosebud, source unique |
| ajusté | côtes 2/2 | aucune | — | aucune source : aisance demandée, Rosebud affiché en repère |

**Oslo.** Mette Wendelboe Okkels, « Bonnet Oslo », PetiteKnit, version 3.0 (2025), patron en français, p. 1–2. PDF privé d’Isabelle, relu le 05/11/2026.
- Tours de tête : 47–48 (49–50) 51–52 (53–54) 55–56 (57–59) 60–63 cm.
- Échantillon : 23 m = 10 cm en jersey, aiguilles 3 mm. Bonnet tricoté en jersey, bord replié en jersey.
- Montage : 92 (96) 100 (104) 108 (112) 120 m.
- Tour du bonnet = montage / 2,3 cm. Aisance au milieu de chaque plage : −15,8 / −15,7 / −15,6 / −15,5 / −15,4 / −16,0 / −15,2 %. Médiane −15,6 %. L’aisance est stable en % du bébé à l’adulte, ce qui justifie le %.
- Fils suggérés : Sunday (Sandnes Garn), Arwetta (Filcolana), avec ou sans mohair. Le patron ne donne pas la composition des fils.
- Le patron ne dit pas « ajusté » : c’est l’ADR qui le classe ainsi, d’après l’aisance de −15,6 %.

**Rosebud.** Jared Flood, « Rosebud », Brooklyn Tweed, 2011, p. 2–3. PDF privé d’Isabelle, relu le 05/11/2026.
- Taille : « Average Adult Small Hat/Tam (Longer Slouchy Hat) », « To fit head sizes 20-23¾" ».
- Dimensions finies : « 18" circumference at brim, 22½" circumference at widest point; blocked and unstretched ». Le patron ne donne qu’un chiffre de bord et monte 84 m pour les deux versions : l’ADR en déduit que le bord mesure 18" dans les deux tailles. Ces dimensions sont prises au repos (« blocked and unstretched »), alors que le bord en côtes s’étire sur la tête.
- Bord : 84 m en côtes 2/2, sur une aiguille « two sizes smaller than Gauge Needle ». Corps au point mousse, 4½ m = 1" ; fil Shelter, 100 % laine Targhee-Columbia.
- Aisance du bord : −10,0 % pour une tête de 20", −24,2 % pour 23¾", −17,7 % au milieu (21⅞"). Corps au plus large : +2,9 % au milieu. Le patron se dit « Small Hat/Tam (Longer Slouchy Hat) » : le classement « ample » est un choix de l’ADR, confirmé par Isabelle. `docs/plan.md` décrivait déjà le Mélèze comme bonnet ample, et Isabelle le rapproche du Rosebud.
- Seule source publiée relue en côtes 2/2 : la valeur reste « À VÉRIFIER » et la plage s’affiche avec elle.

## Repères affichés, non chargés

- Woolly Wormhead, « A Guide to Hat Sizing », <https://www.woollywormhead.com/sizing>, lu le 05/11/2026 : l’écart entre le bonnet fini et la tête est « usually 2 to 3 inches », « 5 to 7.5 centimetres, or roughly 12% ». La page parle de tailles (tour de tête, tailles par âge, réglage selon l’échantillon), mais ne précise ni l’ajustement, ni la fibre. Elle ajoute que le goût personnel compte, et que certaines personnes préfèrent peu ou pas d’aisance négative.
- Mélèze, design d’Isabelle : 120 m en côtes 2/2, bord replié, aiguilles 3 à 3,5 mm. Pas de tour de tête, et un échantillon donné en jersey seulement. D’après Isabelle, son aisance « se rapproche » de celle du Rosebud. C’est un avis d’Isabelle, que le PDF ne permet pas de vérifier, et non une valeur chiffrée : il n’entre pas dans la table.

## Ce que change cet ADR pour l’ADR 0010

Un ADR accepté ne se réécrit pas : on en écrit un nouveau qui en remplace une partie, et l’ancien le signale. Ici :

- La phrase de l’ADR 0010 « Le comportement d’un mélange (détente au blocage, modulation de l’aisance) est la moyenne des profils de ses fibres » perd la partie « modulation de l’aisance ». La pondération des mélanges reste valable pour la détente au blocage.
- L’ADR 0010 reçoit en tête la mention « Remplacé en partie par l’ADR 0024 (aisance) ». Le reste de son texte ne change pas.
- `docs/architecture.md` retire `ease_modifier` de `FiberProfile`. La fibre ne porte plus de chiffre d’aisance, seulement des avertissements sourcés.

## Alternatives écartées

- **Aisance en cm par taille** : l’Oslo montre une aisance stable en %, alors que des cm fixes la feraient varier d’une taille à l’autre.
- **Coefficients chiffrés multipliés (point × fibre × aiguilles)** : aucune source chiffrée par fibre ni par aiguille n’a été trouvée. Ce serait inventer des nombres.
- **La fibre qui module l’aisance (ADR 0010, `ease_modifier`)** : contredit la décision du 26/10/2026.
- **Valeur appliquée d’office, sans `Decision`** : c’est une estimation sans arbitrage (architecture §7).
- **Toujours demander l’aisance, même pour un couple sourcé** : laisse sans aide la personne qui ne connaît pas l’aisance d’un bonnet.
- **Chiffre d’Isabelle en côtes 2/2** : elle n’en a pas. Selon elle, l’élasticité des côtes dépend de la laine.
- **Rosebud pour un bonnet ajusté en côtes 2/2** : l’ADR classe le Rosebud comme bonnet ample (confirmé par Isabelle). Son bord n’est qu’un repère pour l’ajusté.
- **Woolly Wormhead comme valeur de table** : la page ne précise ni l’ajustement, ni la fibre.
- **Mélèze comme source chiffrée** : il ne donne ni tour de tête, ni échantillon en côtes.

## Conséquences

- La question tricot 1 de `docs/plan.md` est tranchée.
- `docs/architecture.md` : `ease_modifier` est retiré (l. 182). L’ordre de confiance de l’aisance (l. 234) devient « saisie > table de référence par couple (ajustement, point), proposée puis décidée (`needs_review`) », et une question en attente sinon. `Ease` est précisé (l. 201) : % ou cm, unité d’origine.
- L’ADR 0010 porte la mention « Remplacé en partie par l’ADR 0024 ».
- README : « à confirmer » est retiré des lignes 32 et 47. L’exemple −10 % reste une valeur saisie, avec sa ligne de `examples/bonnet-3-ans.yaml`. Les lignes 114–116 sont à aligner : la fibre donne des avertissements, pas une part chiffrée de l’aisance.
- Une valeur issue de la table cite sa source et la taille. La valeur retenue après la `Decision` porte `person_decision`.
- Les patrons Oslo, Rosebud et Mélèze ne sont pas versionnés. La bibliothèque ne garde que les mesures citées ici et leurs références.

## Suites

| Ticket | Contenu |
|---|---|
| CLA-67 | Charger la table d’aisance (deux lignes sourcées, données brutes par taille), le repère Woolly Wormhead et les avertissements fibre et aiguilles sourcés |
| CLA-115 | Mesurer l’étirement d’un échantillon (au repos, étiré, relâché), par laine et par point, qui prime sur la table |
| CLA-66 | Question en attente sur l’aisance : valeur « À VÉRIFIER » et `Decision`, ou demande avec repères |
| CLA-102 | Utilise cette table pour juger la taille annoncée d’un patron |
| CLA-116 | Réunir plusieurs patrons publiés par couple (ajustement, point), d’abord (ajusté, côtes 2/2) et (ample, côtes 2/2), pour qu’aucune valeur de la table ne repose sur une source unique, plus les sources qualitatives sur la fibre et les aiguilles |
