# ADR 0028 — Rangs du bonnet et bonnet à plat

Amende l’[ADR 0007](0007-decimal-et-arrondis.md) ; complète les [ADR 0019](0019-calotte-du-bonnet.md) et [0020](0020-hauteur-finie-et-bord-replie.md).

## Contexte

L’ADR 0019 mesure la calotte en cm et en déduit le corps ; convertir ce corps en rangs ajoute un arrondi, alors que l’ADR 0007 n’en permet qu’un. Le revers se tricote deux fois. Un bonnet peut aussi se tricoter à plat, avec une couture.

## Décision

Décisions d’Isabelle du 09/11/2026.

1. **Rangs.** Tout se compte en entiers de rangs. Un arrondi par grandeur saisie : rangs tricotés au total, rangs du bord. Le corps est la différence de deux entiers, et la profondeur de calotte se déduit de ses rangs. Chaque arrondi est tracé (`RowCount`) ; l’égalité arrondit en dessous, comme le montage.
2. **Revers.** Le bord tricoté vaut 2 × la hauteur visible du revers ; les rangs tricotés au total valent hauteur finie + revers (ADR 0020, décision 7).
3. **Bonnet à plat.** Montage calculé sur le multiple du point, plus une maille de lisière à chaque bord (côtes 2/2 : 88 m donnent 90). Le tour fini se mesure sur les 88 m.
4. **Lisières.** Maille glissée en tête de chaque rang et maille de fin, comptées comme travaillées.
5. **Calotte à plat.** Calculée sur les mailles hors lisière, avec les valeurs de l’ADR 0019 ; `k2tog` à l’endroit seulement, soit un rang sur deux, et `2n − 1` rangs pour `n` rangs de diminution.
6. **Aiguilles.** Pas de passage au magic loop à plat : l’ADR 0023 ne vaut qu’en rond.
7. **Hauteur à plat.** Le corps se règle de ± 1 rang pour que le premier rang de la calotte tombe à l’endroit : au plus proche du brut, égalité vers le bas, règle tracée.

## Alternatives écartées

- Profondeur en cm, corps en cm, puis rangs : deux arrondis enchaînés.
- Lisières comptées dans la calotte : le tour fini serait faux.
- Diminuer aussi à l’envers : change le rythme de l’ADR 0019 sans raison.

## Conséquences

- La profondeur à plat reste « À VÉRIFIER » : elle se mesure à plat, le tombé reste au tricot-test.
- Un bord à multiple différent du corps attend `build_transition` (ADR 0025).
