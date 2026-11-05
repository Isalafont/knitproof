# ADR 0025 — Rang d’ajustement entre bord et corps

## Contexte

Le bord et le corps d’un bonnet n’ont pas toujours le même nombre de mailles : un bord en côtes 2×2 et un corps multiple de 6 ne tombent pas juste ensemble, et un bord calculé sur un échantillon en côtes n’a pas la jauge du corps. La pratique visée est de changer le nombre de mailles au premier rang après le bord, par des diminutions ou des augmentations réparties sur le rang. CLA-103 doit le calculer et le faire vérifier par le moteur (question tricot 4, `docs/plan.md`).

## Décision

Décisions d’Isabelle du 05/11/2026 :

1. Chaque point est monté au plus proche (CLA-65, ADR 0015), sans plus petit multiple commun avec seuil : c’est une suite possible, à rattacher à CLA-105 (tolérance sur l’écart au montage calculé) ou à un futur ticket.
2. `Transition` est un modèle à part ; `CastOnResult` ne change pas.
3. La répartition suit l’ADR 0019, décision 2.
4. Au-delà d’un rang, refus typé ; plusieurs rangs d’ajustement sont une suite possible, utile pour une manche.
5. Bornes de l’écart : rang de `k2tog` sur tout le tour, `m1` après chaque maille, acceptées par Isabelle.

Décisions du plan :

1. **Forme du refus.** `TransitionRefusal`, rendu en résultat (`Transition | TransitionRefusal`), ni exception ni `Finding`. Le dépôt rend ses refus métier en données (`CastOnCheck`, `NeedleCheck`) ; un `Finding` exige un rang et des comptes de patron.
2. **Preuve de l’arrivée.** `stated_count` égal au corps, puis `verify` sur `Pattern(cast_on=bord, rounds=(rang,))` : `count_mismatch` couvre l’arrivée, `repeat_not_fitting` le départ.
3. **Bord égal au corps.** `Transition(adjustment_round=None)`, pour que CLA-68 n’ait pas de cas particulier.
4. **Sections.** Il y a `c = |corps − bord|` changements et une section par changement, terminée par lui. Les `W` mailles tricotées telles quelles (`bord − 2c` en diminution, `bord` en augmentation) se répartissent : la section `i` reçoit `(i+1)×W//c − i×W//c` mailles, soit `W//c` plus la part de reste de l’ADR 0019.
5. **Départ du rang.** Au début du tour, sans décalage : un décalage serait une règle inventée.
6. **Bornes.** Diminution jusqu’à corps = bord − ⌊bord/2⌋, augmentation jusqu’à corps = 2·bord. Ce sont les limites physiques d’un rang de `k2tog` ou de `m1` ; une borne plus stricte serait sans source.

Les sections identiques et consécutives se regroupent en `repeat`.

## Alternatives écartées

- `CastOnResult.adjustment_round` : mêle le montage d’un seul point et le passage entre deux points.
- Exception métier : hors du style du dépôt, et CLA-69 devrait l’attraper.
- `Finding` avec un nouveau code : exige `round`, `expected` et `actual` sans sens ici.
- Chercher une période de compactage (10, 11…) : une règle de plus, à justifier.

## Conséquences

- CLA-68 compose `cast_on` (bord), `cast_on` (corps) et `build_transition`.
- Le rang est numéroté 1 dans la transition ; CLA-68 le renumérote.
- CLA-66 (RG4, CA3b) s’appuiera sur `build_transition`.
