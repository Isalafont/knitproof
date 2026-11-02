# ADR 0019 — Calotte du bonnet

## Contexte

`knitproof calc` ne peut pas produire de `crown_plan` sans règle de construction de la calotte (question tricot 5). `docs/architecture.md` prévoyait `crown_sectors` en entrée, et « secteur » n’avait pas de sens fixe : `bonnet-synthetique.yaml` comptait 8 secteurs à 1 diminution, `bonnet-secteurs-*` 4 secteurs à 2 diminutions, pour les mêmes comptes.

## Décision

Décisions d’Isabelle du 02/11/2026, modifiables, d’après sa pratique et sans source publiée. Elles valent pour `calc` : `verify` reste ouvert à toute construction.

1. **Construction.** Une seule : 8 diminutions par rang, sauf le dernier rang, soit 4 secteurs à 2 diminutions. Un secteur est la partie de la calotte qui répète le même groupe de diminutions. Une section est l’intervalle entre deux diminutions, diminution comprise : 8 sections par rang. `crown_sectors` sort de `BeanieSpecification`.
2. **Reste.** Si le compte n’est pas multiple de 8, le reste `r` se répartit entre les sections, sans changer la circonférence ni le plan. La section `i` (de 0 à 7) a une maille de plus quand `(i + 1) × r // 8 − i × r // 8` vaut 1.
3. **Rythme.** Un rang de diminution un rang sur deux, sauf les 3 derniers, à chaque rang, quelle que soit la taille. Avec `n` rangs de diminution, la calotte compte `2n − 3` rangs.
4. **Dernier rang.** Quand le compte passe sous 24 m : `k2tog` partout. Il reste 8 à 12 m, et la fin est une fermeture déclarée. `k2tog` suffit ; `ssk` attend un test qui l’exige.
5. **Compte impair au dernier rang.** La maille seule est tricotée à l’endroit. Le moteur émet un `warning` : « montage impair : une maille seule reste au dernier rang, à l’endroit ». Il ne se déclenche que si le multiple du point vaut 1 : rien n’explique alors le compte impair. Un multiple de 2 ou plus explique le compte impair, sans `warning`.
6. **Motif précis.** Propriété du point, rattachée à `body_pattern_id`. Sur un compte impair, un point marqué « motif précis » donne `needs_review`, les autres suivent la règle 5 : d’après la pratique d’Isabelle, fermée sur le fil, la maille seule ne se voit pas, sauf avec un motif précis. `needs_review` vaut quel que soit le multiple du point : la maille se voit quand même. La source d’une marque « motif précis » est une décision d’Isabelle datée, comme les seuils. La liste des points marqués revient au ticket de la bibliothèque de points. Le multiple du point existe déjà (`StitchMultiple`) : CLA-67 le rattache à `StitchPattern`.
7. **Règle transitoire.** Tant que la marque « motif précis » n’existe pas, un compte impair sur un point non marqué donne `needs_review`, avec sa question en attente : le cas ne reste ni silencieux ni bloquant, et le plan continue. Les règles 5 et 6 décrivent le comportement une fois la marque disponible.
8. **Montage trop petit.** Sous 32 m, la calotte compte moins de 3 rangs de diminution : `needs_review`, cas hors de la règle.
9. **Profondeur.** Résultat calculé : rangs de la calotte × 10 / rangs pour 10 cm, jauge après blocage, mesuré à plat du premier au dernier rang de diminution. Sans jauge en rangs : `PendingQuestion`. Le tombé reste au tricot-test.
10. **Hauteur.** Longueur du corps = hauteur finie − profondeur de calotte, à ne pas compter deux fois. Le corps est tout ce qui précède la calotte, bord compris ; le découpage du bord revient à CLA-79 et CLA-68.

| Montage | Rangs de diminution | Rangs de calotte | Dernier rang | Mailles restantes |
|---|---|---|---|---|
| 88 m | 10 | 17 | 16 → 8 m | 8 m |
| 92 m | 10 | 17 | 20 → 10 m | 10 m |
| 91 m | 10 | 17 | 19 → 10 m, maille seule | 10 m |

## Comparaison

Oslo (PetiteKnit), de 92 à 120 m : 8 diminutions un rang sur deux, les 3 dernières à chaque rang, soit 17 à 25 rangs, comptes identiques à la règle. C’est une comparaison, pas une preuve. Les bonnets de CLA-75 sont de notre cru : cas de test seulement. Aucune source publiée n’est retenue pour ces règles ni pour la profondeur de calotte.

## Alternatives écartées

- Plusieurs constructions au choix : découperait CLA-68 sans besoin en M1.
- `crown_sectors` modifiable : un ticket pourra le rouvrir ; rien ne le demande avant la démo.
- Rang d’ajustement avant la calotte : un rang de plus, alors que répartir le reste ne change ni la circonférence ni le plan.
- Nombre de secteurs selon le montage : la construction changerait d’une taille à l’autre.
- Profondeur saisie, dont le moteur déduit le rythme : suppose une cible qu’aucune source fiable ne donne.
- Profondeur demandée à la personne : elle est calculable.
- Passage à chaque rang à 48 m : seuil de CLA-75, de notre cru, sans comparaison réelle.
- Passage à chaque rang en proportion du montage : aucun patron lu ne le fait.
- Paliers (`bonnet-paliers-*`, 6, 7 ou 10 sections) : hors de la construction unique de `calc` ; ces rythmes restent des cas de `verify`.
- Construction DROPS 41-27 (diminutions de plus en plus fortes : un quart, puis un tiers, puis la moitié des mailles) : non retenue ; une seule construction pour `calc`.
- Fin à 0 maille : `Op` impose `produces ≥ 1`.

## Conséquences

- CLA-68 reçoit plus de travail : `crown_plan` complet, jauge en rangs dans `SwatchMeasurement` ; à ré-estimer à sa planification. Proposition : il livre aussi les statuts `warning` et `needs_review` de `Finding`, s’ils n’existent pas encore. La règle du reste s’y teste sur tous les restes modulo 8, en propriété du moteur. Exemple 88 m : calotte de 17 rangs, aucun constat de `verify`. Les `needs_review` imposent une question en attente, non écrite (motif précis, moins de 32 m, cas transitoire de la règle 7) : CLA-68 écrit la question et la sortie du plan.
- Le ticket de la bibliothèque de points est proposé, sans bloquer CLA-68 ; sa création attend l’accord d’Isabelle. Il porte les points marqués « motif précis » ; le multiple du point reste à CLA-67. Il n’a pas d’identifiant tant qu’il n’est pas créé.
- Un ticket pourra rouvrir `crown_sectors`.
- CLA-82 lit les comptes de la calotte pour son seuil de changement d’aiguilles.
- La question 5 de `plan.md` est tranchée.

## Questions ouvertes

- Après un rang d’ajustement (CLA-103), le montage peut être pair et le corps impair : « montage impair » serait inexact. Le texte du `warning` reste celui d’Isabelle, et la condition porte sur le compte de la calotte. Le texte ne change que si CLA-103 entre dans `calc`.
- `needs_review` impose une question en attente, non écrite (motif précis, moins de 32 m, cas transitoire de la règle 7) : CLA-68 écrit la question et la sortie du plan.
- Convertir le corps en rangs ajoute un deuxième arrondi, alors que l’ADR 0007 n’en permet qu’un. Question de conception à reprendre par CLA-68 ; CLA-79 reste à relire.
- En jersey, un montage impair donne ce `warning`, peut-être souvent. Si cela devient du bruit sur de vrais calculs, CLA-68 revoit la règle ou l’arrondi du montage, qui changerait le calcul.
